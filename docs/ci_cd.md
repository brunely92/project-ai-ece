# Intégration et Livraison Continue — C18 / C19

## Pipeline CI

**Outil :** GitHub Actions
**Fichier :** `.github/workflows/ci.yml`
**Déclencheurs :** push sur `main` et `dev`, pull requests vers `main`

### Étapes du pipeline

```
checkout → setup python 3.11 → pip install (requirements-ci.txt) → generate dataset → clean → import → pytest
```

### Pourquoi un dataset léger en CI ?

La CI installe `requirements-ci.txt` (sans `torch`/`transformers`, trop lourds et lents à installer sur
un runner GitHub Actions) et génère un petit dataset de démonstration via
`python -m src.collect.download_dataset` (50 avis), au lieu du pipeline complet 7 sources / 188K lignes
utilisé en local pour la version livrée (voir `docs/final_evidence_map.md` C1 et `docs/cleaning_rules.md`).
Les tests qui appellent réellement le modèle HuggingFace (`/predict`, `/predict/batch`, `/predict/compare`,
`/predict/explain`) détectent l'absence de `torch`/`transformers` et sont automatiquement skippés
(`requires_model` dans `tests/test_api.py`) — la CI reste donc rapide tout en validant les 35 autres tests.

### Résultat attendu

Tous les tests non skippés passent automatiquement à chaque push. Badge CI visible sur le README.

## Workflow détaillé

```yaml
on:
  push: [main, dev]
  pull_request: [main]

jobs:
  test:
    - checkout
    - setup python 3.11
    - pip install requirements.txt
    - generate demo dataset
    - clean dataset
    - import to database
    - pytest tests/ -v
```

## Convention de branches

| Branche | Rôle |
|---------|------|
| `main` | Version stable, protégée |
| `dev` | Intégration, tests |
| `feature/*` | Développement de fonctionnalités |
| `docs/*` | Modifications documentation |
| `fix/*` | Corrections de bugs |
