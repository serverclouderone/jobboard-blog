#!/usr/bin/env python3
"""
Initialise l'arborescence complète du projet jobboard-blog (Phase A1).
Conforme à .cursorrules — JOBBOARD BLOG MAROC.
"""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

DIRS = [
    ".github/workflows",
    "scripts/scrapers",
    "scripts/agents",
    "scripts/images",
    "scripts/publisher",
    "scripts/utils",
    "content/offres",
    "content/public",
    "content/etranger",
    "content/stage",
    "content/conseils",
    "content/concours",
    "content/pages",
    "static/images",
    "static/icons",
    "layouts/_default",
    "layouts/partials",
    "layouts/shortcodes",
    "assets/css",
    "assets/js",
    "data",
    "logs",
]

FILES = [
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "README.md",
    ".github/workflows/pipeline_offres.yml",
    ".github/workflows/pipeline_public.yml",
    ".github/workflows/pipeline_etranger.yml",
    ".github/workflows/pipeline_editorial.yml",
    ".github/workflows/maintenance.yml",
    "scripts/main_pipeline.py",
    "scripts/scrapers/__init__.py",
    "scripts/scrapers/base_scraper.py",
    "scripts/scrapers/raw_scraper.py",
    "scripts/scrapers/scraper_bghit.py",
    "scripts/scrapers/scraper_rekrute.py",
    "scripts/scrapers/scraper_emploima.py",
    "scripts/scrapers/scraper_indeed.py",
    "scripts/scrapers/scraper_anapec.py",
    "scripts/scrapers/scraper_alwadifa.py",
    "scripts/scrapers/scraper_marocannonces.py",
    "scripts/scrapers/scraper_optioncarriere.py",
    "scripts/scrapers/scraper_linkedin.py",
    "scripts/scrapers/scraper_manager.py",
    "scripts/agents/__init__.py",
    "scripts/agents/agent_writer.py",
    "scripts/images/__init__.py",
    "scripts/images/image_generator.py",
    "scripts/images/image_downloader.py",
    "scripts/publisher/__init__.py",
    "scripts/publisher/hugo_publisher.py",
    "scripts/publisher/cross_poster.py",
    "scripts/utils/__init__.py",
    "scripts/utils/logger.py",
    "scripts/utils/deduplication.py",
    "scripts/utils/seo_scorer.py",
    "scripts/utils/published_slugs.txt",
    "content/pages/a-propos.md",
    "content/pages/contact.md",
    "content/pages/politique-de-confidentialite.md",
    "content/pages/conditions-utilisation.md",
    "content/pages/mentions-legales.md",
    "content/pages/publier-offre.md",
    "content/pages/newsletter.md",
    "layouts/_default/baseof.html",
    "layouts/_default/single.html",
    "layouts/_default/list.html",
    "layouts/partials/head.html",
    "layouts/partials/header.html",
    "layouts/partials/footer.html",
    "layouts/partials/adsense.html",
    "layouts/partials/seo-schema.html",
    "layouts/partials/share-buttons.html",
    "layouts/partials/newsletter-inline.html",
    "layouts/shortcodes/apply-button.html",
    "layouts/shortcodes/info-box.html",
    "assets/css/main.css",
    "assets/js/main.js",
    "data/editorial_topics.json",
    "data/alwadifa_sources.json",
]

# Fichiers à ne pas écraser s'ils ont du contenu (config créés séparément)
SKIP_IF_EXISTS = {"config.toml", "scripts/config.py"}


def main():
    os.chdir(ROOT)
    for d in DIRS:
        path = os.path.join(ROOT, d)
        os.makedirs(path, exist_ok=True)
        print(f"  {d}/")
    for f in FILES:
        path = os.path.join(ROOT, f)
        if f in SKIP_IF_EXISTS and os.path.exists(path) and os.path.getsize(path) > 0:
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", encoding="utf-8") as _:
                pass
            print(f"  {f}")
    print("\nArborescence créée. Affichage (fichiers, triés, max 100):")
    all_paths = []
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        if ".git" in dirpath or "__pycache__" in dirpath or "node_modules" in dirpath:
            continue
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT)
            all_paths.append(rel.replace("\\", "/"))
    for p in sorted(all_paths)[:100]:
        print(f"  {p}")
    if len(all_paths) > 100:
        print(f"  ... et {len(all_paths) - 100} autres fichiers")


if __name__ == "__main__":
    main()
