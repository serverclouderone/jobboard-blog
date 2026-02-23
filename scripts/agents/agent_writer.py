"""
Agent IA complet — 3 appels DeepSeek : extraction (reasoner), rédaction (chat), métadonnées SEO (chat).
Conforme .cursorrules : deepseek-reasoner pour extraction, deepseek-chat pour article + SEO.
"""
import json
import os
import re

from openai import OpenAI

from scripts.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_CHAT_MODEL,
    DEEPSEEK_THINK_MODEL,
    FONCTIONS,
    SECTEURS,
)
from scripts.utils.logger import log


class ArticleWriterAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", DEEPSEEK_API_KEY),
            base_url=DEEPSEEK_BASE_URL,
        )

    # ─────────────────────────────────────────────────────────────
    # APPEL 1 — Extraction avec deepseek-reasoner
    # ─────────────────────────────────────────────────────────────

    def _extract(self, scraped_data):
        """Extrait les infos structurées du texte brut (modèle raisonnement)."""
        title = (scraped_data.get("title") or "").strip()
        raw_text = (scraped_data.get("raw_text") or "").strip()
        source_url = (scraped_data.get("source_url") or "").strip()
        if not title:
            return None
        secteurs_str = " | ".join(SECTEURS)
        fonctions_str = " | ".join(FONCTIONS)
        user_prompt = f"""
Analyse ce texte brut d'une page web d'offre d'emploi et extrais les infos.

TITRE DE LA PAGE: {title}
TEXTE BRUT:
{raw_text[:3200]}
URL SOURCE: {source_url}

Retourne ce JSON exact (pas de texte avant/après):
{{
    "poste": "intitulé exact du poste (ou liste si plusieurs postes)",
    "nombre_postes": 1,
    "entreprise": "nom de l'entreprise",
    "ville": "ville(s) au Maroc",
    "region": "grand-casablanca | rabat-sale-kenitra | tanger-tetouan | marrakech-safi | fes-meknes | oriental | el-jadida | du-sud",
    "pays": "maroc | france | canada",
    "secteur": "un secteur parmi: {secteurs_str}",
    "fonction": "une fonction parmi: {fonctions_str}",
    "type_contrat": "CDI | CDD | Stage | PFE | Freelance | Concours | Alternance",
    "type_article": "prive | public | etranger | stage | concours",
    "salaire": "fourchette ou vide",
    "competences": ["compétence1", "compétence2"],
    "diplome": "niveau diplôme requis ou vide",
    "experience": "années d'expérience requises ou vide",
    "avantages": "avantages mentionnés ou vide",
    "description_courte": "résumé du poste en 2 phrases max",
    "profil": "profil idéal en 1 phrase",
    "entreprise_description": "description de l'entreprise si disponible",
    "remote": true ou false,
    "urgent": true si mention urgence,
    "focus_keyword_seo": "mot-clé SEO principal ex: ingénieur informatique casablanca 2026",
    "slug": "entreprise-poste-ville-annee tout en minuscules tirets sans accents"
}}
"""
        try:
            resp = self.client.chat.completions.create(
                model=DEEPSEEK_THINK_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un expert RH marocain spécialisé dans l'analyse d'offres d'emploi. Tu extrais les informations clés d'un texte brut avec précision maximale. Le marché ciblé est le Maroc. Tu réponds UNIQUEMENT en JSON valide, sans markdown ni texte autour.",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                return None
            # Nettoyer d'éventuels blocs markdown
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text).rstrip("`")
            return json.loads(text)
        except Exception as e:
            log(f"Agent _extract error: {e}", "ERROR")
            return None

    # ─────────────────────────────────────────────────────────────
    # APPEL 2 — Rédaction article avec deepseek-chat
    # ─────────────────────────────────────────────────────────────

    def _write(self, scraped_data, job_info):
        """Rédige l'article Markdown complet (850–1000 mots)."""
        apply_url = (scraped_data.get("apply_url") or "").strip()
        job_json = json.dumps(job_info, ensure_ascii=False, indent=2)
        focus = (job_info.get("focus_keyword_seo") or "").strip()
        type_article = (job_info.get("type_article") or "prive").strip()
        entreprise = (job_info.get("entreprise") or "L'entreprise").strip()
        ville = (job_info.get("ville") or "").strip()
        n_postes = job_info.get("nombre_postes") or 1

        user_prompt = f"""
Rédige un article de blog complet sur cette opportunité d'emploi.

DONNÉES EXTRAITES:
{job_json}

LIEN POSTULER: {apply_url}
MOT-CLÉ SEO: {focus}
TYPE D'ARTICLE: {type_article}

STRUCTURE OBLIGATOIRE (respecter exactement):

## {entreprise} Recrute {n_postes} Poste(s) à {ville} – 2026
[Paragraphe d'accroche: 120-150 mots. Présenter l'opportunité de façon attractive. Intégrer naturellement: {focus} Mentionner: entreprise, poste, ville, type de contrat, pourquoi c'est une belle opportunité]

## À propos de {entreprise}
[120-200 mots. Présenter l'entreprise si le texte le permet. Si les infos sur {entreprise} ne sont pas clairement présentes dans l'annonce, NE PAS INVENTER. Dans ce cas, expliquer en 1 phrase que l'annonce donne peu d'informations sur l'entreprise, puis donner un bref contexte sur le secteur (sans attribuer ces faits à l'entreprise).]

## Postes à Pourvoir chez {entreprise}
[Pour chaque poste mentionné:]
### [Titre exact du poste]
**Missions principales:**
- [Mission 1]
- [Mission 2]
- [Mission 3]

**Profil recherché:**
- [Compétence/qualité 1]
- [Compétence/qualité 2]

## Conditions du Poste
[Tableau ou liste: Type de contrat, Ville, Salaire, Expérience, Formation, Avantages]

## Comment Postuler chez {entreprise}
[80-100 mots. Instructions claires: qui peut postuler, quoi préparer (CV, lettre), délai si mentionné. Note: postuler via le bouton ci-dessous.]

{{{{< apply-button url="{apply_url}" text="Postuler maintenant →" >}}}}

## FAQ – Questions Fréquentes
[3 questions-réponses PERTINENTES qu'un candidat se poserait:]

**Q: [Question spécifique au poste ou à l'entreprise] ?**
R: [Réponse utile, 2-3 phrases]

**Q: [Question sur le processus de candidature ou les conditions] ?**
R: [Réponse utile]

**Q: [Question sur l'entreprise ou les perspectives] ?**
R: [Réponse utile]

RÈGLES RÉDACTION:
- Longueur totale: environ 850 à 1100 mots (sans mentionner le nombre de mots).
- Ton: professionnel, clair, naturel, orienté candidat.
- Mot-clé SEO "{focus}": intégrer au maximum 1-2 fois, uniquement si ça sonne naturel.
- Zéro blabla: éviter les phrases creuses. Chaque paragraphe doit aider le candidat.
- Style "humain": varier la longueur des phrases, utiliser des formulations naturelles, éviter les répétitions.
- Exactitude: ne pas inventer de chiffres, d'avantages, de lieux, ou de faits sur l'entreprise.
- Sous-titres H3 si une section devient longue.
- Listes à puces pour missions et compétences.
- Si type_article=public: insister sur stabilité emploi public, avantages fonctionnaires.
- Si type_article=etranger: insister sur démarches visa/permis, salaire €/CAD.
- Si type_article=stage: insister sur expérience professionnelle, réseau, perspectives.
- Écris en Markdown pur, JAMAIS de HTML dans le contenu.
"""
        try:
            resp = self.client.chat.completions.create(
                model=DEEPSEEK_CHAT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un expert en rédaction web SEO pour les offres d'emploi au Maroc. Tu rédiges des articles engageants, professionnels et optimisés pour Google. Tu donnes envie aux candidats de postuler. Tu écris en Markdown pur, JAMAIS de HTML brut dans le contenu.",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.75,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            log(f"Agent _write error: {e}", "ERROR")
            return None

    # ─────────────────────────────────────────────────────────────
    # APPEL 3 — Métadonnées SEO avec deepseek-chat
    # ─────────────────────────────────────────────────────────────

    def _seo(self, job_info):
        """Génère title_seo, meta_description, slug, keywords, og_*, faq_schema."""
        poste = (job_info.get("poste") or "").strip()
        entreprise = (job_info.get("entreprise") or "").strip()
        ville = (job_info.get("ville") or "").strip()
        type_contrat = (job_info.get("type_contrat") or "").strip()
        focus = (job_info.get("focus_keyword_seo") or "").strip()
        slug = (job_info.get("slug") or "").strip()

        user_prompt = f"""
Génère les métadonnées SEO optimales pour cet article.

POSTE: {poste}
ENTREPRISE: {entreprise}
VILLE: {ville}
TYPE: {type_contrat}
MOT-CLÉ: {focus}
SLUG SUGGÉRÉ: {slug}

RÈGLES STRICTES:
- title_seo: EXACTEMENT entre 55 et 60 caractères. Format: "[Entreprise] Recrute [Poste] à [Ville] 2026"
- meta_description: EXACTEMENT entre 150 et 160 caractères. Contient le mot-clé, donne envie de cliquer, mentionne le type de contrat.
- slug: minuscules, tirets, sans accents, sans espaces. Format: entreprise-recrute-poste-ville-2026
- Retourne UNIQUEMENT un objet JSON valide avec les clés: title_seo, meta_description, slug, focus_keyword, secondary_keywords (liste), og_title, og_description, faq_schema (liste de {{"question": "...", "answer": "..."}} avec 3 éléments).
"""
        try:
            resp = self.client.chat.completions.create(
                model=DEEPSEEK_CHAT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu génères des métadonnées SEO en JSON uniquement. Pas de texte avant ou après le JSON.",
                    },
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            text = (resp.choices[0].message.content or "").strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text).rstrip("`")
            return json.loads(text)
        except Exception as e:
            log(f"Agent _seo error: {e}", "ERROR")
            return None

    # ─────────────────────────────────────────────────────────────
    # MÉTHODE PRINCIPALE: generate(scraped_data) → dict | None
    # ─────────────────────────────────────────────────────────────

    def generate(self, scraped_data):
        """
        Enchaîne: extraction → rédaction → SEO.
        Retourne un dict avec article, meta, job_info, apply_url, source_url, etc. ou None en cas d'erreur.
        """
        if not scraped_data or not (scraped_data.get("title") or "").strip():
            log("Agent generate: scraped_data vide ou sans titre", "WARNING")
            return None
        try:
            job_info = self._extract(scraped_data)
            if not job_info:
                log("Agent generate: _extract a retourné vide", "WARNING")
                return None
            article = self._write(scraped_data, job_info)
            if not article:
                log("Agent generate: _write a retourné vide", "WARNING")
                return None
            meta = self._seo(job_info)
            if not meta:
                meta = {}
                meta["title_seo"] = (scraped_data.get("title") or "")[:60]
                meta["meta_description"] = (job_info.get("description_courte") or "")[:160]
                meta["slug"] = (job_info.get("slug") or "offre-emploi-2026").strip().lower()
                meta["focus_keyword"] = job_info.get("focus_keyword_seo") or ""
                meta["secondary_keywords"] = []
                meta["og_title"] = meta["title_seo"]
                meta["og_description"] = (meta["meta_description"] or "")[:120]
                meta["faq_schema"] = []

            # Harmoniser le slug (minuscules, tirets, sans accents)
            slug = (meta.get("slug") or job_info.get("slug") or "offre-2026").strip().lower()
            slug = re.sub(r"[^\w\-]", "-", slug)
            slug = re.sub(r"-+", "-", slug).strip("-")
            meta["slug"] = slug or "offre-emploi-2026"

            word_count = len(article.split())
            return {
                "article": article,
                "meta": meta,
                "job_info": job_info,
                "apply_url": (scraped_data.get("apply_url") or "").strip(),
                "source_url": (scraped_data.get("source_url") or "").strip(),
                "word_count": word_count,
                "og_image_url": scraped_data.get("og_image_url"),
            }
        except Exception as e:
            log(f"Agent generate error: {e}", "ERROR")
            return None
