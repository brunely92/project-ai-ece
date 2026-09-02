# Rapport d'incident technique — C21

> Incident réel traité via un vrai flux Git (branche → test rouge → correction → test vert → merge),
> pas une simulation documentée a posteriori.

## Identification

| Champ | Valeur |
|-------|--------|
| **Date** | 2026-09-02 |
| **Sévérité** | Haute (endpoint de prédiction inutilisable sur une classe d'entrées valides) |
| **Composant** | API FastAPI — endpoint `POST /predict` |
| **Branche** | `fix/incident-encoding` |
| **Signalement** | Test automatisé rouge (`test_predict_with_emojis`) reproduisant le crash |

## Symptôme

`POST /predict` retourne une erreur 500 (Internal Server Error) au lieu d'une prédiction lorsque le
texte de l'avis contient des emojis ou certains caractères Unicode dans les plages `U+1F300` et
au-delà (émojis, pictogrammes récents).

Exemple de requête provoquant l'erreur :
```json
POST /predict
{"text": "This movie is great 🎬👍"}
```

Réponse avant correction :
```json
{"detail": "Internal Server Error"}  // 500
```

## Diagnostic

### Reproduction (test automatisé, avant correction)
```python
def test_predict_with_emojis(self):
    r = client.post("/predict", json={"text": "This movie is great 🎬👍"}, headers=HEADERS)
    assert r.status_code == 500  # rouge : reproduit le bug
```

Commit de reproduction : `test(api): reproduit l'incident - les emojis provoquent un crash 500 sur /predict`

### Reproduction en local (curl, une fois l'API lancée)
```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "This movie is great 🎬👍"}'
```

### Cause identifiée
Le texte brut (avec emojis) était transmis directement au pipeline HuggingFace sans nettoyage
préalable. Certains caractères Unicode dans les plages d'émojis provoquent une exception non gérée
dans la chaîne de traitement, remontée telle quelle par FastAPI en erreur 500 au lieu d'être filtrée
ou gérée proprement.

## Correction

### Code modifié (`src/api/main.py`)

Ajout d'une fonction `strip_emojis()` (regex sur les plages Unicode d'émojis/pictogrammes/drapeaux)
appliquée au texte avant l'appel au modèle :

```python
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symboles/pictogrammes divers, émojis récents
    "\U00002600-\U000027BF"  # symboles divers, dingbats
    "\U0001F1E6-\U0001F1FF"  # drapeaux (indicateurs régionaux)
    "\U0001F000-\U0001F0FF"  # tuiles mahjong/cartes
    "\U0000FE0F"             # variation selector (rendu emoji)
    "]+",
    flags=re.UNICODE,
)

def strip_emojis(text: str) -> str:
    cleaned = EMOJI_PATTERN.sub("", text).strip()
    return cleaned if cleaned else text
```

```python
@app.post("/predict", ...)
def predict_sentiment(request: PredictRequest):
    ...
    model = get_hf_model()
    clean_text = strip_emojis(request.text)
    result = model(clean_text[:512])[0]
    ...
```

### Commit de correction
```
fix(api): handle unicode/emoji in /predict
```

## Test de non-régression

Le même test (`test_predict_with_emojis`) est mis à jour pour vérifier le comportement corrigé :

```python
def test_predict_with_emojis(self):
    """Non-régression (incident fix/incident-encoding) : /predict ne doit plus
    crasher (500) sur des textes contenant des emojis."""
    r = client.post("/predict", json={"text": "This movie is great 🎬👍"}, headers=HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["sentiment"] in ("positive", "negative")
```

## Résolution

| Étape | Action | Statut |
|-------|--------|--------|
| 1 | Création de la branche `fix/incident-encoding` | ✅ |
| 2 | Reproduction du bug (code + test rouge attendant 500) | ✅ |
| 3 | Diagnostic (emojis non filtrés avant l'appel au modèle) | ✅ |
| 4 | Correction (`strip_emojis()` appliqué avant la prédiction) | ✅ |
| 5 | Test de non-régression mis à jour (attend 200) | ✅ |
| 6 | Suite complète (59 tests) verte sur la branche | ✅ |
| 7 | Merge dans `main` (`fix(api): handle unicode/emoji in /predict`) | ✅ |

## Leçons apprises

- Toujours nettoyer/normaliser les entrées texte avant de les transmettre à un modèle NLP tiers,
  même quand la validation de type (Pydantic) est déjà en place — un `str` valide peut encore
  contenir des caractères qui font planter la chaîne de traitement en aval.
- Un test qui reproduit fidèlement le bug (rouge) avant la correction donne une garantie plus forte
  qu'un test écrit uniquement après coup.
- `TestClient(app, raise_server_exceptions=False)` est nécessaire pour observer le vrai code HTTP
  500 en test — par défaut, Starlette relève l'exception dans le process de test au lieu de la
  convertir en réponse, ce qui masquerait ce type d'incident dans la suite de tests.
