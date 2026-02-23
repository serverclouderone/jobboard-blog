"""
Gestion de published_slugs.txt — évite de republier le même slug.
"""
import os

from scripts.config import PUBLISHED_SLUGS_FILE


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_published_slugs():
    """Retourne l'ensemble des slugs déjà publiés."""
    path = os.path.join(_project_root(), PUBLISHED_SLUGS_FILE)
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def is_published(slug):
    """True si le slug a déjà été publié."""
    return (slug or "").strip().lower() in load_published_slugs()


def add_published_slug(slug):
    """Ajoute un slug au fichier (append)."""
    s = (slug or "").strip().lower()
    if not s:
        return
    path = os.path.join(_project_root(), PUBLISHED_SLUGS_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(s + "\n")
