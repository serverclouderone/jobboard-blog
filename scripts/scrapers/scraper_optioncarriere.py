"""
Scraper Optioncarriere.ma — BS4, cards article.job.
URL: https://www.optioncarriere.ma/emploi.html?s=&l=Maroc
"""
from urllib.parse import urljoin

from scripts.scrapers.base_scraper import BaseScraper


class OptionCarriereScraper(BaseScraper):
    BASE = "https://www.optioncarriere.ma"
    LISTING = "https://www.optioncarriere.ma/emploi.html?s=&l=Maroc"

    def __init__(self):
        super().__init__()
        self.source_name = "optioncarriere.ma"

    def _job_cards(self, soup):
        """Extrait les cards job (article.job ou équivalent)."""
        cards = soup.select("article.job, .job-item, .job-card, .result-item, [data-job-id]")
        if not cards:
            cards = soup.select("article a[href*='emploi'], .list-jobs a[href]")
        urls = []
        for card in cards:
            a = card if card.name == "a" else card.select_one("a[href]")
            if not a:
                continue
            href = (a.get("href") or "").strip()
            if not href or "/emploi.html" in href:
                continue
            full = urljoin(self.BASE, href)
            if "optioncarriere.ma" in full:
                urls.append(full)
        return list(dict.fromkeys(urls))[:20]

    def _next_page(self, soup, current_url):
        next_a = soup.select_one('a.next, a[rel="next"], .pagination a[rel="next"]')
        if not next_a or not next_a.get("href"):
            return None
        return urljoin(current_url, next_a["href"])

    def fetch(self, keywords=None, pages=3):
        """Pages listing puis scrape détail."""
        all_articles = []
        url = self.LISTING
        for _ in range(pages):
            soup = self.get_page(url)
            if not soup:
                break
            for job_url in self._job_cards(soup):
                data = self._scrape_job(job_url)
                if data and data.get("title") and data.get("apply_url"):
                    all_articles.append(data)
            url = self._next_page(soup, url)
            if not url:
                break
        return all_articles

    def _scrape_job(self, url):
        """Scrape une page offre Optioncarriere."""
        soup = self.get_page(url)
        if not soup:
            return None
        title_el = soup.find("h1") or soup.select_one(".job-title, .title, h2")
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
