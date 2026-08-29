# Carte finale des preuves — Soutenance RNCP 37827

## Bloc 1 — Collecte, stockage et mise à disposition des données

| Compétence | Preuve | Fichier Git | Commande de reproduction |
|-----------|--------|------------|-------------------------|
| C1 | Scripts collecte 3 sources + logs | src/collect/*.py | `python -m src.collect.download_dataset` |
| C2 | 7 requêtes SQL documentées | src/sql/queries.sql | `sqlite3 data/movies_reviews.sqlite < src/sql/queries.sql` |
| C3 | Pipeline nettoyage + validation + avant/après | src/transform/*.py + docs/cleaning_rules.md | `python -m src.transform.clean_dataset` |
| C4 | MCD/MPD + schema + import + RGPD | src/sql/schema.sql + docs/mcd_mpd.md + docs/rgpd.md | `python -m src.db.import_data` |
| C5 | API FastAPI 5 endpoints + auth + Swagger | src/api/main.py | `uvicorn src.api.main:app --reload` → /docs |

## Bloc 2 — Intégrer modèles et services IA

| Compétence | Preuve | Fichier Git | Commande de reproduction |
|-----------|--------|------------|-------------------------|
| C6 | Sources qualifiées + synthèse veille | docs/watch.md | Lecture document |
| C7 | Benchmark 4 services + matrice + recommandation | docs/benchmark.md | Lecture document |
| C8 | Configuration HuggingFace + test | docs/service_ia.md + scripts/test_ai_service.py | `python scripts/test_ai_service.py` |
| C9 | Endpoint POST /predict + auth + tests | src/api/main.py + tests/test_api.py | `curl -X POST /predict` |
| C10 | App Streamlit connectée API | app/streamlit_app.py | `streamlit run app/streamlit_app.py` |
| C11 | Logger structuré + seuils + alertes | src/monitoring/logger.py + docs/monitoring.md | Lecture logs/ |
| C12 | 14 tests pytest (données + API) | tests/test_data.py + tests/test_api.py | `pytest tests/ -v` |
| C13 | Pipeline GitHub Actions | .github/workflows/ci.yml | Push → voir Actions tab |

## Bloc 3 — Réaliser une application intégrant un service IA

| Compétence | Preuve | Fichier Git | Commande de reproduction |
|-----------|--------|------------|-------------------------|
| C14 | 3 user stories + critères acceptation + accessibilité | docs/user_stories.md | Lecture document |
| C15 | Architecture MVC + flux données + choix justifiés | docs/technical_specifications.md + docs/data_flow.md | Lecture document |
| C16 | Kanban GitHub Issues + backlog + imprévus | docs/project_management.md + GitHub Issues | https://github.com/brunely92/project-ai-ece/issues |
| C17 | App Streamlit 3 pages + sécurité | app/streamlit_app.py | `streamlit run app/streamlit_app.py` |
| C18 | Workflow CI déclenché à chaque push | .github/workflows/ci.yml | Push → GitHub Actions |
| C19 | Procédure release + tag | docs/release.md + docs/ci_cd.md | `git tag -a v1.0.0` |
| C20 | Logs structurés + métriques + seuils | src/monitoring/logger.py + docs/monitoring.md | Lecture logs/api.log |
| C21 | Incident simulé + diagnostic + correction + test | docs/incident_report.md | Lecture document |
