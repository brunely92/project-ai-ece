# Dictionnaire de données

## Table `reviews`

| Colonne | Type | Description | Nullable |
|---------|------|------------|----------|
| id | INTEGER | Identifiant unique auto-incrémenté | Non |
| review_text | TEXT | Texte de l'avis | Non |
| sentiment | TEXT | Label : positive / negative | Oui |
| source | TEXT | Origine : csv, api, scraping | Non |
| film_id | INTEGER | Clé étrangère vers films | Oui |
| author | TEXT | Auteur de l'avis | Oui |
| created_at | TEXT | Date de l'avis | Oui |
| imported_at | TEXT | Date d'import en base | Non |

## Table `films`

| Colonne | Type | Description | Nullable |
|---------|------|------------|----------|
| id | INTEGER | Identifiant unique | Non |
| tmdb_id | INTEGER | ID TMDB unique | Oui |
| title | TEXT | Titre du film | Non |
| release_date | TEXT | Date de sortie | Oui |
| vote_average | REAL | Note moyenne TMDB | Oui |
| vote_count | INTEGER | Nombre de votes | Oui |
| overview | TEXT | Synopsis | Oui |

## Table `predictions`

| Colonne | Type | Description | Nullable |
|---------|------|------------|----------|
| id | INTEGER | Identifiant unique | Non |
| review_id | INTEGER | FK vers reviews | Non |
| predicted_sentiment | TEXT | Sentiment prédit | Non |
| confidence_score | REAL | Score de confiance 0-1 | Non |
| model_version | TEXT | Version du modèle utilisé | Non |
| predicted_at | TEXT | Date de la prédiction | Non |
