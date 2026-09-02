# Changelog

Toutes les évolutions notables du projet sont documentées ici.
Format inspiré de [Keep a Changelog](https://keepachangelog.com/), versionnage [SemVer](https://semver.org/).

## [v2.0.0] — 2026-09-02 — « PhD Edition »

### Ajouté
- **Modèle custom** TF-IDF (max_features=50000, ngrams 1-3) + LogisticRegression entraîné sur les
  188 190 avis labellisés du projet (`src/model/train_model.py`) — 90.70% accuracy sur 37 638 avis
  de test (split 80/20 stratifié, `random_state=42`).
- **Comparaison objective de 3 modèles** (`src/model/compare_models.py`) : HuggingFace DistilBERT
  vs modèle custom vs TextBlob, sur un échantillon de 2000 avis (accuracy/precision/recall/F1/latence).
- Endpoints API : `POST /predict/explain` (mots les plus influents par occlusion), `GET /model/info`,
  `POST /predict/custom`, `GET /models/comparison`, `GET /monitoring/logs`, `GET /monitoring/alerts`
  — API à 17 endpoints métier.
- Monitoring avancé : middleware de monitoring actif sur toutes les requêtes, script de health check
  périodique (`src/monitoring/health_check.py`) avec historique dans `logs/health_report.json`.
- Application Streamlit enrichie à 7 pages : ajout **Comparaison de modèles** et **Analyse avancée**
  (distribution des scores de qualité, fréquence des mots par sentiment, mots les plus discriminants
  du modèle custom, corrélation note du film / sentiment moyen), export CSV sur la page Recherche.
- **Architecture Decision Records** (`docs/adr/`) : choix du SGBD (SQLite), des modèles IA
  (DistilBERT + custom), du framework API (FastAPI), avec alternatives écartées et conséquences.
- CI/CD renforcée : job de lint (`ruff check`), couverture de tests (`pytest-cov`), configuration
  `ruff.toml` dédiée.
- 17 nouveaux tests API + 7 tests du modèle custom → **59 tests au total**.
- Gestion d'un incident réel (pas simulé) : caractères Unicode/emoji provoquant un crash de
  `/predict`, corrigé via la branche `fix/incident-encoding` (voir `docs/incident_report.md`).

### Corrigé
- `/predict` crashait (500) sur des textes contenant des emojis — les emojis sont désormais filtrés
  avant l'appel au modèle (`fix(api): handle unicode/emoji in /predict`).

### Modifié
- Documentation réconciliée avec l'état réel du pipeline (7 sources, 188 190 lignes après nettoyage,
  183 films TMDB, 40 films OMDB) — voir `docs/final_evidence_map.md`, `docs/cleaning_rules.md`,
  `docs/specs_data.md`.
- `data/processed/*.csv` exclu du versionnement Git (dépasse la limite de 100 Mo de GitHub).

## [v1.0.0] — 2026-08-29 — MVP

### Ajouté
- Pipeline de collecte multi-sources (IMDB Kaggle, SST-2 Stanford, Rotten Tomatoes, Amazon, Yelp,
  OMDB, scraping) → dataset nettoyé et validé (~230K lignes brutes).
- Base de données SQLite normalisée 3NF (genres, sources, films, reviews, predictions, data_lineage).
- API FastAPI (endpoints données + prédiction de sentiment via HuggingFace DistilBERT) avec
  authentification par clé API et documentation Swagger.
- Application Streamlit (analyse de sentiment, statistiques, recherche, dashboard IA, catalogue films).
- Monitoring (logger structuré, seuils d'alerte) et 14 tests pytest (données + API).
- Pipeline CI GitHub Actions (génération dataset, nettoyage, import, tests).
- Documentation complète : spécifications techniques, MCD/MPD, RGPD, veille technique, benchmark
  des services IA, user stories, gestion de projet agile, procédure de release.
