"""
Scraper emploi public + concours — Alwadifa.ma, emploi-public.ma, concours.ma.
Force type=public, pays=maroc. Conforme .cursorrules.
"""
from urllib.parse import urljoin

from scripts.config import ALWADIFA_SOURCES
from scripts.scrapers.base_scraper import BaseScraper


PUBLIC_KEYWORDS = [
    "concours", "recrutement", "alwadifa", "avis de recrutement",
    "ministère", "commune", "collectivité", "résultats", "liste",
]


class AlwadifaScraper(BaseScraper):
    SOURCES = ALWADIFA_SOURCES

    def __init__(self):
        super().__init__()
        self.source_name = "alwadifa"

    def _is_article_link(self, href, text):
        """Détecte si le lien pointe vers un article emploi public."""
        h = (href or "").lower()
        t = (text or "").lower()
        if any(kw in h for kw in ["concours", "recrutement", "avis", "alwadifa"]):
            return True
        if any(kw in t for kw in PUBLIC_KEYWORDS):
            return True
        return False

    def _listing_links(self, soup, base_url):
        """Extrait les liens vers articles/annonces depuis la page d'accueil ou listing."""
        links = []
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if not href or href.startswith("#"):
                continue
            if not any(x in href for x in ["concours", "recrutement", "avis", "emploi", "alwadifa", ".ma/"]):
                continue
            if "javascript:" in href or "mailto:" in href:
                continue
            full = urljoin(base_url, href)
            if full == base_url or full.rstrip("/") == base_url.rstrip("/"):
                continue
            text = a.get_text(strip=True)
            if self._is_article_link(href, text) or len(text) > 20:
                links.append(full)
        seen = set()
        out = []
        for u in links:
            if u in seen:
                continue
            seen.add(u)
            out.append(u)
        return out[:50]

    def scrape_article(self, url):
        """Scrape une page détail et retourne le dict normalisé (type=public)."""
        soup = self.get_page(url)
        if not soup:
            return None
        title_el = soup.find("h1") or soup.find("title")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title or len(title) < 10:
            return None
        raw_text = self.extract_content(soup)
        apply_url = self.find_apply_link(soup, url)
        date = ""
        time_el = soup.find("time", datetime=True)
        if time_el and time_el.get("datetime"):
            date = time_el["datetime"][:10]
        raw = {
            "title": title,
            "raw_text": raw_text,
            "source_url": url,
            "apply_url": apply_url or url,
            "date": date,
            "type": "public",
            "og_image_url": self.extract_og_image(soup),
        }
        return self.normalize(raw)

    def fetch(self, keywords=None, pages=3):
        """Pour chaque source, récupère la page puis les liens d'articles et scrape chaque détail."""
        all_articles = []
        for source_url in self.SOURCES:
            soup = self.get_page(source_url)
            if not soup:
                continue
            links = self._listing_links(soup, source_url)
            for link in links[:15]:
                data = self.scrape_article(link)
                if data and data.get("title") and data.get("apply_url"):
                    all_articles.append(data)
        return all_articles
