"""
Orchestrateur global des scrapers. Déduplication, filtres, tri, limite.
Conforme .cursorrules : max 3 simultanés (ThreadPoolExecutor), post-traitement strict.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from scripts.config import (
    BGHIT_CATEGORIES,
    MAX_ARTICLE_AGE_HOURS,
    MAX_ARTICLES_PER_RUN,
    REKRUTE_KEYWORDS,
)
from scripts.scrapers.scraper_alwadifa import AlwadifaScraper
from scripts.scrapers.scraper_bghit import BghitScraper
from scripts.scrapers.scraper_emploima import EmploiMAScraper
from scripts.scrapers.scraper_indeed import IndeedScraper
from scripts.scrapers.scraper_linkedin import LinkedInScraper
from scripts.scrapers.scraper_marocannonces import MarocAnnoncesScraper
from scripts.scrapers.scraper_optioncarriere import OptionCarriereScraper
from scripts.scrapers.scraper_rekrute import RekruteScraper
from scripts.utils.logger import log

# Catégories bghit par type (sous-ensembles de BGHIT_CATEGORIES)
BGHIT_PUBLIC_URLS = [
    u for u in BGHIT_CATEGORIES
    if "emploi-public" in u or "alwadifa" in u
]
BGHIT_ETRANGER_URLS = [
    u for u in BGHIT_CATEGORIES
    if "etranger" in u and ("france" in u or "canada" in u)
]
BGHIT_STAGE_URL = [u for u in BGHIT_CATEGORIES if "stage" in u]

SCRAPERS_PRIVE = {
    "bghit": BghitScraper(),
    "rekrute": RekruteScraper(),
    "emploima": EmploiMAScraper(),
    "indeed": IndeedScraper(),
    "optioncarriere": OptionCarriereScraper(),
    "marocannonces": MarocAnnoncesScraper(),
    "linkedin": LinkedInScraper(),
}

SCRAPERS_PUBLIC = {
    "alwadifa": AlwadifaScraper(),
    "bghit_public": BghitScraper(),
}


def _run_scraper(name, scraper, **kwargs):
    """Exécute un scraper et retourne (name, results)."""
    try:
        results = scraper.fetch(**kwargs)
        return (name, results or [])
    except Exception as e:
        log(f"[MANAGER] {name} error: {e}", "ERROR")
        return (name, [])


def _merge_all(results_per_source):
    """Fusionne toutes les listes en une seule."""
    out = []
    for _name, jobs in results_per_source:
        out.extend(jobs)
    return out


def _deduplicate(jobs):
    """Déduplication par (titre normalisé, apply_url)."""
    seen = set()
    out = []
    for j in jobs:
        title = (j.get("title") or "").strip().lower()[:80]
        url = (j.get("apply_url") or "").strip()
        key = (title, url)
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def _parse_date(s):
    """Retourne un datetime ou None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _filter_recent(jobs):
    """Garde les offres de moins de MAX_ARTICLE_AGE_HOURS (ou sans date)."""
    if not MAX_ARTICLE_AGE_HOURS:
        return jobs
    cutoff = datetime.utcnow() - timedelta(hours=MAX_ARTICLE_AGE_HOURS)
    out = []
    for j in jobs:
        d = _parse_date(j.get("date"))
        if d is None:
            out.append(j)
            continue
        if d.replace(tzinfo=None) >= cutoff:
            out.append(j)
    return out


def _filter_already_published(jobs):
    """Exclut les offres dont l'URL source est déjà connue (optionnel). Unicité slug vérifiée à la publication."""
    # Les slugs sont générés par l'agent ; on ne peut pas filtrer ici par slug.
    # On pourrait maintenir un fichier published_urls.txt en parallèle si besoin.
    return jobs


def _sort_by_relevance(jobs):
    """Maroc > présence image > description longue."""
    def score(j):
        s = 0
        if j.get("og_image_url"):
            s += 100
        raw = (j.get("raw_text") or "")
        s += min(50, len(raw) // 100)
        title = (j.get("title") or "").lower()
        if "maroc" in title or "casablanca" in title or "rabat" in title:
            s += 20
        return s
    return sorted(jobs, key=score, reverse=True)


def _validate_required(jobs):
    """Garde uniquement title + apply_url valides."""
    out = []
    for j in jobs:
        title = (j.get("title") or "").strip()
        apply_url = (j.get("apply_url") or "").strip()
        if not title or len(title) < 5:
            continue
        if not apply_url or not apply_url.startswith("http"):
            continue
        out.append(j)
    return out


def fetch_all(mode="prive", keywords=None):
    """
    Lance les scrapers selon le mode, puis enchaîne le post-traitement.
    mode: "prive" | "public" | "etranger" | "stage"
    """
    results_per_source = []
    max_workers = 3

    if mode == "prive":
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_run_scraper, name, scraper, keywords=keywords, pages=2): name
                for name, scraper in SCRAPERS_PRIVE.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    n, results = future.result()
                    results_per_source.append((n, results))
                    log(f"[MANAGER] {n}: {len(results)} offres")
                except Exception as e:
                    log(f"[MANAGER] {name} failed: {e}", "ERROR")

    elif mode == "public":
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(_run_scraper, "alwadifa", SCRAPERS_PUBLIC["alwadifa"], keywords=keywords, pages=3),
                executor.submit(_run_bghit_categories, BGHIT_PUBLIC_URLS, 2),
            ]
            for future in as_completed(futures):
                try:
                    name, results = future.result()
                    results_per_source.append((name, results))
                    log(f"[MANAGER] {name}: {len(results)} offres")
                except Exception as e:
                    log(f"[MANAGER] public scraper failed: {e}", "ERROR")

    elif mode == "etranger":
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(_run_bghit_categories, BGHIT_ETRANGER_URLS, 2),
                executor.submit(_run_scraper, "linkedin", SCRAPERS_PRIVE["linkedin"], keywords=keywords or ["Maroc"], pages=2),
            ]
            for future in as_completed(futures):
                try:
                    name, results = future.result()
                    results_per_source.append((name, results))
                    log(f"[MANAGER] {name}: {len(results)} offres")
                except Exception as e:
                    log(f"[MANAGER] etranger scraper failed: {e}", "ERROR")

    elif mode == "stage":
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(_run_bghit_categories, BGHIT_STAGE_URL, 2),
                executor.submit(_run_scraper, "rekrute", RekruteScraper(), keywords=["stage", "pfe"], pages=2),
            ]
            for future in as_completed(futures):
                try:
                    name, results = future.result()
                    results_per_source.append((name, results))
                    log(f"[MANAGER] {name}: {len(results)} offres")
                except Exception as e:
                    log(f"[MANAGER] stage scraper failed: {e}", "ERROR")

    elif mode == "editorial":
        # Mode editorial : pas de scraping, génération d'articles conseils (à implémenter)
        log("[MANAGER] Mode editorial : pas de scraping pour l'instant", "INFO")
        return []

    else:
        log(f"[MANAGER] Unknown mode: {mode}", "WARNING")
        return []

    jobs = _merge_all(results_per_source)
    if mode == "public":
        jobs = [j for j in jobs if (j.get("type") or "") == "public"]
    elif mode == "etranger":
        jobs = [j for j in jobs if (j.get("type") or "") == "etranger" or j.get("source_name") == "linkedin.com"]
    elif mode == "stage":
        jobs = [j for j in jobs if (j.get("type") or "") == "stage"]
    elif mode == "prive":
        jobs = [j for j in jobs if (j.get("type") or "") == "prive"]

    jobs = _deduplicate(jobs)
    jobs = _filter_recent(jobs)
    jobs = _filter_already_published(jobs)
    jobs = _sort_by_relevance(jobs)
    jobs = _validate_required(jobs)
    jobs = jobs[:MAX_ARTICLES_PER_RUN]
    log(f"[MANAGER] Total final: {len(jobs)} offres après filtres")
    return jobs


def _run_bghit_categories(category_urls, max_pages):
    """Exécute BghitScraper sur une liste de catégories. Retourne (name, list)."""
    scraper = BghitScraper()
    all_jobs = []
    for url in category_urls:
        all_jobs.extend(scraper.fetch_category(url, max_pages=max_pages))
    return ("bghit", all_jobs)
