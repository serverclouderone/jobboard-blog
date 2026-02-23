# Scrapers — jobboard-blog
from scripts.scrapers.base_scraper import BaseScraper
from scripts.scrapers.scraper_alwadifa import AlwadifaScraper
from scripts.scrapers.scraper_bghit import BghitScraper
from scripts.scrapers.scraper_emploima import EmploiMAScraper
from scripts.scrapers.scraper_indeed import IndeedScraper
from scripts.scrapers.scraper_linkedin import LinkedInScraper
from scripts.scrapers.scraper_manager import fetch_all
from scripts.scrapers.scraper_marocannonces import MarocAnnoncesScraper
from scripts.scrapers.scraper_optioncarriere import OptionCarriereScraper
from scripts.scrapers.scraper_rekrute import RekruteScraper

__all__ = [
    "BaseScraper",
    "BghitScraper",
    "AlwadifaScraper",
    "RekruteScraper",
    "EmploiMAScraper",
    "IndeedScraper",
    "OptionCarriereScraper",
    "MarocAnnoncesScraper",
    "LinkedInScraper",
    "fetch_all",
]
