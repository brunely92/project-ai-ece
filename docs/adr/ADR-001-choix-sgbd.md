# ADR-001 — Choix du SGBD : SQLite plutôt que PostgreSQL

## Statut
Accepté — 2026-05 (Bloc 1)

## Contexte

Le projet doit stocker ~230K avis bruts (188K après nettoyage), ~200 films enrichis (TMDB/OMDB)
et les prédictions du modèle IA, avec des relations simples (film 1:N avis, avis 1:N prédictions).
L'application tourne en local/mono-poste pour un projet de certification : pas de serveur de
production, pas d'accès concurrent multi-utilisateurs, pas d'infrastructure à administrer.

## Décision

Utiliser **SQLite** comme unique SGBD, via le module standard `sqlite3` de Python, avec un schéma
normalisé 3NF (`src/sql/schema.sql` : genres, sources, films, reviews, predictions, data_lineage,
vues croisées).

## Conséquences

**Positives**
- Aucune installation ni administration de serveur de base de données (fichier unique `data/movies_reviews.sqlite`).
- Zéro dépendance supplémentaire : `sqlite3` est dans la stdlib Python.
- Reproductibilité maximale pour la soutenance : `git clone` + `pip install` + scripts suffisent, pas
  de service externe à démarrer.
- Performances largement suffisantes pour ~200K lignes en lecture/écriture mono-utilisateur (index
  sur `sentiment`, `source`, `film_id`, `confidence_score`, cf. schema.sql).
- Sauvegarde/versionnage triviaux (copie de fichier).

**Négatives**
- Pas d'accès concurrent en écriture performant (verrouillage fichier) : inadapté à une montée en
  charge multi-utilisateurs ou multi-instances.
- Pas de types stricts avancés (JSON natif, tableaux) ni de réplication/haute disponibilité.
- Migration nécessaire si le projet évolue vers une mise en production multi-utilisateurs réelle.

## Alternatives écartées

| Alternative | Raison de l'écart |
|---|---|
| **PostgreSQL** | Nécessite un serveur à installer/administrer (Docker ou service), complexité disproportionnée pour un usage mono-poste académique ; aucun besoin identifié de concurrence, JSONB ou extensions avancées (full-text search géré différemment ici). |
| **MySQL/MariaDB** | Mêmes inconvénients que PostgreSQL (serveur à administrer) sans bénéfice supplémentaire pour ce volume/usage. |
| **MongoDB (NoSQL)** | Le modèle de données est relationnel par nature (film → avis → prédictions, genres N:N) ; un schéma normalisé SQL est plus adapté et plus simple à interroger (SQL standard, `src/sql/queries.sql`). |
| **Fichiers plats (CSV/Parquet) sans BDD** | Perd les contraintes d'intégrité (FOREIGN KEY, CHECK), les index, les jointures et vues SQL déjà utilisées par l'API et les dashboards Streamlit. |

## Réversibilité

Si une mise en production multi-utilisateurs devenait nécessaire, la migration vers PostgreSQL est
mécanique : le schéma est déjà en 3NF avec types SQL standards, et le code d'accès passe uniquement
par des requêtes SQL portables (`src/api/main.py`, `src/db/*.py`) — pas de fonctions spécifiques à
SQLite utilisées en dehors de `datetime('now')`.
