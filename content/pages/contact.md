---
title: "Contactez BeJob"
date: 2026-01-01T00:00:00+00:00
draft: false
description: "Contactez l'équipe BeJob pour vos questions, suggestions ou pour publier une offre d'emploi. Réponse rapide garantie."
---

## Nous Contacter

Vous avez une question, une suggestion, ou souhaitez publier une offre d'emploi sur BeJob ? N'hésitez pas à nous écrire !

### Formulaire de Contact

Remplissez le formulaire ci-dessous et nous vous répondrons dans les plus brefs délais.

<form name="contact" method="POST" action="https://bejob-api.YOUR-SUBDOMAIN.workers.dev/forms/contact">
  <p style="display:none">
    <label>Ne remplissez pas ce champ si vous êtes humain : <input name="bot-field" /></label>
  </p>
  
  <div class="form-group">
    <label for="name">Nom complet *</label>
    <input type="text" id="name" name="name" required aria-label="Nom complet">
  </div>
  
  <div class="form-group">
    <label for="email">Email *</label>
    <input type="email" id="email" name="email" required aria-label="Email">
  </div>
  
  <div class="form-group">
    <label for="subject">Sujet *</label>
    <select id="subject" name="subject" required aria-label="Sujet">
      <option value="">Sélectionnez un sujet</option>
      <option value="publier-offre">Publier une offre d'emploi</option>
      <option value="question">Question générale</option>
      <option value="partenariat">Partenariat</option>
      <option value="signalement">Signaler un problème</option>
      <option value="autre">Autre</option>
    </select>
  </div>
  
  <div class="form-group">
    <label for="message">Message *</label>
    <textarea id="message" name="message" rows="6" required aria-label="Message"></textarea>
  </div>
  
  <button type="submit" class="btn-apply-main">Envoyer le message</button>
</form>

### Informations de Contact

**Email** : [contact@bejob.ma](mailto:contact@bejob.ma)

**Heures de réponse** : Nous répondons généralement sous 24-48 heures.

### Publier une Offre

Vous êtes recruteur et souhaitez publier une offre d'emploi ? Consultez notre [page dédiée](/pages/publier-offre/) pour connaître nos tarifs et modalités.

### Suivez-Nous

Restez informé des dernières offres et actualités :
- **Telegram** : [Rejoindre le canal](https://t.me/bejobma)
- **Facebook** : [Page Facebook](https://facebook.com/bejobma)
- **LinkedIn** : [Page LinkedIn](https://linkedin.com/company/bejobma)

---

*Tous les champs marqués d'un astérisque (*) sont obligatoires.*
