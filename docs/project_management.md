# Gestion de projet agile — C16

## Méthode

**Kanban simplifié** avec 3 colonnes : To Do → In Progress → Done.

## Outil

GitHub Issues + GitHub Projects (Kanban board intégré au repository).
URL : https://github.com/brunely92/project-ai-ece/issues

## Backlog priorisé

| Priorité | Issue | Bloc | Statut |
|----------|-------|------|--------|
| 🔴 Haute | #1 Collecte multi-sources C1 | Bloc 1 | Done |
| 🔴 Haute | #3 Nettoyage dataset C3 | Bloc 1 | Done |
| 🟡 Moyenne | #2 Requêtes SQL C2 | Bloc 1 | Done |
| 🟡 Moyenne | #4 Base de données C4 | Bloc 1 | Done |
| 🟡 Moyenne | #5 API REST C5 | Bloc 1 | Done |
| 🟡 Moyenne | #6 Veille + benchmark C6-C8 | Bloc 2 | Done |
| 🔴 Haute | #7 API modèle + app C9-C10 | Bloc 2 | Done |
| 🟡 Moyenne | #8 Monitoring + tests + CI C11-C13 | Bloc 2 | Done |
| 🟡 Moyenne | #9 Besoin + architecture C14-C17 | Bloc 3 | Done |
| 🟡 Moyenne | #10 CI/CD app C18-C19 | Bloc 3 | Done |
| 🔴 Haute | #11 Monitoring + incident C20-C21 | Bloc 3 | Done |
| 🔴 Haute | #12 Soutenance | Transversal | To Do |

## Rituels

| Rituel | Fréquence | Description |
|--------|-----------|-------------|
| Point d'avancement | Chaque séance coaching | Revue des issues terminées / en cours / bloquées |
| Rétrospective | Fin de bloc | Ce qui a marché / à améliorer / actions |

## Gestion des imprévus

| Imprévu | Impact | Action |
|---------|--------|--------|
| CSV IMDB trop volumineux pour GitHub (64 Mo > 25 Mo) | Bloquant | Création d'un script `download_dataset.py` générant un dataset de démo |
| Site de scraping inaccessible | Mineur | Utilisation de quotes.toscrape.com (site prévu pour le scraping) |
| Modèle HuggingFace lent au premier chargement | Mineur | Chargement lazy (singleton) dans l'API |
