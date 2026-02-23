"""
Scraper MarocAnnonces.com — annonces emploi.
URL: https://www.marocannonces.com/categorie-12.html
"""
from urllib.parse import urljoin

from scripts.scrapers.base_scraper import BaseScraper


class MarocAnnoncesScraper(BaseScraper):
    BASE_URL = "https://www.marocannonces.com"
    JOBS_URL = "https://www.marocannonces.com/categorie-12.html"

    def __init__(self):
        super().__init__()
        self.source_name = "marocannonces.com"

    def _annonce_links(self, soup):
        """Trouve les liens des annonces (div.holder, div.annonce, li.post)."""
        urls = []
        for selector in ["div.holder a[href]", "div.annonce a[href]", "li.post a[href]", ".listing a[href]", "article a[href]"]:
            for a in soup.select(selector):
                href = (a.get("href") or "").strip()
                if not href or href.startswith("#") or "categorie-" in href:
                    continue
                full = urljoin(self.BASE_URL, href)
                if "marocannonces.com" in full and full != self.JOBS_URL:
                    urls.append(full)
        return list(dict.fromkeys(urls))[:25]

    def fetch(self, keywords=None, pages=3):
        """Page liste emploi puis scrape chaque annonce."""
        all_articles = []
        url = self.JOBS_URL
        for _ in range(pages):
            soup = self.get_page(url)
            if not soup:
                break
            for annonce_url in self._annonce_links(soup):
                data = self._scrape_annonce(annonce_url)
                if data and data.get("title") and data.get("apply_url"):
                    all_articles.append(data)
            next_a = soup.select_one('a.next, a[rel="next"], .pagination a')
            if not next_a or not next_a.get("href"):
                break
            url = urljoin(url, next_a["href"])
        return all_articles

    def _scrape_annonce(self, url):
        """Scrape une page détail annonce."""
        soup = self.get_page(url)
        if not soup:
            return None
        title_el = soup.find("h1") or soup.select_one(".title, .annonce-title, h2")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None
        raw_text = self.extract_content(soup)
        apply_url = self.find_apply_link(soup, url) or url
        date = ""
        time_el = soup.find("time", datetime=True)
        if time_el and time_el.get("datetime"):
            date = time_el["datetime"][:10]
        raw = {
            "title": title,
            "raw_text": raw_text,
            "source_url": url,
            "apply_url": apply_url,
            "date": date,
            "type": "prive",
            "og_image_url": self.extract_og_image(soup),
        }
        return self.normalize(raw)
