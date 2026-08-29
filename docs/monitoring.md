# Monitoring — C11 / C20

## Métriques surveillées

### Modèle IA (C11)

| Métrique | Description | Seuil d'alerte | Source |
|----------|------------|---------------|--------|
| Latence prédiction | Temps de réponse /predict | > 1000 ms | Logs API |
| Score de confiance | Confiance du modèle | < 0.5 | Logs prédiction |
| Distribution sentiments | Ratio positif/négatif | Déséquilibre > 80/20 | Agrégation logs |
| Prédiction vide | Résultat absent | > 0 occurrence | Logs erreur |
| Erreur chargement modèle | Modèle indisponible | Toute erreur | Logs système |

### Application (C20)

| Métrique | Description | Seuil d'alerte | Source |
|----------|------------|---------------|--------|
| Disponibilité /health | API accessible | Status ≠ 200 | Healthcheck |
| Latence endpoints | Temps de réponse global | > 1000 ms | Logs API |
| Taux erreurs 5xx | Erreurs serveur | > 5% | Logs API |
| Usage endpoints | Requêtes par endpoint | Informatif | Logs API |

## Format des logs

```
timestamp | level | endpoint=X | status=200 | latency_ms=150.3 | details
```

Exemple :
```
2026-06-01T10:30:15 | INFO | endpoint=/predict | prediction=positive | score=0.9532 | latency_ms=180.5 | text_length=85
2026-06-01T10:30:18 | WARNING | ALERTE LATENCE | /predict | 1250ms > seuil 1000ms
```

## Journalisation et RGPD

- Les textes d'avis ne sont **jamais** enregistrés dans les logs
- Seule la longueur du texte est loguée (`text_length=85`)
- Pas de données personnelles dans les fichiers de log
- Logs stockés localement dans `logs/api.log`

## Outils

| Composant | Outil | Fichier |
|-----------|-------|---------|
| Logger structuré | Python logging | `src/monitoring/logger.py` |
| Logs fichier | FileHandler | `logs/api.log` |
| Alertes console | StreamHandler (WARNING+) | Console |
| Dashboard | Page Streamlit dédiée | `app/streamlit_app.py` |

## Alertes configurées

| Alerte | Condition | Action |
|--------|----------|--------|
| ALERTE LATENCE | latency_ms > 1000 | Log WARNING |
| ALERTE CONFIANCE | score < 0.5 | Log WARNING |
| ALERTE ERREUR | status >= 500 | Log ERROR |
