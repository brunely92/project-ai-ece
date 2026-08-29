# Intégration et Livraison Continue — C18 / C19

## Pipeline CI

**Outil :** GitHub Actions
**Fichier :** `.github/workflows/ci.yml`
**Déclencheurs :** push sur `main` et `dev`, pull requests vers `main`

### Étapes du pipeline

```
checkout → setup python 3.11 → pip install → generate dataset → clean → import → pytest
```

### Résultat attendu

Tous les tests passent automatiquement à chaque push. Badge CI visible sur le README.

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
