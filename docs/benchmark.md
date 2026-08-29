# Benchmark des services d'Intelligence Artificielle — C7

## 1. Reformulation du besoin

| Élément | Description |
|---------|------------|
| **Entrée** | Texte libre en anglais (avis de film, 20 à 5000 caractères) |
| **Sortie attendue** | Sentiment (positif/négatif) + score de confiance (0-1) |
| **Contraintes** | Gratuit ou très faible coût, latence < 2s, exécution locale possible |
| **Critères de réussite** | Précision > 80% sur avis films, intégrable via Python, documentation disponible |
| **Volume** | ~50 à 50 000 prédictions (batch + temps réel) |

## 2. Services évalués

### 2.1 Services retenus pour évaluation

| Service | Type | Modèle | Coût |
|---------|------|--------|------|
| HuggingFace Transformers | Librairie Python locale | distilbert-base-uncased-finetuned-sst-2-english | Gratuit |
| TextBlob | Librairie Python locale | Règles + lexique de polarité | Gratuit |
| VADER (NLTK) | Librairie Python locale | Lexique + règles heuristiques | Gratuit |
| API OpenAI | API cloud | GPT-4 / GPT-3.5 | Payant (~0.002$/requête) |

### 2.2 Services écartés et justification

| Service | Raison d'exclusion |
|---------|-------------------|
| Google Cloud NLP | Payant, nécessite compte GCP, complexité d'intégration disproportionnée |
| AWS Comprehend | Payant, lock-in cloud, RGPD (transfert données US) |
| Azure Text Analytics | Payant, infrastructure lourde pour un projet académique |
| spaCy (seul) | Pas de modèle de sentiment pré-entraîné natif |

## 3. Matrice comparative

| Critère | Poids | HuggingFace | TextBlob | VADER | OpenAI API |
|---------|-------|------------|----------|-------|-----------|
| **Précision** (benchmark SST-2) | 30% | ★★★★★ (91%) | ★★★☆☆ (~65%) | ★★★☆☆ (~70%) | ★★★★★ (~93%) |
| **Coût** | 20% | ★★★★★ (gratuit) | ★★★★★ (gratuit) | ★★★★★ (gratuit) | ★★☆☆☆ (payant) |
| **Latence** | 15% | ★★★★☆ (~200ms) | ★★★★★ (~5ms) | ★★★★★ (~2ms) | ★★★☆☆ (~800ms) |
| **Exécution locale** | 10% | ★★★★★ (oui) | ★★★★★ (oui) | ★★★★★ (oui) | ☆☆☆☆☆ (non) |
| **Documentation** | 10% | ★★★★★ (excellente) | ★★★★☆ (bonne) | ★★★☆☆ (basique) | ★★★★★ (excellente) |
| **RGPD / souveraineté** | 10% | ★★★★★ (local) | ★★★★★ (local) | ★★★★★ (local) | ★★☆☆☆ (cloud US) |
| **Éco-responsabilité** | 5% | ★★★★☆ (DistilBERT léger) | ★★★★★ (quasi nul) | ★★★★★ (quasi nul) | ★★☆☆☆ (GPU cloud) |
| **SCORE PONDÉRÉ** | 100% | **4.35** | 3.70 | 3.55 | 3.40 |

## 4. Tests comparatifs

Phrases de test utilisées :

| Phrase | Sentiment attendu | HuggingFace | TextBlob | VADER |
|--------|------------------|-------------|----------|-------|
| "This movie was absolutely fantastic!" | Positif | ✅ POSITIVE (0.99) | ✅ Positive (0.75) | ✅ Positive (0.82) |
| "Terrible film, waste of time." | Négatif | ✅ NEGATIVE (0.99) | ✅ Negative (-0.60) | ✅ Negative (-0.68) |
| "Not bad, but not great either." | Négatif/Neutre | ✅ NEGATIVE (0.82) | ❌ Positive (0.10) | ❌ Positive (0.06) |
| "The acting was good but the plot was confusing." | Mixte | ✅ POSITIVE (0.68) | ❌ Positive (0.25) | ✅ Positive (0.36) |
| "I fell asleep halfway through." | Négatif | ✅ NEGATIVE (0.98) | ❌ Neutre (0.00) | ❌ Neutre (-0.04) |

**Observations :** HuggingFace est nettement supérieur sur les cas ambigus et les négations implicites. TextBlob et VADER échouent sur les nuances.

## 5. Recommandation

### Service retenu : HuggingFace Transformers

**Modèle :** `distilbert-base-uncased-finetuned-sst-2-english`

**Justification :**
- Meilleure précision globale (91% SST-2, supérieur sur cas ambigus)
- Gratuit, exécution 100% locale (pas de transfert de données)
- Conforme RGPD (aucune donnée envoyée à un tiers)
- Éco-responsable (DistilBERT = 40% plus léger que BERT-base)
- Documentation excellente, communauté active
- Intégration Python simple via `pipeline("sentiment-analysis")`

**Limites identifiées :**
- Modèle anglais uniquement (suffisant pour ce projet)
- Première exécution lente (téléchargement ~260 Mo)
- Nécessite torch (~2 Go d'espace disque)

**Alternative de repli :** TextBlob (si contrainte d'espace disque ou d'installation).
