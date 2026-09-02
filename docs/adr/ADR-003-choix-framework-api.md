# ADR-003 — Choix du framework API : FastAPI plutôt que Flask/Django

## Statut
Accepté — 2026-05 (Bloc 1)

## Contexte

Le projet expose une API REST (données + prédictions IA + monitoring, aujourd'hui 17 endpoints)
consommée par une application Streamlit et testable via Swagger pour la soutenance. Les besoins
identifiés : validation stricte des entrées (types, longueurs, bornes), documentation interactive
auto-générée, authentification simple par clé API, et une base de code lisible pour un projet
académique maintenu par une seule personne.

## Décision

Utiliser **FastAPI** (+ Uvicorn comme serveur ASGI) pour l'ensemble de l'API REST.

## Conséquences

**Positives**
- Validation automatique des requêtes via Pydantic (`PredictRequest`, `BatchPredictRequest`,
  `Query(..., ge=1, le=100)`, etc.) : les erreurs de saisie (texte trop court, limite hors bornes)
  sont rejetées en 422 sans code de validation manuel à écrire.
- Documentation interactive gratuite et toujours à jour : `/docs` (Swagger UI) et `/redoc`, générés
  automatiquement depuis les types Python et les docstrings — précieux pour la démonstration en
  soutenance sans outil tiers (Postman collections, etc.) à maintenir.
- Performances async natives (utile pour le futur si les appels au modèle IA ou à des API externes
  devaient être parallélisés), bien qu'actuellement peu exploitées (endpoints synchrones).
- Écosystème moderne et actif, typage Python natif qui réduit les bugs de contrat d'API.
- Middleware simple à brancher (`BaseHTTPMiddleware`) pour le monitoring (`src/api/middleware.py`).

**Négatives**
- Framework plus jeune que Flask/Django : moins de ressources historiques, quelques breaking changes
  entre versions majeures (mitigé ici par l'épinglage `fastapi>=0.110.0` dans `requirements.txt`).
- Pas d'ORM ni d'admin intégrés (contrairement à Django) : l'accès SQLite se fait en SQL brut
  (`sqlite3`), ce qui est un choix assumé (cf. ADR-001) mais demanderait plus de discipline sur un
  projet plus gros avec plusieurs contributeurs.
- Async mal utilisé peut introduire des blocages (le chargement du modèle HuggingFace est
  synchrone et bloquant dans les endpoints actuels) — acceptable ici vu le volume de requêtes visé
  (usage local/démonstration, pas de charge production).

## Alternatives écartées

| Alternative | Raison de l'écart |
|---|---|
| **Flask** | Pas de validation de schéma ni de documentation OpenAPI intégrées : nécessiterait des librairies additionnelles (Marshmallow/Flask-RESTX, flasgger) pour retrouver ce que FastAPI offre nativement — plus de code à écrire et maintenir pour un résultat équivalent. |
| **Django (+ Django REST Framework)** | Framework "batteries incluses" (ORM, admin, auth complexe) disproportionné pour une API à 17 endpoints sans besoin d'interface d'administration ni de gestion multi-app ; courbe d'apprentissage et boilerplate plus lourds pour un projet solo. |
| **Flask + Flask-RESTX** | Retenu un temps en pré-étude, mais la documentation Swagger générée est moins fidèle aux types Python réels (pas de Pydantic) et la validation reste plus manuelle. |

## Réversibilité

Le code métier (accès SQLite, appels aux modèles IA) est découplé des routes FastAPI dans des
fonctions autonomes (`get_db()`, `get_hf_model()`, `get_custom_model()`) : une migration vers un
autre framework REST ne nécessiterait de ré-écrire que la couche routing/validation, pas la logique
métier elle-même.
