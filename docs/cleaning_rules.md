# Règles de nettoyage du dataset — C3

## Règles appliquées (dans l'ordre)

| # | Règle | Justification | Impact |
|---|-------|--------------|--------|
| 1 | Suppression doublons exacts | Éviter le sur-apprentissage | Variable |
| 2 | Suppression lignes sans texte | Données inexploitables | Variable |
| 3 | Nettoyage HTML et caractères spéciaux | Bruit pour le modèle NLP | Tous les textes |
| 4 | Normalisation espaces multiples | Cohérence format | Tous les textes |
| 5 | Filtre longueur minimum (< 20 car) | Avis trop courts non informatifs | Variable |
| 6 | Normalisation sentiments (lowercase) | Cohérence labels | Avis labellisés |

## Tableau avant/après

| Métrique | Avant nettoyage | Après nettoyage |
|----------|----------------|-----------------|
| Nombre de lignes | À compléter | À compléter |
| Doublons | À compléter | 0 |
| Valeurs nulles (texte) | À compléter | 0 |
| Avis < 20 caractères | À compléter | 0 |
| Sentiments invalides | À compléter | 0 |

## Scripts

- Nettoyage : `python -m src.transform.clean_dataset`
- Validation : `python -m src.transform.validate_dataset`
- Sortie : `data/processed/reviews_clean.csv`
