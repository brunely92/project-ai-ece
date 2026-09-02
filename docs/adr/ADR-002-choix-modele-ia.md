# ADR-002 — Choix des modèles IA : DistilBERT pré-entraîné + TF-IDF/LogReg custom

## Statut
Accepté — 2026-05 (Bloc 2), complété 2026-09 (modèle custom, Bloc 2 extension)

## Contexte

Le projet doit prédire le sentiment (positif/négatif) d'avis de films en anglais, avec une latence
raisonnable (< 2s), un coût nul, une exécution locale (RGPD, souveraineté) et une bonne précision
sur des cas ambigus (négations, phrases mitigées). Le benchmark initial (`docs/benchmark.md`) a
comparé 4 services : HuggingFace Transformers, TextBlob, VADER, API OpenAI. Une fois un corpus
propre de 188K avis multi-sources disponible (Bloc 1), la question s'est posée de savoir s'il valait
la peine d'entraîner un modèle spécifiquement sur ces données plutôt que de s'appuyer uniquement sur
un modèle pré-entraîné généraliste.

## Décision

Utiliser **deux modèles complémentaires**, exposés tous les deux via l'API (`/predict` et
`/predict/custom`) et comparés objectivement (`/predict/compare`, `/models/comparison`) :

1. **HuggingFace `distilbert-base-uncased-finetuned-sst-2-english`** — modèle Transformer
   pré-entraîné, utilisé tel quel (pas de fine-tuning), retenu par le benchmark C7 (score pondéré
   4.35/5, 91% accuracy sur SST-2).
2. **TF-IDF (max_features=50000, ngram_range=(1,3)) + LogisticRegression** — modèle custom entraîné
   sur les 188 190 avis labellisés du projet (`src/model/train_model.py`, split 80/20 stratifié,
   `random_state=42`).

## Conséquences

**Positives**
- Le modèle custom obtient une meilleure accuracy sur un échantillon de nos propres données
  (92.0% vs 87.7% pour DistilBERT sur 2000 avis, voir `reports/model_comparison.json`) : il a appris
  le vocabulaire et les tournures spécifiques du corpus (mélange IMDB/Amazon/Yelp/SST-2/Rotten Tomatoes).
- Latence du modèle custom quasi nulle (0.55 ms/avis vs 145 ms pour DistilBERT) : pas de réseau de
  neurones à faire tourner, juste un produit matriciel creux — pertinent pour du batch à grand volume.
- Conserver DistilBERT donne une baseline généraliste robuste, utile si le projet doit un jour
  traiter des avis hors du domaine d'entraînement (autres langues de corpus, autres types de texte).
- Les deux étant gratuits et 100% locaux, aucun compromis RGPD/coût n'est fait en gardant les deux.
- La comparaison objective (accuracy/precision/recall/F1/latence) documente un vrai choix argumenté
  plutôt qu'un choix arbitraire — utile en soutenance.

**Négatives**
- Deux modèles à maintenir, charger et tester (complexité et surface de test accrues :
  `tests/test_model_training.py`, `TestPredictCustom`).
- Le modèle custom est surspécialisé sur la distribution du corpus d'entraînement (essentiellement
  des avis de films anglophones de sources publiques 2010-2015) : sa généralisation à des avis très
  différents (autre registre de langue, autre domaine) n'est pas garantie et non testée.
- TF-IDF + LogReg ne capture pas le contexte séquentiel (contrairement à un Transformer) : plus
  vulnérable sur des négations complexes ou du sarcasme long (non mesuré ici faute de jeu de test dédié).
- Coût de ré-entraînement à chaque évolution significative du corpus (~5 min sur 188K lignes).

## Alternatives écartées

| Alternative | Raison de l'écart |
|---|---|
| **Fine-tuner DistilBERT sur nos données** | Nécessite GPU/temps de calcul significatif et une infrastructure d'entraînement (torch training loop, gestion de checkpoints) disproportionnés pour ce projet académique ; le gain potentiel n'a pas été jugé nécessaire face à un modèle TF-IDF/LogReg déjà performant et quasi instantané à entraîner. |
| **VADER / TextBlob comme modèle principal** | Écartés dès le benchmark C7 : lexique/règles, faible précision sur cas ambigus (`docs/benchmark.md` section tests comparatifs) — conservés uniquement comme référence de comparaison (`/predict/compare`, `textblob` dans `compare_models.py`). |
| **API OpenAI (GPT)** | Payant, dépendance réseau/cloud, transfert de données hors UE (RGPD) — écarté dès le benchmark initial. |
| **Modèle custom seul (sans DistilBERT)** | Perdrait la robustesse d'un modèle Transformer pré-entraîné sur des cas hors distribution, et priverait le projet d'une comparaison multi-approches pourtant pédagogiquement utile pour la certification. |

## Réversibilité

Les deux modèles sont interchangeables au niveau de l'API sans impact sur le reste de
l'architecture : `get_hf_model()` et `get_custom_model()` sont deux fonctions de chargement lazy
indépendantes dans `src/api/main.py`. Réentraîner ou remplacer l'un des deux n'affecte pas l'autre.
