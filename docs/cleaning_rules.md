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

Mesuré sur l'exécution du pipeline complet (7 sources, voir `docs/final_evidence_map.md` C1) :

| Métrique | Avant nettoyage | Après nettoyage |
|----------|----------------|-----------------|
| Nombre de lignes | 230 173 | 188 190 |
| Doublons | 6 892 (supprimés après dédoublonnage) | 0 |
| Valeurs nulles (texte) | 0 | 0 |
| Avis < 20 caractères | 15 832 (supprimés) | 0 |
| Non-anglais (filtre langue) | 19 203 (supprimés) | — |
| Sentiments invalides | 0 | 0 |

Sources finales : amazon_reviews (49 857), csv_kaggle_imdb (49 566), yelp_reviews (49 068),
sst2_stanford (34 312), rotten_tomatoes (5 023), scraping_imdb (364).
Rapport complet et reproductible : `data/processed/cleaning_report.txt` (régénéré à chaque exécution).

## Scripts

- Nettoyage : `python -m src.transform.clean_dataset`
- Validation : `python -m src.transform.validate_dataset`
- Sortie : `data/processed/reviews_clean.csv` (non versionné — dépasse la limite de taille GitHub,
  voir `data/raw/*.csv` dans `.gitignore` ; régénérer localement via les commandes ci-dessus)
