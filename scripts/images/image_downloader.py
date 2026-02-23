"""
Téléchargement de l'image og:image depuis la source (priorité 1).
Sauvegarde dans static/images/{slug}-cover.jpg. Conforme .cursorrules.
"""
import os
import re

import requests

from scripts.config import IMAGE_TIMEOUT, STATIC_IMAGES_DIR


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _slug_to_filename(slug):
    """Garde uniquement caractères sûrs pour le fichier."""
    s = (slug or "").strip().lower()
    s = re.sub(r"[^\w\-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "cover"


def download_from_url(image_url, slug):
    """
    Télécharge l'image depuis image_url et la sauvegarde en static/images/{slug}-cover.jpg.
    Retourne le chemin relatif Hugo "/images/{slug}-cover.jpg" ou None en cas d'échec.
    """
    if not (image_url or "").strip().startswith("http"):
        return None
    safe_slug = _slug_to_filename(slug)
    root = _project_root()
    dir_path = os.path.join(root, STATIC_IMAGES_DIR)
    file_path = os.path.join(dir_path, f"{safe_slug}-cover.jpg")
    if os.path.exists(file_path):
        return f"/images/{safe_slug}-cover.jpg"
    os.makedirs(dir_path, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/*",
    }
    try:
        r = requests.get(image_url, timeout=IMAGE_TIMEOUT, headers=headers, stream=True)
        r.raise_for_status()
        ct = (r.headers.get("Content-Type") or "").lower()
        if not ct.startswith("image/"):
            return None
        content = r.content
        if len(content) < 10 * 1024:
            return None
        with open(file_path, "wb") as f:
            f.write(content)
        return f"/images/{safe_slug}-cover.jpg"
    except Exception:
        return None
