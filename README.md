# BeJob — Blog Automatisé d'Offres d'Emploi au Maroc

Plateforme automatisée d'offres d'emploi au Maroc, conçue pour dépasser bghit-nekhdem.com sur Google.

## 🎯 Objectifs

- **Articles 1000 mots** vs 400 mots (concurrent)
- **Schema JSON-LD JobPosting** → Google Jobs (concurrent absent)
- **FAQ dans chaque article** → Google People Also Ask
- **Automatisé 24h/7j** vs rédaction humaine (concurrent)
- **Hugo statique ultra-rapide** vs WordPress lent (concurrent)
- **Présence Telegram + WhatsApp** (concurrent absent Telegram)

## 🏗️ Stack Technique

- **Générateur** : Hugo (statique)
- **Hébergement** : Netlify (gratuit, SSL auto)
- **Backend** : Python 3.11
- **LLM** : DeepSeek Chat + DeepSeek Reasoner
- **Images** : Pollinations AI (flux model)
- **Scraping** : requests + BeautifulSoup4 (lxml)
- **Automatisation** : GitHub Actions (cron)

## 📁 Structure

```
jobboard-blog/
├── scripts/
│   ├── scrapers/        # 8 scrapers (bghit, rekrute, indeed, etc.)
│   ├── agents/          # Agent IA (DeepSeek)
│   ├── images/          # Génération/téléchargement images
│   ├── publisher/       # Publication Hugo + Telegram
│   └── utils/           # Logger, déduplication, SEO scorer
├── content/             # Articles Hugo (.md)
├── layouts/             # Templates Hugo
├── assets/              # CSS + JS
└── .github/workflows/   # 5 workflows GitHub Actions
```

## 🚀 Installation

1. **Cloner le repo**
   ```bash
   git clone <repo-url>
   cd jobboard-blog
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env et ajouter :
   # DEEPSEEK_API_KEY=...
   # TELEGRAM_BOT_TOKEN=...
   # TELEGRAM_CHANNEL_ID=...
   ```

4. **Tester le pipeline localement**
   ```bash
   python scripts/main_pipeline.py --mode prive
   ```

## ⚙️ Configuration GitHub Actions

Ajouter ces secrets dans GitHub → Settings → Secrets :

- `DEEPSEEK_API_KEY` : Clé API DeepSeek
- `TELEGRAM_BOT_TOKEN` : Token bot Telegram
- `TELEGRAM_CHANNEL_ID` : ID du canal Telegram
- `POLLINATIONS_API_KEY` : (optionnel) Clé API Pollinations
- `SITE_BASE_URL` : URL du site (ex: https://bejob.ma)

## 📅 Workflows Automatisés

- **pipeline_offres.yml** : 6h, 14h, 20h UTC (offres privées)
- **pipeline_public.yml** : 7h, 15h UTC (emploi public)
- **pipeline_etranger.yml** : 9h UTC (France + Canada)
- **pipeline_editorial.yml** : 8h UTC (conseils RH)
- **maintenance.yml** : Dimanche 2h UTC (nettoyage)

## 🔧 Utilisation

### Lancer le pipeline manuellement

```bash
# Offres privées
python scripts/main_pipeline.py --mode prive

# Emploi public
python scripts/main_pipeline.py --mode public

# Emploi étranger
python scripts/main_pipeline.py --mode etranger

# Stages
python scripts/main_pipeline.py --mode stage
```

### Générer le site Hugo

```bash
hugo
# ou
hugo server
```

## 🌐 Déploiement Netlify

1. **Connecter le repo GitHub à Netlify**
   - Aller sur [netlify.com](https://netlify.com)
   - "Add new site" → "Import an existing project"
   - Connecter le repo GitHub
   - Netlify détecte automatiquement Hugo via `netlify.toml`

2. **Configuration automatique**
   - Build command : `hugo --minify` (défini dans `netlify.toml`)
   - Publish directory : `public`
   - Hugo version : 0.120.0 (défini dans `netlify.toml`)

3. **Formulaires Netlify**
   - Les formulaires (contact, newsletter, publier-offre) fonctionnent automatiquement
   - Les soumissions sont disponibles dans Netlify Dashboard → Forms

4. **Déploiement automatique**
   - Chaque push sur `main` déclenche un nouveau build
   - Les workflows GitHub Actions commitent automatiquement → Netlify rebuild automatiquement

## 📝 Notes

- Les slugs sont stockés dans `scripts/utils/published_slugs.txt` pour éviter les doublons
- Les logs sont dans `logs/pipeline.log` et `logs/errors.log`
- Les images sont dans `static/images/`
- Les articles sont dans `content/{section}/`
- Le fichier `netlify.toml` configure les headers de sécurité, cache, et redirections

## 📄 Licence

Propriétaire — BeJob 2026
