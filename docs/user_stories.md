# User Stories — C14

## Persona

**Marie**, analyste marketing dans une société de distribution de films. Elle souhaite comprendre rapidement le sentiment des spectateurs sur les films de son catalogue pour orienter les campagnes de promotion.

## User Stories

### US1 — Analyser un avis individuellement
**En tant qu'** analyste marketing,
**je veux** saisir un avis de film et obtenir instantanément son sentiment (positif/négatif) avec un score de confiance,
**afin de** gagner du temps par rapport à une lecture manuelle.

**Critères d'acceptation :**
- [ ] Un champ texte permet de saisir un avis (min 5, max 5000 caractères)
- [ ] Le bouton "Analyser" déclenche l'appel API
- [ ] Le sentiment est affiché avec une couleur (vert=positif, rouge=négatif)
- [ ] Le score de confiance est affiché en pourcentage
- [ ] Le temps de traitement est affiché
- [ ] Un message d'erreur clair apparaît si l'API est indisponible
- [ ] Accessibilité : labels clairs, contraste suffisant (WCAG AA)

### US2 — Consulter les statistiques globales
**En tant qu'** analyste marketing,
**je veux** visualiser les statistiques globales du dataset (distribution des sentiments, nombre d'avis par source),
**afin de** comprendre la tendance générale du corpus.

**Critères d'acceptation :**
- [ ] Graphique de distribution positif/négatif
- [ ] Nombre total d'avis affiché
- [ ] Répartition par source de collecte
- [ ] Longueur moyenne des avis
- [ ] Accessibilité : textes alternatifs pour les graphiques

### US3 — Rechercher des avis par mot-clé
**En tant qu'** analyste marketing,
**je veux** rechercher des avis contenant un mot-clé,
**afin de** identifier les thèmes récurrents (ex: "acting", "plot", "boring").

**Critères d'acceptation :**
- [ ] Champ de recherche avec min 2 caractères
- [ ] Résultats affichés avec sentiment et source
- [ ] Maximum 20 résultats par page
- [ ] Message si aucun résultat trouvé

## Accessibilité (WCAG 2.1 AA / RG2AA)

| Critère | Exigence | Implémentation |
|---------|----------|---------------|
| Contraste | Ratio ≥ 4.5:1 texte / ≥ 3:1 grands textes | Couleurs vérifiées |
| Labels | Tous les champs ont un label explicite | st.text_area avec label |
| Messages d'erreur | Textuels et explicites | Streamlit st.error() |
| Navigation clavier | Tous les éléments accessibles au clavier | Natif Streamlit |
| Langue | Attribut lang défini | HTML lang="fr" |
