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
| Latence prédiction | > 1000 ms | Logs structurés |
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

## Service custom : TF-IDF + Régression Logistique

Cette section documente le second service d'intelligence artificielle du projet : le modèle entraîné sur le corpus SentimentFlick. Elle complète la section DistilBERT ci-dessus.

### Rôle du service

Le service reçoit un avis de film en anglais et renvoie un sentiment (positif ou négatif) accompagné d'un score de confiance compris entre 0 et 1. Il est exposé par l'endpoint `POST /predict/custom` de l'API.

### Paramétrage retenu et justification

| Paramètre | Valeur | Justification |
|-----------|--------|---------------|
| `ngram_range` | (1, 3) | Le modèle lit les mots seuls, les paires et les triplets. Les négations comme « not very good » deviennent une unité de sens. Sur IMDB (50 000 avis), les unigrammes seuls classent « not very good » comme positif ; avec (1, 3), il est classé négatif. |
| `max_features` | 50 000 | Sans plafond, les trigrammes produisent 5 015 764 n-grammes sur IMDB. Garder les 50 000 plus fréquents (environ 1 %) supprime le bruit des expressions rares. Au-delà, le gain est marginal (+0,33 point à 100 000) alors que la taille du modèle double. |
| Algorithme | `LogisticRegression` | Adaptée aux vecteurs TF-IDF creux, rapide à entraîner (12 s sur 150 552 avis), interprétable (un coefficient par n-gramme). |
| `max_iter` | 1 000 | Plafond de sécurité. Sur IMDB, la convergence est atteinte en 11 itérations. |
| Découpage | 80/20 stratifié, `random_state=42` | Même proportion positif/négatif en entraînement et en test. Résultats reproductibles. |

Expérience de contrôle reproductible : `python -m src.model.tune_tfidf`. Résultats dans `reports/tfidf_tuning.json`.

### Accès au service

- Le service n'est jamais appelé directement : il passe par l'API FastAPI.
- Chaque requête doit contenir l'en-tête `x-api-key`. Sans clé valide, l'API répond `401 Clé API invalide ou manquante`.
- La clé est lue dans la variable d'environnement `API_SECRET_KEY`, stockée dans `.env`. Ce fichier n'est jamais versionné. Seul `.env.example` l'est.

### Installation

1. Installer les dépendances : `pip install -r requirements.txt` (scikit-learn 1.4 ou plus, joblib).
2. Construire la base : `python -m src.db.import_data`.
3. Entraîner le service : `python -m src.model.train_model`.
4. Lancer l'API : `uvicorn src.api.main:app --reload`.

L'entraînement produit deux fichiers dans `models/` : `tfidf_vectorizer.joblib` (vocabulaire et poids IDF) et `tfidf_logreg.joblib` (50 000 coefficients). Les métriques sont écrites dans `reports/model_evaluation.json`.

### Test

- Tests automatisés : `python -m pytest tests/test_model_training.py -v`. Ils vérifient la présence des fichiers du modèle et une accuracy supérieure à 80 %.
- Test manuel : dans Swagger (`/docs`), appeler `POST /predict/custom` avec la clé et le corps `{"text": "This movie was absolutely brilliant"}`. La réponse attendue contient `"model": "tfidf_logreg_custom"`.

### Dépendances et interconnexions

| Élément | Rôle |
|---------|------|
| Base SQLite `data/movies_reviews.sqlite` | Source des 188 190 avis labellisés utilisés pour l'entraînement |
| scikit-learn, joblib | Entraînement, sauvegarde et chargement du modèle |
| API FastAPI | Point d'accès unique, authentification, validation des entrées |
| Middleware de monitoring | Journalise chaque appel au service (statut, latence) |

### Données impliquées

- Entraînement : 188 190 avis publics en anglais (texte et label), découpés en 150 552 pour l'entraînement et 37 638 pour le test.
- Utilisation : un texte saisi par l'utilisateur (5 à 5 000 caractères). Le texte n'est pas conservé dans les journaux, seule sa longueur l'est.
- Sortie : un sentiment et un score de confiance.

### Monitorage

| Mesure | Seuil | Où la consulter |
|--------|-------|-----------------|
| Latence d'un appel | Alerte au-delà de 1 000 ms | `logs/api.log`, `GET /monitoring/alerts` |
| Refus d'accès | Chaque 401 est journalisé | `logs/api.log`, `GET /monitoring/logs` |
| Qualité du modèle | Accuracy, matrice de confusion | `GET /monitoring/metrics`, `GET /models/comparison` |

### Résultats mesurés

Sur les 37 638 avis de test : accuracy 90,7 %, précision 90,6 %, rappel 90,8 %, F1 90,7 %.

### Limites connues

- Anglais uniquement.
- Négation encore fragile : « not bad at all » est classé négatif, car le mot « bad » pèse plus que le trigramme.
- Un mot absent du vocabulaire appris est ignoré.

### Accessibilité de cette documentation

Cette documentation suit les recommandations de l'association Valentin Haüy et du guide AcceDe d'Atalan :

- titres hiérarchisés (niveaux 2 et 3) pour la navigation au lecteur d'écran ;
- tableaux simples avec une ligne d'en-tête ;
- aucune information transmise par la seule couleur ;
- phrases courtes et termes techniques expliqués ;
- format texte (Markdown) lisible sans outil propriétaire, exportable en PDF balisé.
