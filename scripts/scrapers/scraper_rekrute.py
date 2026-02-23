"""
Scraper Rekrute.ma — BS4, pagination, page détail, normalisation.
URL: https://www.rekrute.com/offres.html?s=3&p={page}&o=1
"""
import re
from urllib.parse import urljoin

from scripts.config import DELAY_DEFAULT, REKRUTE_KEYWORDS
from scripts.scrapers.base_scraper import BaseScraper


class RekruteScraper(BaseScraper):
    BASE = "https://www.rekrute.com"
    LISTING_URL = "https://www.rekrute.com/offres.html?s=3&p={page}&o=1"

    def __init__(self):
        super().__init__()
        self.source_name = "rekrute.com"
        self.delay = DELAY_DEFAULT

    def _offer_links_from_page(self, soup):
        """Extrait les URLs des offres depuis la page listing (li ou cards)."""
        urls = []
        for a in soup.select("a[href*='/offres/'], a[href*='offre-'], .post a[href], .job-item a[href], li a[href]"):
            href = (a.get("href") or "").strip()
            if not href or "offres.html" in href or "p=" in href:
                continue
            if "/offre-" in href or "/offres/" in href:
                full = urljoin(self.BASE, href)
                urls.append(full)
        return list(dict.fromkeys(urls))

    def fetch(self, keywords=None, pages=3):
        """Récupère les pages de listing puis scrape chaque offre."""
        all_articles = []
        for page in range(1, pages + 1):
            url = self.LISTING_URL.format(page=page)
            soup = self.get_page(url)
            if not soup:
                continue
            links = self._offer_links_from_page(soup)
            for offer_url in links:
                data = self._scrape_offer(offer_url)
                if data and data.get("title") and data.get("apply_url"):
                    all_articles.append(data)
        return all_articles

    def _scrape_offer(self, url):
        """Scrape une page offre Rekrute."""
        soup = self.get_page(url)
        if not soup:
            return None
        title_el = soup.find("h1") or soup.select_one(".title, .job-title, h2")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None
        raw_text = self.extract_content(soup)
        apply_url = self.find_apply_link(soup, url)
        if not apply_url:
            apply_url = url
        date = ""
        for el in soup.select("[datetime], .date, .published"):
            if el.get("datetime"):
                date = el["datetime"][:10]
                break
            t = el.get_text(strip=True)
            if re.search(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}", t):
                date = t[:10] if len(t) >= 10 else t
                break
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
