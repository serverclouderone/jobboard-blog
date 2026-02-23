"""
Scraper bghit-nekhdem.com (concurrent) — catégories + articles + og:image.
Délai 4 secondes (respecter leur serveur). Conforme .cursorrules.
"""
from scripts.config import BGHIT_CATEGORIES, DELAY_BGHIT
from scripts.scrapers.base_scraper import BaseScraper


class BghitScraper(BaseScraper):
    BASE = "https://bghit-nekhdem.com"

    def __init__(self):
        super().__init__()
        self.source_name = "bghit-nekhdem.com"
        self.delay = DELAY_BGHIT

    def _article_links_from_soup(self, soup, base_url):
        """Extrait les URLs d'articles depuis une page catégorie. Exclut /category/, /author/, /tag/, /page/."""
        seen = set()
        urls = []
        for a in soup.select("article.post a[href], h2.entry-title a[href], h3.entry-title a[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            if "/category/" in href or "/author/" in href or "/tag/" in href or "/page/" in href:
                continue
            if "bghit-nekhdem.com" not in href:
                continue
            if href in seen:
                continue
            seen.add(href)
            urls.append(href)
        return urls

    def _next_page_url(self, soup, current_url):
        """Retourne l'URL de la page suivante (a.next ou a[rel='next']) ou None."""
        next_a = soup.select_one('a.next, a[rel="next"]')
        if not next_a or not next_a.get("href"):
            return None
        return urljoin(current_url, next_a["href"])

    def fetch_category(self, category_url, max_pages=3):
        """Récupère les articles d'une catégorie avec pagination."""
        all_articles = []
        url = category_url
        for _ in range(max_pages):
            soup = self.get_page(url)
            if not soup:
                break
            links = self._article_links_from_soup(soup, url)
            for article_url in links:
                data = self.scrape_article(article_url)
                if data and data.get("title") and data.get("apply_url"):
                    all_articles.append(data)
            url = self._next_page_url(soup, url)
            if not url:
                break
        return all_articles

    def _detect_type(self, url, title):
        """Détecte type: public, stage, etranger ou prive."""
        u = (url or "").lower()
        t = (title or "").lower()
        if "concours" in u or "alwadifa" in u or "concours" in t or "alwadifa" in t:
            return "public"
        if "stage" in u or "pfe" in u or "stage" in t or "pfe" in t:
            return "stage"
        if "france" in u or "canada" in u or "france" in t or "canada" in t or "étranger" in t:
            return "etranger"
        return "prive"

    def scrape_article(self, url):
        """Scrape une page article : titre, og:image, contenu, lien postuler, date, type."""
        soup = self.get_page(url)
        if not soup:
            return None
        title_el = soup.find("h1")
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            return None
        og_image = self.extract_og_image(soup)
        raw_text = self.extract_content(soup)
        apply_url = self.find_apply_link(soup, url)
        date = ""
        time_el = soup.find("time", datetime=True)
        if time_el and time_el.get("datetime"):
            date = time_el["datetime"][:10]
        type_ = self._detect_type(url, title)
        raw = {
            "title": title,
            "raw_text": raw_text,
            "source_url": url,
            "apply_url": apply_url,
            "date": date,
            "type": type_,
            "og_image_url": og_image,
        }
        return self.normalize(raw)

    def fetch(self, keywords=None, pages=3):
        """Boucle sur BGHIT_CATEGORIES et retourne la liste unifiée."""
        all_articles = []
        for cat_url in BGHIT_CATEGORIES:
            articles = self.fetch_category(cat_url, max_pages=pages)
            all_articles.extend(articles)
        return all_articles
