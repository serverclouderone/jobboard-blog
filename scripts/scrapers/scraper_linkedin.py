"""
Scraper LinkedIn — offres publiques sans authentification.
API guest: seeMoreJobPostings. Délai 6s. Conforme .cursorrules.
"""
from urllib.parse import quote_plus, urljoin

from scripts.config import DELAY_LINKEDIN
from scripts.scrapers.base_scraper import BaseScraper


LINKEDIN_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class LinkedInScraper(BaseScraper):
    SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    BASE = "https://www.linkedin.com"

    def __init__(self):
        super().__init__()
        self.source_name = "linkedin.com"
        self.delay = DELAY_LINKEDIN

    def _headers(self):
        return {
            "User-Agent": LINKEDIN_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Referer": "https://www.linkedin.com/jobs/search/",
        }

    def _build_search_url(self, keywords=None, start=0):
        """URL API guest avec keywords et offset."""
        kw = (keywords or ["emploi"])[0]
        params = f"keywords={quote_plus(kw)}&location=Morocco&start={start}"
        return f"{self.SEARCH_URL}?{params}"

    def fetch(self, keywords=None, pages=2):
        """Récupère les résultats via seeMoreJobPostings (HTML public)."""
        keywords = keywords or ["emploi", "Maroc"]
        all_articles = []
        for kw in keywords[:2]:
            for page in range(pages):
                start = page * 25
                url = self._build_search_url(keywords=[kw], start=start)
                soup = self.get_page(url)
                if not soup:
                    continue
                for card in soup.select("li.result-card, div.result-card, [data-job-id]"):
                    job_id = card.get("data-job-id")
                    a = card.select_one("a[href*='/jobs/view/']")
                    if not a:
                        continue
                    href = (a.get("href") or "").strip()
                    if not href.startswith("http"):
                        href = urljoin(self.BASE, href)
                    title_el = card.select_one("h3.result-card__title, .result-card__title, h3")
                    title = title_el.get_text(strip=True) if title_el else "Offre LinkedIn"
                    company_el = card.select_one("h4.result-card__subtitle, .result-card__subtitle, h4")
                    company = company_el.get_text(strip=True) if company_el else ""
                    location_el = card.select_one("span.job-result-card__location, .result-card__location")
                    location = location_el.get_text(strip=True) if location_el else ""
                    if company:
                        title = f"{title} - {company}"
                    raw = {
                        "title": title,
                        "raw_text": location,
                        "source_url": href,
                        "apply_url": href,
                        "date": "",
                        "type": "prive",
                        "og_image_url": None,
                    }
                    all_articles.append(self.normalize(raw))
        return all_articles
