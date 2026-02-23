"""
Scraper Indeed.ma — re.findall JSON embarqué + fallback BS4. Délai 5s.
URL: https://ma.indeed.com/jobs?q={keyword}&l=Maroc&fromage=2&sort=date
"""
import json
import re
from urllib.parse import quote_plus, urljoin

from scripts.config import DELAY_INDEED, REKRUTE_KEYWORDS
from scripts.scrapers.base_scraper import BaseScraper


class IndeedScraper(BaseScraper):
    BASE = "https://ma.indeed.com"
    SEARCH_URL = "https://ma.indeed.com/jobs?q={q}&l=Maroc&fromage=2&sort=date"

    def __init__(self):
        super().__init__()
        self.source_name = "indeed.ma"
        self.delay = DELAY_INDEED

    def _extract_json_jobs(self, html):
        """Extrait les jobs depuis le JSON embarqué dans la page (script type application/ld+json ou window.mosaic)."""
        jobs = []
        # Pattern courant Indeed: jobmap ou données dans script
        patterns = [
            r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});',
            r'"jobKey":"([^"]+)".*?"title":"([^"]+)".*?"companyName":"([^"]+)"',
            r'"title":"([^"]+)".*?"companyName":"([^"]+)".*?"jobKey":"([^"]+)"',
        ]
        for pattern in patterns:
            for m in re.finditer(pattern, html, re.DOTALL):
                if m.lastindex == 1:
                    try:
                        data = json.loads(m.group(1))
                        if isinstance(data, dict) and "metaData" in data:
                            meta = data.get("metaData", {}).get("mosaicProviderJobCardsModel", {})
                            results = meta.get("results", [])
                            for r in results:
                                if isinstance(r, dict):
                                    jobs.append({
                                        "key": r.get("jobKey"),
                                        "title": r.get("title"),
                                        "company": r.get("companyName"),
                                        "url": r.get("link") or ("https://ma.indeed.com/viewjob?jk=" + (r.get("jobKey") or "")),
                                    })
                    except (json.JSONDecodeError, TypeError):
                        pass
                elif m.lastindex >= 2:
                    g = m.groups()
                    title = g[0] if len(g) > 0 else ""
                    company = g[1] if len(g) > 1 else ""
                    jk = g[2] if len(g) > 2 else ""
                    if title and jk:
                        jobs.append({
                            "key": jk,
                            "title": title,
                            "company": company,
                            "url": "https://ma.indeed.com/viewjob?jk=" + jk,
                        })
        # Fallback: liens viewjob
        if not jobs:
            for m in re.finditer(r'href="(/viewjob\?jk=[^"]+)"', html):
                href = m.group(1)
                jobs.append({
                    "key": "",
                    "title": "",
                    "company": "",
                    "url": urljoin(self.BASE, href),
                })
        return jobs[:20]

    def fetch(self, keywords=None, pages=2):
        """Recherche par mots-clés (REKRUTE_KEYWORDS ou liste fournie), extraction JSON puis fallback BS4."""
        keywords = keywords or REKRUTE_KEYWORDS[:5]
        all_articles = []
        for kw in keywords[:3]:
            q = quote_plus(kw)
            url = self.SEARCH_URL.format(q=q)
            html = self.get_raw_html(url)
            if not html:
                continue
            jobs = self._extract_json_jobs(html)
            if not jobs:
                soup = self.get_page(url)
                if soup:
                    for a in soup.select('a[href*="/viewjob"]'):
                        href = a.get("href")
                        if not href:
                            continue
                        full = urljoin(self.BASE, href)
                        title_el = a.find_previous(["h2", "h3", "span"]) or a
                        title = title_el.get_text(strip=True) if title_el else "Offre Indeed"
                        jobs.append({"key": "", "title": title, "company": "", "url": full})
            for j in jobs:
                job_url = j.get("url") or ""
                title = (j.get("title") or "").strip() or "Offre d'emploi"
                company = (j.get("company") or "").strip()
                if company:
                    title = f"{title} - {company}"
                raw = {
                    "title": title,
                    "raw_text": "",
                    "source_url": job_url,
                    "apply_url": job_url,
                    "date": "",
                    "type": "prive",
                    "og_image_url": None,
                }
                all_articles.append(self.normalize(raw))
        return all_articles
