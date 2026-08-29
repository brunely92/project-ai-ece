# Veille technique et réglementaire — C6

## Planning de veille

| Semaine | Date | Durée | Thème |
|---------|------|-------|-------|
| 1 | 04/05/2026 | 1h | État de l'art NLP — modèles de sentiment analysis |
| 2 | 11/05/2026 | 1h | Frameworks Python pour le NLP (HuggingFace, spaCy, NLTK) |
| 3 | 18/05/2026 | 1h | Réglementation IA — AI Act européen et impact sur les projets NLP |
| 4 | 25/05/2026 | 1h | RGPD et traitement de texte — anonymisation, consentement |
| 5 | 01/06/2026 | 1h | Éco-responsabilité des modèles IA — empreinte carbone, optimisation |
| 6 | 08/06/2026 | 1h | Accessibilité des interfaces IA — WCAG, RG2AA |

## Sources qualifiées

| # | Source | Type | Auteur/Org | Fiabilité | Critère de fiabilité | Dernière consultation |
|---|--------|------|-----------|-----------|---------------------|----------------------|
| 1 | [HuggingFace Documentation](https://huggingface.co/docs) | Documentation officielle | HuggingFace Inc. | Haute | Éditeur du framework, mis à jour en continu | 05/2026 |
| 2 | [CNIL — Guide IA](https://www.cnil.fr/fr/intelligence-artificielle) | Guide réglementaire | CNIL (autorité publique) | Haute | Autorité nationale, source officielle RGPD | 05/2026 |
| 3 | [AI Act — Texte officiel](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) | Réglementation | Union Européenne | Haute | Journal officiel UE, texte juridique | 05/2026 |
| 4 | [Papers with Code — Sentiment Analysis](https://paperswithcode.com/task/sentiment-analysis) | Benchmark académique | Communauté ML | Moyenne-Haute | Agrégation de papiers peer-reviewed, classements reproductibles | 05/2026 |
| 5 | [FastAPI Documentation](https://fastapi.tiangolo.com/) | Documentation officielle | Sebastián Ramírez | Haute | Créateur du framework, exemples vérifiables | 05/2026 |
| 6 | [GreenIT.fr — Éco-conception](https://www.greenit.fr/) | Blog spécialisé | Collectif GreenIT | Moyenne | Expertise reconnue éco-conception numérique, sources citées | 05/2026 |
| 7 | [Référentiel RG2AA](https://accessibilite.numerique.gouv.fr/) | Référentiel officiel | DINUM (État français) | Haute | Source officielle accessibilité numérique France | 05/2026 |
| 8 | [MLOps Community](https://mlops.community/) | Blog/communauté | Communauté MLOps | Moyenne | Praticiens actifs, retours d'expérience variés | 06/2026 |

### Grille d'évaluation de la fiabilité

| Critère | Description |
|---------|------------|
| **Auteur identifié** | L'auteur ou l'organisation est clairement identifié et reconnu |
| **Date récente** | Contenu mis à jour dans les 12 derniers mois |
| **Convergence** | L'information est confirmée par au moins 2 autres sources |
| **Accessibilité** | Le contenu est disponible dans un format accessible |
| **Biais identifié** | Les biais potentiels (commercial, idéologique) sont identifiés |

## Synthèse de veille

### 1. Analyse de sentiment — État de l'art (mai 2026)

Les modèles Transformer pré-entraînés (BERT, DistilBERT, RoBERTa) dominent les benchmarks d'analyse de sentiment. Le modèle `distilbert-base-uncased-finetuned-sst-2-english` offre un excellent compromis entre performance (91% accuracy sur SST-2) et légèreté (66M paramètres vs 340M pour BERT-large).

**Tendances observées :**
- Modèles pré-entraînés via HuggingFace Hub : standard de l'industrie
- Fine-tuning sur données métier pour améliorer la performance
- Modèles multilingues (XLM-RoBERTa) pour le support international
- Quantification (INT8) pour réduire l'empreinte mémoire et carbone

**Impact sur le projet :** Choix du pipeline HuggingFace pré-entraîné — pas de fine-tuning nécessaire pour ce projet, performance suffisante, empreinte réduite.

### 2. Réglementation — AI Act et RGPD

L'AI Act (Règlement UE 2024/1689) classe les systèmes IA par niveau de risque. L'analyse de sentiment sur des avis publics de films est classée **risque minimal** (pas de prise de décision automatisée sur des personnes, pas de données biométriques).

**Obligations identifiées :**
- Transparence : informer l'utilisateur que le résultat provient d'une IA
- RGPD : les pseudonymes d'auteurs sont des données personnelles potentielles
- Pas d'obligation de conformité spécifique AI Act pour le risque minimal

**Impact sur le projet :** Mention "résultat généré par IA" dans l'interface Streamlit. Procédures RGPD documentées dans `docs/rgpd.md`.

### 3. Éco-responsabilité

Un modèle DistilBERT consomme environ 2x moins d'énergie que BERT-base pour une performance comparable (source : Sanh et al., 2019, "DistilBERT, a distilled version of BERT").

**Impact sur le projet :** Choix de DistilBERT plutôt que BERT-base ou BERT-large. Pas de fine-tuning (économie de GPU). Exécution locale sans appel cloud.

## Communication

La synthèse de veille est versionnée sur Git et accessible dans `docs/watch.md`. Format accessible : Markdown (convertible en HTML/PDF).
