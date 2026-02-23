#!/usr/bin/env python3
"""
Orchestrateur principal du pipeline BeJob.
Enchaîne : scraping → génération IA → images → publication Hugo → cross-posting Telegram.
Conforme .cursorrules — JOBBOARD BLOG MAROC.
"""
import argparse
import os
import sys

from scripts.agents.agent_writer import ArticleWriterAgent
from scripts.config import (
    ERRORS_LOG_FILE,
    LOG_FILE,
    REJECTED_LOG_FILE,
)
from scripts.images.image_generator import get_article_image
from scripts.publisher.cross_poster import CrossPoster
from scripts.publisher.hugo_publisher import publish
from scripts.scrapers.scraper_manager import fetch_all
from scripts.utils.logger import log, set_log_files


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_pipeline(mode="prive", keywords=None):
    """
    Exécute le pipeline complet pour un mode donné.
    mode: "prive" | "public" | "etranger" | "stage" | "editorial"
    """
    os.chdir(_project_root())
    log_dir = os.path.join(_project_root(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    set_log_files(
        log_path=os.path.join(log_dir, "pipeline.log"),
        errors_path=os.path.join(log_dir, "errors.log"),
    )
    log(f"[PIPELINE] Démarrage mode={mode}")
    agent = ArticleWriterAgent()
    cross_poster = CrossPoster()
    scraped_jobs = fetch_all(mode=mode, keywords=keywords)
    if not scraped_jobs:
        log("[PIPELINE] Aucune offre scrapée", "WARNING")
        return 0
    log(f"[PIPELINE] {len(scraped_jobs)} offres scrapées, traitement...")
    published_count = 0
    rejected_count = 0
    for i, scraped in enumerate(scraped_jobs, 1):
        log(f"[PIPELINE] Traitement {i}/{len(scraped_jobs)}: {scraped.get('title', '')[:60]}")
        try:
            article_data = agent.generate(scraped)
            if not article_data:
                log(f"[PIPELINE] Agent a échoué pour: {scraped.get('title', '')}", "WARNING")
                rejected_count += 1
                continue
            job_info = article_data.get("job_info", {})
            slug = (article_data.get("meta", {}).get("slug") or "").strip()
            image_path = get_article_image(scraped, job_info, slug)
            article_data["image_path"] = image_path
            file_path = publish(article_data)
            if not file_path:
                log(f"[PIPELINE] Publication échouée pour: {scraped.get('title', '')}", "WARNING")
                rejected_count += 1
                continue
            published_count += 1
            base_url = os.environ.get("SITE_BASE_URL", "https://bejob.ma").rstrip("/")
            rel_path = file_path.replace(os.sep, "/").replace("content/", "").replace(".md", "")
            article_url = f"{base_url}/{rel_path}/"
            cross_poster.post_telegram(article_data, article_url)
            log(f"[PIPELINE] ✓ Publié: {file_path}")
        except Exception as e:
            log(f"[PIPELINE] Erreur traitement {scraped.get('title', '')}: {e}", "ERROR")
            rejected_count += 1
    log(f"[PIPELINE] Terminé: {published_count} publiés, {rejected_count} rejetés")
    return published_count


def main():
    parser = argparse.ArgumentParser(description="Pipeline BeJob — Génération automatique d'articles")
    parser.add_argument("--mode", choices=["prive", "public", "etranger", "stage", "editorial"], default="prive", help="Mode de scraping")
    parser.add_argument("--keywords", nargs="+", help="Mots-clés pour le scraping")
    args = parser.parse_args()
    try:
        count = run_pipeline(mode=args.mode, keywords=args.keywords)
        sys.exit(0 if count > 0 else 1)
    except KeyboardInterrupt:
        log("[PIPELINE] Interrompu par l'utilisateur", "WARNING")
        sys.exit(130)
    except Exception as e:
        log(f"[PIPELINE] Erreur fatale: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
