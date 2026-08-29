# Spécifications techniques — C15

## Architecture globale

```
┌─────────────────┐     HTTP     ┌─────────────────┐     Python    ┌──────────────┐
│                 │  ──────────> │                 │  ──────────> │              │
│   Streamlit     │              │    FastAPI       │              │  HuggingFace │
│   (Frontend)    │  <────────── │    (Backend)     │  <────────── │  (Modèle IA) │
│   Port 8501     │     JSON     │    Port 8000     │   Résultat   │              │
└─────────────────┘              └────────┬────────┘              └──────────────┘
                                          │
                                          │ SQL
                                          ▼
                                 ┌─────────────────┐
                                 │     SQLite       │
                                 │  (Base données)  │
                                 └─────────────────┘
```

## Architecture applicative : MVC

| Couche | Composant | Responsabilité |
|--------|-----------|---------------|
| **Vue** | Streamlit (`app/`) | Interface utilisateur, formulaires, affichage |
| **Contrôleur** | FastAPI (`src/api/`) | Routing, validation, auth, orchestration |
| **Modèle** | SQLite + HuggingFace | Données + intelligence artificielle |

## Flux de données

### Flux 1 : Prédiction temps réel
```
Utilisateur → [texte] → Streamlit → POST /predict → FastAPI → HuggingFace → [sentiment, score] → Streamlit → affichage
```

### Flux 2 : Consultation données
```
Utilisateur → Streamlit → GET /reviews → FastAPI → SQLite → [données] → Streamlit → affichage
```

### Flux 3 : Pipeline de données (batch)
```
Sources (CSV, API, scraping) → collect → clean → validate → import → SQLite
```

## Choix techniques justifiés

| Choix | Justification |
|-------|--------------|
| **Python 3.11** | Langage de l'équipe, écosystème IA mature, cohérence stack |
| **FastAPI** | Performance (async), documentation OpenAPI auto, validation Pydantic |
| **SQLite** | Léger, sans serveur, inclus Python, suffisant pour le volume |
| **Streamlit** | Prototypage rapide, Python natif, composants UI prêts |
| **HuggingFace** | Standard industrie NLP, modèles pré-entraînés, gratuit, local |
| **pytest** | Standard Python, fixtures, paramétrisation, intégration CI |
| **GitHub Actions** | CI/CD intégré au repo, gratuit, YAML simple |

## Dépendances externes

| Dépendance | Version | Rôle |
|-----------|---------|------|
| requests | ≥ 2.31 | Appels HTTP (collecte API) |
| beautifulsoup4 | ≥ 4.12 | Parsing HTML (scraping) |
| pandas | ≥ 2.1 | Manipulation données |
| fastapi | ≥ 0.110 | API REST |
| uvicorn | ≥ 0.27 | Serveur ASGI |
| transformers | ≥ 4.38 | Modèle NLP |
| torch | ≥ 2.2 | Backend deep learning |
| streamlit | ≥ 1.31 | Application web |
| python-dotenv | ≥ 1.0 | Variables d'environnement |
