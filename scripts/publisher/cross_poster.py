"""
Cross-poster : Telegram (Bot API) + génération lien WhatsApp.
Conforme .cursorrules : Telegram critique au Maroc, ne jamais bloquer le pipeline.
"""
import os
import urllib.parse

import requests

from scripts.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from scripts.utils.logger import log


class CrossPoster:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
        self.channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", TELEGRAM_CHANNEL_ID)

    def post_telegram(self, article_data, article_url):
        """
        Poste dans le canal Telegram après publication.
        article_data doit contenir: job_info (entreprise, poste, ville, type_contrat, salaire).
        Retourne True si succès, False sinon (ne bloque jamais le pipeline).
        """
        if not self.bot_token or not self.channel_id:
            log("CrossPoster: TELEGRAM_BOT_TOKEN ou TELEGRAM_CHANNEL_ID manquant", "WARNING")
            return False
        job_info = article_data.get("job_info", {})
        apply_url = article_data.get("apply_url", "")
        entreprise = job_info.get("entreprise", "Entreprise")
        poste = job_info.get("poste", "Poste")
        ville = job_info.get("ville", "")
        type_contrat = job_info.get("type_contrat", "")
        salaire = job_info.get("salaire", "")
        secteur = job_info.get("secteur", "").replace("-", "")
        type_short = type_contrat.lower()
        message = f"""🆕 *{entreprise} recrute !*

📋 *Poste:* {poste}
📍 *Ville:* {ville}
💼 *Contrat:* {type_contrat}
"""
        if salaire:
            message += f"💰 *Salaire:* {salaire}\n"
        message += f"""
👉 [Voir l'offre complète]({article_url})
✅ [Postuler directement]({apply_url})

#emploimaroc #{secteur} #{type_short}
"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.channel_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        try:
            r = requests.post(url, json=payload, timeout=10)
            r.raise_for_status()
            log(f"CrossPoster: message Telegram envoyé pour {entreprise}", "INFO")
            return True
        except Exception as e:
            log(f"CrossPoster: erreur Telegram: {e}", "WARNING")
            return False

    def generate_whatsapp_url(self, title, url):
        """Génère le lien WhatsApp pour le partage (utilisé dans le template Hugo)."""
        message = f"{title} → {url}"
        return f"https://wa.me/?text={urllib.parse.quote(message)}"
