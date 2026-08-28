# Modèle Conceptuel et Physique de Données — C4

## MCD (Modèle Conceptuel de Données)

```
┌──────────┐       ┌──────────────┐       ┌──────────────┐
│  SOURCE  │       │   REVIEW     │       │    FILM      │
├──────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)  │       │ id (PK)      │       │ id (PK)      │
│ name     │       │ review_text  │──────>│ tmdb_id      │
│ type     │       │ sentiment    │       │ title        │
│ url      │       │ source       │       │ release_date │
│ desc     │       │ film_id (FK) │       │ vote_average │
│ date     │       │ author       │       │ overview     │
└──────────┘       │ created_at   │       └──────────────┘
                   │ imported_at  │
                   └──────┬───────┘
                          │
                   ┌──────┴───────┐
                   │ PREDICTION   │
                   ├──────────────┤
                   │ id (PK)      │
                   │ review_id(FK)│
                   │ sentiment    │
                   │ score        │
                   │ model_version│
                   │ predicted_at │
                   └──────────────┘
```

## Relations

| Relation | Cardinalité | Description |
|----------|------------|-------------|
| FILM → REVIEW | 1:N | Un film peut avoir plusieurs avis |
| REVIEW → PREDICTION | 1:N | Un avis peut avoir plusieurs prédictions (versions modèle) |

## MPD (Modèle Physique)

SGBD : **SQLite**
Justification : projet local, pas de concurrent access, léger, inclus dans Python.

Fichier schéma : `src/sql/schema.sql`

## Choix techniques

- Clés primaires auto-incrémentées
- Clés étrangères avec contrainte FOREIGN KEY
- Contraintes CHECK sur les valeurs de sentiment
- Dates en format ISO 8601 (TEXT en SQLite)
