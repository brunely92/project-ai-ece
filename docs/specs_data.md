# Spécifications des données

## Sources de données

| Source | Type | Format | Volume estimé | Accès |
|--------|------|--------|--------------|-------|
| IMDB Dataset (Kaggle) | Fichier CSV | text + label | 50 000 avis | Téléchargement gratuit |
| TMDB API | API REST | JSON | ~100 films/requête | Clé API gratuite |
| quotes.toscrape.com | Scraping | HTML | ~100 citations | Accès libre |

## Contraintes

- **Confidentialité** : données publiques, pas de données personnelles sensibles
- **Format** : textes en anglais, labels binaires (positive/negative)
- **Volume** : ~50 000 avis + ~100 films + ~30 citations
- **Fréquence** : collecte ponctuelle (pas de flux continu)

## Objectif de collecte

Constituer un dataset d'avis de films labellisés pour entraîner/tester un modèle d'analyse de sentiment.

## Choix techniques

- **Langage** : Python 3.11
- **Librairies** : pandas, requests, beautifulsoup4
- **Stockage brut** : data/raw/ (fichiers CSV)
- **Stockage final** : SQLite (data/movies_reviews.sqlite)

## Règles de sauvegarde

- `data/raw/` : données brutes telles que collectées (non modifiées)
- `data/processed/` : données nettoyées et normalisées
- Les fichiers CSV volumineux sont dans .gitignore (non versionnés)
