"""
Classe parente pour tous les scrapers. Session, headers, clean_text, extract_content, normalize.
Conforme .cursorrules : requests + BeautifulSoup4 (lxml) uniquement.
"""
import random
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from scripts.config import DELAY_DEFAULT, MAX_RAW_TEXT_CHARS


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


class BaseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.source_name = ""
        self.delay = DELAY_DEFAULT

    def _headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        }

    def get_page(self, url):
        """Récupère l'URL et retourne un BeautifulSoup ou None. Gère 200/403/429/404. Délai après requête."""
        try:
            r = self.session.get(
                url,
                headers=self._headers(),
                timeout=15,
                allow_redirects=True,
            )
            time.sleep(self.delay)
            if r.status_code == 200:
                return BeautifulSoup(r.text, "lxml")
            if r.status_code in (403, 429):
                return None  # Blocage / rate limit
            if r.status_code == 404:
                return None
            return None
        except requests.RequestException:
            return None

    def get_raw_html(self, url):
        """Même logique que get_page mais retourne le texte brut."""
        try:
            r = self.session.get(
                url,
                headers=self._headers(),
                timeout=15,
                allow_redirects=True,
            )
            time.sleep(self.delay)
            if r.status_code == 200:
                return r.text
            return None
        except requests.RequestException:
            return None

    def extract_og_image(self, soup):
        """Retourne l'URL absolue de og:image ou None."""
        if not soup:
            return None
        meta = soup.find("meta", property="og:image")
        if not meta or not meta.get("content"):
            return None
        url = meta["content"].strip()
        if not url.startswith("http"):
            return None
        return url

    def find_apply_link(self, soup, page_url):
        """Cherche un lien postuler/apply/candidater. Fallback: page_url."""
        if not soup or not page_url:
            return page_url or ""
        base = page_url.rsplit("/", 1)[0] + "/" if "/" in page_url else page_url
        keywords = ["postuler", "apply", "candidater", "candidature", "postuler maintenant"]
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            text = (a.get_text() or "").lower()
            if not href or href.startswith("#"):
                continue
            if any(kw in text for kw in keywords):
                return urljoin(base, href)
            if any(kw in href.lower() for kw in ["postuler", "apply", "candidat"]):
                return urljoin(base, href)
        return urljoin(base, page_url)

    def clean_text(self, text):
        """Nettoyage complet du texte : espaces, sauts de ligne, caractères indésirables."""
        if not text or not isinstance(text, str):
            return ""
        t = text
        t = re.sub(r"\r\n", "\n", t)
        t = re.sub(r"\r", "\n", t)
        t = re.sub(r"\t", " ", t)
        t = re.sub(r" +", " ", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", t)
        t = t.strip()
        return t

    def extract_content(self, soup):
        """Extrait le contenu principal : supprime script/style/nav/header/footer/aside/form, trouve zone principale, limite à MAX_RAW_TEXT_CHARS."""
        if not soup:
            return ""
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "form"]):
            tag.decompose()
        body = soup.find("body")
        if not body:
            body = soup
        for selector in ["main", "article", "div#content", "div.content", ".post-content", ".entry-content"]:
            zone = body.select_one(selector)
            if zone:
                body = zone
                break
        paras = body.find_all("p") if body else []
        if len(paras) >= 3:
            parts = []
            for p in paras:
                t = self.clean_text(p.get_text())
                if t:
                    parts.append(t)
            text = "\n\n".join(parts)
        else:
            text = self.clean_text(body.get_text(separator="\n"))
        if len(text) > MAX_RAW_TEXT_CHARS:
            text = text[:MAX_RAW_TEXT_CHARS].rsplit(" ", 1)[0] + "..."
        return text

    def normalize(self, raw):
        """
        Format standard obligatoire pour le pipeline.
        raw peut être un dict avec au minimum: title, raw_text, source_url, apply_url, date, type.
        Retourne un dict avec les clés: title, raw_text, source_url, apply_url, date, type, source_name, og_image_url (optionnel).
        """
        title = (raw.get("title") or "").strip() or "Offre d'emploi"
        raw_text = (raw.get("raw_text") or "").strip()
        source_url = (raw.get("source_url") or "").strip()
        apply_url = (raw.get("apply_url") or source_url or "").strip()
        date = (raw.get("date") or "")[:10] if raw.get("date") else ""
        type_ = (raw.get("type") or "prive").strip().lower()
        if type_ not in ("prive", "public", "etranger", "stage", "concours"):
            type_ = "prive"
        return {
            "title": title,
            "raw_text": raw_text,
            "source_url": source_url,
            "apply_url": apply_url,
            "date": date,
            "type": type_,
            "source_name": self.source_name,
            "og_image_url": raw.get("og_image_url"),
        }
