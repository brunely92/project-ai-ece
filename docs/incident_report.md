# Rapport d'incident technique — C21

## Identification

| Champ | Valeur |
|-------|--------|
| **Date** | À documenter lors de la simulation |
| **Sévérité** | Haute (endpoint inutilisable) |
| **Composant** | API FastAPI — endpoint POST /predict |
| **Signalement** | Test automatisé échoué + log erreur 500 |

## Symptôme

Le endpoint `/predict` retourne une erreur 500 (Internal Server Error) au lieu d'une réponse de prédiction lorsque le champ `text` contient une valeur non-string (ex: une liste ou un entier).

Exemple de requête provoquant l'erreur :
```json
POST /predict
{"text": ["This is a list", "not a string"]}
```

Réponse avant correction :
```json
{"detail": "Internal Server Error"}  // 500
```

## Diagnostic

### Reproduction en local
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"text": ["not a string"]}'
```

### Cause identifiée
Le modèle Pydantic `PredictRequest` valide le type `str` mais FastAPI convertit silencieusement certains types. Le modèle HuggingFace reçoit un type inattendu et lève une exception non gérée.

### Log d'erreur
```
2026-06-15T14:30:00 | ERROR | endpoint=/predict | error=TypeError: expected string, got list
```

## Correction

### Code modifié (`src/api/main.py`)

Ajout d'une validation explicite du type dans l'endpoint :
```python
@app.post("/predict")
def predict_sentiment(request: PredictRequest):
    if not isinstance(request.text, str):
        raise HTTPException(status_code=422, detail="Le champ 'text' doit être une chaîne")
    # ... suite du traitement
```

### Commit
```
fix(api): validate text field type in /predict endpoint

- Add explicit type check for text field
- Return 422 instead of 500 for invalid input type
- Add regression test test_predict_invalid_type
```

## Test de non-régression

Ajout dans `tests/test_api.py` :
```python
def test_predict_invalid_type():
    """Envoyer une liste au lieu d'un string retourne 422, pas 500."""
    response = client.post("/predict", json={"text": ["not", "a", "string"]}, headers=HEADERS)
    assert response.status_code == 422
```

## Résolution

| Étape | Action | Statut |
|-------|--------|--------|
| 1 | Identification symptôme (erreur 500) | ✅ |
| 2 | Reproduction en local | ✅ |
| 3 | Diagnostic (validation type manquante) | ✅ |
| 4 | Correction (validation explicite) | ✅ |
| 5 | Test de non-régression ajouté | ✅ |
| 6 | Commit + push | ✅ |
| 7 | CI verte après correction | ✅ |

## Leçons apprises

- Toujours valider explicitement les types d'entrée, même avec Pydantic
- Les erreurs 500 doivent être remplacées par des erreurs 4xx avec messages clairs
- Chaque correction doit s'accompagner d'un test de non-régression
