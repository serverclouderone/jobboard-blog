"""
Scraper Emploi.ma — structure WordPress, liste articles, pagination.
URL: https://www.emploi.ma/recherche-emploi-maroc/
"""
from urllib.parse import urljoin

from scripts.scrapers.base_scraper import BaseScraper


class EmploiMAScraper(BaseScraper):
    BASE = "https://www.emploi.ma"
    LISTING = "https://www.emploi.ma/recherche-emploi-maroc/"

    def __init__(self):
        super().__init__()
        self.source_name = "emploi.ma"

    def _article_links(self, soup):
        """Liens vers articles depuis une page WordPress typique."""
        urls = []
        for a in soup.select("article a[href], .post a[href], .entry-title a[href], h2 a[href], h3 a[href]"):
            href = (a.get("href") or "").strip()
            if not href or href.startswith("#"):
                continue
            if "emploi.ma" not in href:
                continue
            if "/recherche-" in href or "/page/" in href or "/category/" in href or "/author/" in href:
                continue
            urls.append(urljoin(self.BASE, href))
        return list(dict.fromkeys(urls))[:25]

    def _next_page(self, soup, current_url):
        """Lien page suivante (next)."""
        next_a = soup.select_one('a.next, a[rel="next"], .pagination a.next')
        if not next_a or not next_a.get("href"):
            return None
        return urljoin(current_url, next_a["href"])

    def fetch(self, keywords=None, pages=3):
        """Listing puis scrape chaque article."""
        all_articles = []
        url = self.LISTING
        for _ in range(pages):
            soup = self.get_page(url)
            if not soup:
                break
            for link in self._article_links(soup):
                data = self._scrape_article(link)
                if data and data.get("title") and data.get("apply_url"):
                    all_articles.append(data)
            url = self._next_page(soup, url)
            if not url:
                break
        return all_articles

    def _scrape_article(self, url):
        """Scrape une page article emploi.ma."""
        soup = self.get_page(url)
        if not soup:
            return None
        title_el = soup.find("h1") or soup.select_one(".entry-title, .post-title")
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
