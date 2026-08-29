# Flux de données — C15

## Flux global

```
 SOURCES                  TRAITEMENT              STOCKAGE            EXPOSITION          APPLICATION
┌────────┐              ┌────────────┐           ┌────────┐         ┌──────────┐        ┌───────────┐
│CSV     │──┐           │            │           │        │         │          │        │           │
│Kaggle  │  │  collect  │  clean     │  import   │ SQLite │  API    │ FastAPI  │  HTTP  │ Streamlit │
├────────┤  ├─────────> │  validate  │ ───────>  │  BDD   │ ─────> │ /reviews │ ────> │ Dashboard │
│API     │  │           │  transform │           │        │         │ /predict │        │ Analyse   │
│TMDB    │──┤           │            │           └────────┘         │ /search  │        │ Recherche │
├────────┤  │           └────────────┘                              │ /stats   │        └───────────┘
│Scraping│──┘                                                       └──────────┘
└────────┘
```

## Traçabilité des données

| Étape | Entrée | Sortie | Script |
|-------|--------|--------|--------|
| Collecte CSV | IMDB_Dataset.csv | data/raw/imdb_reviews_raw.csv | collect_csv.py |
| Collecte API | API TMDB | data/raw/tmdb_movies_raw.csv | collect_api.py |
| Collecte scraping | Page web | data/raw/scraped_reviews_raw.csv | collect_scraping.py |
| Nettoyage | data/raw/*.csv | data/processed/reviews_clean.csv | clean_dataset.py |
| Validation | data/processed/ | Rapport console | validate_dataset.py |
| Import BDD | data/processed/ | data/movies_reviews.sqlite | import_data.py |
| API données | SQLite | JSON | src/api/main.py |
| Prédiction | Texte utilisateur | JSON (sentiment, score) | src/api/main.py |
