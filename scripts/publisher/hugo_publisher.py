"""
Génère le fichier .md Hugo avec front matter complet + Schema JSON-LD.
Vérifie la checklist avant écriture. Conforme .cursorrules.
"""
import json
import os
from datetime import datetime, timedelta

import yaml

from scripts.config import (
    ARTICLE_MIN_WORDS,
    CONTENT_DIRS,
    PUBLISHED_SLUGS_FILE,
)
from scripts.utils.deduplication import add_published_slug, is_published
from scripts.utils.logger import log


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _normalize_slug(slug):
    """Nettoie le slug : minuscules, tirets, sans accents."""
    import unicodedata
    s = (slug or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = "".join(c if c.isalnum() or c == "-" else "-" for c in s)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-") or "offre-emploi-2026"


def _build_schema_jsonld(job_info, meta, apply_url, date_str):
    """Construit le Schema JSON-LD JobPosting + FAQPage + BreadcrumbList."""
    schemas = []
    job_posting = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": meta.get("title_seo", ""),
        "description": meta.get("meta_description", ""),
        "datePosted": date_str,
        "validThrough": ((datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.utcnow()).replace(tzinfo=None) + timedelta(days=30)).strftime("%Y-%m-%d"),
        "employmentType": (job_info.get("type_contrat") or "FULL_TIME").upper().replace("CDI", "FULL_TIME").replace("CDD", "PART_TIME").replace("STAGE", "INTERN"),
        "hiringOrganization": {"@type": "Organization", "name": job_info.get("entreprise", "")},
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": job_info.get("ville", ""),
                "addressRegion": job_info.get("region", ""),
                "addressCountry": "MA",
            },
        },
        "directApply": True,
        "url": apply_url,
    }
    schemas.append(job_posting)
    if meta.get("faq_schema"):
        faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q.get("question", ""),
                    "acceptedAnswer": {"@type": "Answer", "text": q.get("answer", "")},
                }
                for q in meta.get("faq_schema", [])
            ],
        }
        schemas.append(faq)
    return json.dumps(schemas, ensure_ascii=False, indent=2)


def _validate_checklist(meta, job_info, article, apply_url, image_path, slug):
    """Vérifie la checklist obligatoire avant publication."""
    errors = []
    title = meta.get("title_seo", "")
    if not title or not (55 <= len(title) <= 60):
        errors.append(f"title_seo doit être entre 55-60 caractères (actuel: {len(title)})")
    desc = meta.get("meta_description", "")
    if not desc or not (150 <= len(desc) <= 160):
        errors.append(f"meta_description doit être entre 150-160 caractères (actuel: {len(desc)})")
    if is_published(slug):
        errors.append(f"slug '{slug}' déjà publié")
    if not apply_url or not apply_url.startswith("https://"):
        errors.append("apply_url invalide ou absent")
    if image_path:
        img_full = os.path.join(_project_root(), image_path.lstrip("/"))
        if not os.path.exists(img_full):
            errors.append(f"image absente: {image_path}")
    else:
        errors.append("image_path manquant")
    word_count = len(article.split())
    if word_count < ARTICLE_MIN_WORDS:
        errors.append(f"article trop court: {word_count} mots (minimum: {ARTICLE_MIN_WORDS})")
    if not job_info.get("secteur") or not job_info.get("ville"):
        errors.append("taxonomies manquantes (secteur, ville)")
    return errors


def publish(article_data):
    """
    Génère le fichier .md Hugo avec front matter complet.
    article_data doit contenir: meta, job_info, article, apply_url, source_url, image_path, word_count.
    Retourne le chemin du fichier créé ou None en cas d'erreur.
    """
    if not article_data:
        log("hugo_publisher: article_data vide", "ERROR")
        return None
    meta = article_data.get("meta", {})
    job_info = article_data.get("job_info", {})
    article = article_data.get("article", "")
    apply_url = article_data.get("apply_url", "")
    source_url = article_data.get("source_url", "")
    image_path = article_data.get("image_path", "")
    slug = _normalize_slug(meta.get("slug") or job_info.get("slug") or "offre-emploi-2026")
    type_article = (job_info.get("type_article") or "prive").strip().lower()
    content_dir = CONTENT_DIRS.get(type_article, CONTENT_DIRS["prive"])
    now = datetime.utcnow()
    date_str = now.isoformat() + "+00:00"
    errors = _validate_checklist(meta, job_info, article, apply_url, image_path, slug)
    if errors:
        log(f"hugo_publisher: validation échouée pour {slug}: {', '.join(errors)}", "ERROR")
        return None
    root = _project_root()
    file_path = os.path.join(root, content_dir, f"{slug}.md")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    front_matter = {
        "title": meta.get("title_seo", ""),
        "date": date_str,
        "lastmod": date_str,
        "draft": False,
        "slug": slug,
        "description": meta.get("meta_description", ""),
        "keywords": (meta.get("secondary_keywords", []) + [meta.get("focus_keyword", "")])[:10],
        "categories": [type_article],
        "secteurs": [job_info.get("secteur", "")],
        "fonctions": [job_info.get("fonction", "")],
        "villes": [job_info.get("region", "")],
        "types": [(job_info.get("type_contrat") or "CDI").lower()],
        "pays": [job_info.get("pays", "maroc")],
        "image": image_path,
        "apply_url": apply_url,
        "source_url": source_url,
        "company": job_info.get("entreprise", ""),
        "location": job_info.get("ville", ""),
        "region": job_info.get("region", ""),
        "contract_type": job_info.get("type_contrat", "CDI"),
        "salary": job_info.get("salaire", ""),
        "sector": job_info.get("secteur", ""),
        "remote": job_info.get("remote", False),
        "urgent": job_info.get("urgent", False),
        "schema_type": "JobPosting",
        "reading_time": f"{article_data.get('word_count', 0) // 200} min",
        "og_title": meta.get("og_title", meta.get("title_seo", "")),
        "og_description": meta.get("og_description", meta.get("meta_description", "")),
        "faq_questions": meta.get("faq_schema", []),
    }
    schema_jsonld = _build_schema_jsonld(job_info, meta, apply_url, date_str)
    yaml_str = yaml.dump(front_matter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    content = f"---\n{yaml_str}---\n\n{article}\n\n<script type=\"application/ld+json\">\n{schema_jsonld}\n</script>\n"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        add_published_slug(slug)
        log(f"hugo_publisher: publié {file_path}", "INFO")
        return file_path
    except Exception as e:
        log(f"hugo_publisher: erreur écriture {file_path}: {e}", "ERROR")
        return None
