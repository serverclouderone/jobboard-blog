import os

# ── DEEPSEEK ──────────────────────────────────────────────────────
DEEPSEEK_API_KEY      = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL     = "https://api.deepseek.com"
DEEPSEEK_CHAT_MODEL   = "deepseek-chat"
DEEPSEEK_THINK_MODEL  = "deepseek-reasoner"  # Modèle de raisonnement

# ── POLLINATIONS ──────────────────────────────────────────────────
# API officielle: https://gen.pollinations.ai/image/{prompt}?model=flux&width=&height=&seed=&enhance=
# Alternative sans auth: https://image.pollinations.ai/prompt/{prompt}
POLLINATIONS_BASE_URL = "https://gen.pollinations.ai"
POLLINATIONS_IMAGE_PATH = "/image"  # GET /image/{prompt}
POLLINATIONS_MODEL    = "flux"
POLLINATIONS_NOLOGO   = True
POLLINATIONS_ENHANCE  = True
POLLINATIONS_API_KEY  = os.environ.get("POLLINATIONS_API_KEY", "")

# ── TELEGRAM ──────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID   = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# ── PIPELINE ──────────────────────────────────────────────────────
MAX_ARTICLES_PER_RUN  = 8
ARTICLE_MIN_WORDS     = 800
ARTICLE_TARGET_WORDS  = 1000
MAX_RAW_TEXT_CHARS    = 3500
MAX_ARTICLE_AGE_HOURS = 48

# ── IMAGES ────────────────────────────────────────────────────────
COVER_WIDTH           = 1200
COVER_HEIGHT          = 630
IMAGE_TIMEOUT         = 60
IMAGE_RETRIES         = 2

# ── DELAYS SCRAPING ───────────────────────────────────────────────
DELAY_BGHIT           = 4.0   # Concurrent (respecter)
DELAY_INDEED          = 5.0
DELAY_LINKEDIN        = 6.0
DELAY_DEFAULT         = 2.5

# ── HUGO ──────────────────────────────────────────────────────────
CONTENT_DIRS = {
    "prive":    "content/offres",
    "public":   "content/public",
    "etranger": "content/etranger",
    "stage":    "content/stage",
    "conseil":  "content/conseils",
    "concours": "content/concours",
}
STATIC_IMAGES_DIR     = "static/images"
PUBLISHED_SLUGS_FILE  = "scripts/utils/published_slugs.txt"
LOG_FILE              = "logs/pipeline.log"
ERRORS_LOG_FILE       = "logs/errors.log"
REJECTED_LOG_FILE     = "logs/rejected.log"

# ── SCRAPING SOURCES ──────────────────────────────────────────────
BGHIT_CATEGORIES = [
    "https://bghit-nekhdem.com/category/emploi-maroc/",
    "https://bghit-nekhdem.com/category/emploi-public/",
    "https://bghit-nekhdem.com/category/alwadifa-maroc/",
    "https://bghit-nekhdem.com/category/emploi-etranger/retrouvez-sur-cette-page-tous-les-offres-en-france/",
    "https://bghit-nekhdem.com/category/emploi-etranger/retrouvez-sur-cette-page-tous-les-offres-demploi-au-canada/",
    "https://bghit-nekhdem.com/category/stage/",
]

REKRUTE_KEYWORDS = [
    "développeur", "ingénieur", "commercial", "comptable",
    "marketing", "ressources humaines", "logistique", "data",
    "chef de projet", "juriste", "technicien", "designer"
]

ALWADIFA_SOURCES = [
    "https://www.alwadifa.ma/",
    "https://concours.ma/",
    "https://www.emploi-public.ma/",
]

# ── TAXONOMIES ────────────────────────────────────────────────────
SECTEURS = [
    "automobile-aeronautique", "banques-assurances", "informatique-it",
    "industrie-btp", "hotellerie-restauration", "agroalimentaire",
    "medecine-sante", "agriculture", "telecom", "energie", "education"
]
FONCTIONS = [
    "audit-controle", "commercial", "finance-comptabilite", "ingenieurs",
    "juridique-droit", "marketing", "ressources-humaines",
    "logistique-supply-chain", "techniciens"
]
VILLES_MAROC = [
    "Casablanca", "Rabat", "Marrakech", "Fès", "Tanger",
    "Agadir", "Meknès", "Oujda", "Kénitra", "Tétouan",
    "El Jadida", "Mohammedia", "Settat", "Berrechid", "Salé"
]
