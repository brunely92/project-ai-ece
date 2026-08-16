# Analyse de Sentiment d'Avis de Films

> Projet de certification RNCP 37827 — Développeur en Intelligence Artificielle
> ECE × Simplon.co — 2026

## Objectif

Application d'analyse de sentiment d'avis de films intégrant un service d'intelligence artificielle.
Le système collecte des avis depuis plusieurs sources, les stocke en base de données, les expose
via une API REST, et utilise un modèle NLP pré-entraîné pour prédire le sentiment (positif/négatif).

## Architecture

```
Utilisateur → Streamlit → FastAPI → HuggingFace Model
                              ↓
                           SQLite
```

## Installation

```bash
git clone https://github.com/<votre-org>/project-ai-ece.git
cd project-ai-ece
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec vos clés API
```

## Collecte des données

```bash
python -m src.collect.collect_csv
python -m src.collect.collect_api
python -m src.collect.collect_scraping
```

## Nettoyage

```bash
python -m src.transform.clean_dataset
```

## Base de données

```bash
python -m src.db.import_data
```

## Lancer l'API

```bash
uvicorn src.api.main:app --reload
# Documentation : http://127.0.0.1:8000/docs
```

## Lancer l'application

```bash
streamlit run app/streamlit_app.py
```

## Tests

```bash
pytest tests/ -v
```

## Structure du projet

```
project-ai-ece/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── .github/workflows/ci.yml
├── data/raw/                  # Données brutes
├── data/processed/            # Données nettoyées
├── src/collect/               # Scripts collecte (C1)
├── src/transform/             # Nettoyage (C3)
├── src/sql/                   # SQL (C2, C4)
├── src/api/                   # API FastAPI (C5, C9)
├── src/model/                 # Service IA (C8-C10)
├── src/db/                    # Import BDD (C4)
├── src/monitoring/            # Logs (C11, C20)
├── app/                       # Streamlit (C17)
├── tests/                     # Tests (C12, C18)
├── docs/                      # Documentation
├── reports/evidence/          # Captures soutenance
└── notebooks/                 # Exploration
```

## Sources de données

| Source | Type | Description |
|--------|------|------------|
| IMDB Reviews | CSV Kaggle | 50 000 avis labellisés positif/négatif |
| TMDB API | API REST | Métadonnées films |
| Site d'avis | Scraping | Avis complémentaires |

## Technologies

Python 3.11 · FastAPI · SQLite · HuggingFace Transformers · Streamlit · pytest · GitHub Actions

## Licence

Projet académique — ECE × Simplon.co 2026
