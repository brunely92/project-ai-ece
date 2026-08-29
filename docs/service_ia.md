# Paramétrage du service d'Intelligence Artificielle — C8

## Service retenu

| Élément | Valeur |
|---------|--------|
| **Librairie** | HuggingFace Transformers |
| **Modèle** | distilbert-base-uncased-finetuned-sst-2-english |
| **Tâche** | sentiment-analysis |
| **Version** | transformers >= 4.38.0 |
| **Backend** | PyTorch >= 2.2.0 |

## Installation

```bash
# Depuis le fichier requirements.txt
pip install transformers torch

# Ou manuellement
pip install transformers==4.44.0 torch==2.4.0
```

## Configuration

### Variables d'environnement (.env.example)

```env
# Nom du modèle HuggingFace
MODEL_NAME=distilbert-base-uncased-finetuned-sst-2-english

# Seuil de confiance minimal pour valider une prédiction
PREDICTION_THRESHOLD=0.5
```

> ⚠️ Le fichier `.env` contenant les vraies valeurs n'est **jamais versionné** (exclus via `.gitignore`).
> Seul `.env.example` est versionné comme template.

### Paramètres du modèle

| Paramètre | Valeur | Justification |
|-----------|--------|--------------|
| `model` | distilbert-base-uncased-finetuned-sst-2-english | Meilleur score au benchmark (voir benchmark.md) |
| `max_length` | 512 tokens | Limite du modèle, textes tronqués au-delà |
| `truncation` | True | Évite les erreurs sur les textes longs |
| `top_k` | 1 | Un seul résultat (sentiment dominant) |

## Test fonctionnel

### Script de test : `scripts/test_ai_service.py`

```python
from transformers import pipeline

# Charger le modèle
classifier = pipeline("sentiment-analysis",
                       model="distilbert-base-uncased-finetuned-sst-2-english")

# Phrases de test
tests = [
    "This movie was absolutely fantastic!",
    "Terrible film, waste of time.",
    "Not bad, but not great either.",
]

for text in tests:
    result = classifier(text)[0]
    print(f"{result['label']:10s} ({result['score']:.4f}) | {text}")
```

### Résultat attendu

```
POSITIVE   (0.9999) | This movie was absolutely fantastic!
NEGATIVE   (0.9998) | Terrible film, waste of time.
NEGATIVE   (0.8224) | Not bad, but not great either.
```

## Monitoring du service

| Métrique | Seuil d'alerte | Outil |
|----------|---------------|-------|
| Latence prédiction | > 2000 ms | Logs structurés |
| Erreur de chargement modèle | Toute erreur | Log + HTTP 500 |
| Score de confiance | < 0.5 | Log warning |
| Prédiction vide | Toute occurrence | Log erreur |

## Limites

- Modèle anglais uniquement
- Tronquage à 512 tokens (avis très longs partiellement analysés)
- Première exécution : téléchargement modèle (~260 Mo)
- Pas de détection de sentiment neutre (binaire : positive/negative)

## Reproductibilité

Le service est entièrement reproductible :
1. `pip install -r requirements.txt`
2. Copier `.env.example` → `.env`
3. Le modèle se télécharge automatiquement au premier appel
4. Aucune configuration serveur externe nécessaire
