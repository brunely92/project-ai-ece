# Spécifications des données

## Sources de données

| Source | Type | Format | Volume réel | Accès |
|--------|------|--------|--------------|-------|
| IMDB Dataset (Kaggle) | Fichier CSV | text + label | 50 000 avis | Téléchargement manuel |
| SST-2 Stanford | HuggingFace Hub | text + label | 68 221 phrases | Gratuit |
| Rotten Tomatoes | HuggingFace Hub | text + label | 10 662 avis | Gratuit |
| Amazon Polarity | HuggingFace Hub | text + label | 50 000 avis | Gratuit |
| Yelp Polarity | HuggingFace Hub | text + label | 50 000 avis | Gratuit |
| OMDB API | API REST | JSON | 40 films | Clé API gratuite |
| Scraping (4 sites) | Scraping | HTML | 1 280 avis | Accès libre |
| TMDB API | API REST | JSON | 183 films (popular + top_rated) | Clé API gratuite |

## Contraintes

- **Confidentialité** : données publiques, pas de données personnelles sensibles
- **Format** : textes en anglais, labels binaires (positive/negative)
- **Volume** : 230 173 avis bruts / 188 190 après nettoyage (6 sources labellisées) + 183 films TMDB + 40 films OMDB
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
