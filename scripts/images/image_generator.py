"""
Génération d'image cover via Pollinations (priorité 2) et fallback générique par secteur (priorité 3).
Conforme .cursorrules : cache obligatoire, prompt anglais, seed déterministe.
"""
import hashlib
import os
import re
import time
from urllib.parse import quote

import requests

from scripts.config import (
    COVER_HEIGHT,
    COVER_WIDTH,
    IMAGE_RETRIES,
    IMAGE_TIMEOUT,
    POLLINATIONS_BASE_URL,
    POLLINATIONS_IMAGE_PATH,
    POLLINATIONS_ENHANCE,
    POLLINATIONS_MODEL,
    POLLINATIONS_API_KEY,
    SECTEURS,
    STATIC_IMAGES_DIR,
)
from scripts.images.image_downloader import download_from_url
from scripts.utils.logger import log


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _slug_to_filename(slug):
    s = (slug or "").strip().lower()
    s = re.sub(r"[^\w\-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "cover"


# Prompts génériques par secteur (niveau 3)
GENERIC_PROMPTS = {
    "informatique-it": "modern tech office Morocco software development team professional",
    "banques-assurances": "professional bank Morocco finance building corporate",
    "automobile-aeronautique": "automotive industry Morocco engineering factory",
    "industrie-btp": "construction industry Morocco building site professional",
    "hotellerie-restauration": "hotel hospitality Morocco reception professional",
    "agroalimentaire": "food industry Morocco production facility",
    "medecine-sante": "hospital healthcare Morocco medical professional",
    "agriculture": "agriculture Morocco farming rural professional",
    "telecom": "telecommunications Morocco office technology",
    "energie": "energy sector Morocco industrial professional",
    "education": "education school Morocco teaching professional",
}


def generate_cover(job_info, slug):
    """
    Génère une image cover avec Pollinations si pas déjà en cache.
    Retourne le chemin relatif "/images/{slug}-cover.jpg" ou None.
    """
    safe_slug = _slug_to_filename(slug)
    root = _project_root()
    dir_path = os.path.join(root, STATIC_IMAGES_DIR)
    file_path = os.path.join(dir_path, f"{safe_slug}-cover.jpg")
    if os.path.exists(file_path):
        return f"/images/{safe_slug}-cover.jpg"
    os.makedirs(dir_path, exist_ok=True)
    entreprise = (job_info.get("entreprise") or "company").replace('"', "")
    poste = (job_info.get("poste") or "job position").replace('"', "")
    prompt = (
        f"Professional corporate recruitment banner, {entreprise} company, "
        f"{poste} job position, Morocco, modern office environment, "
        "blue and white professional corporate photography, no text, no watermark, "
        "4K sharp focus, professional lighting"
    )
    seed_hex = hashlib.md5(slug.encode("utf-8")).hexdigest()[:8]
    seed = int(seed_hex, 16)  # API attend un integer (reproducible)
    params = [
        f"model={POLLINATIONS_MODEL}",
        f"width={COVER_WIDTH}",
        f"height={COVER_HEIGHT}",
        f"seed={seed}",
        f"enhance={str(POLLINATIONS_ENHANCE).lower()}",
    ]
    if POLLINATIONS_API_KEY:
        params.append(f"key={POLLINATIONS_API_KEY}")
    encoded_prompt = quote(prompt)
    url = f"{POLLINATIONS_BASE_URL.rstrip('/')}{POLLINATIONS_IMAGE_PATH}/{encoded_prompt}?{'&'.join(params)}"
    for attempt in range(IMAGE_RETRIES + 1):
        try:
            r = requests.get(url, timeout=IMAGE_TIMEOUT, stream=True)
            r.raise_for_status()
            content = r.content
            if len(content) < 1000:
                raise ValueError("Image too small")
            with open(file_path, "wb") as f:
                f.write(content)
            return f"/images/{safe_slug}-cover.jpg"
        except Exception as e:
            log(f"ImageGenerator attempt {attempt + 1} failed: {e}", "WARNING")
            if attempt < IMAGE_RETRIES:
                time.sleep(5)
    return None


def get_generic_sector_path(secteur):
    """Retourne le chemin relatif de l'image générique du secteur si elle existe."""
    if not secteur:
        return None
    s = (secteur or "").strip().lower().replace(" ", "-")
    if s not in GENERIC_PROMPTS and s not in SECTEURS:
        s = "informatique-it"
    root = _project_root()
    path = os.path.join(root, STATIC_IMAGES_DIR, f"generic-{s}.jpg")
    return f"/images/generic-{s}.jpg" if os.path.exists(path) else None


def get_article_image(scraped_data, job_info, slug):
    """
    Logique de choix d'image : 1) og:image source, 2) Pollinations, 3) générique secteur, 4) défaut.
    Retourne un chemin relatif pour Hugo (ex: /images/xxx-cover.jpg).
    """
    safe_slug = _slug_to_filename(slug)
    root = _project_root()
    static_dir = os.path.join(root, STATIC_IMAGES_DIR)

    # Niveau 1: Image depuis la source (og:image)
    if scraped_data and (scraped_data.get("og_image_url") or "").strip():
        path = download_from_url(scraped_data["og_image_url"], safe_slug)
        if path:
            return path

    # Niveau 2: Pollinations
    path = generate_cover(job_info or {}, safe_slug)
    if path:
        return path

    # Niveau 3: Générique secteur
    secteur = (job_info or {}).get("secteur", "emploi")
    generic = get_generic_sector_path(secteur)
    if generic:
        return generic
    generic = get_generic_sector_path("informatique-it")
    if generic:
        return generic

    # Niveau 4: Image par défaut du site
    default_path = os.path.join(static_dir, "og-default.jpg")
    if os.path.exists(default_path):
        return "/images/og-default.jpg"
    return "/images/og-default.jpg"
