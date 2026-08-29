# Procédure de livraison — C19

## Processus de release

### Étapes

1. Vérifier que tous les tests passent en local : `pytest tests/ -v`
2. Vérifier que la CI GitHub Actions est verte
3. Merger la branche `dev` dans `main` (si applicable)
4. Créer un tag de version : `git tag -a v1.0.0 -m "Release 1.0.0"`
5. Pousser le tag : `git push origin v1.0.0`
6. Créer une release GitHub depuis le tag

### Convention de versioning

Format : `vMAJEUR.MINEUR.PATCH` (SemVer)
- MAJEUR : changement incompatible
- MINEUR : nouvelle fonctionnalité rétrocompatible
- PATCH : correction de bug

### Prérequis pré-production

- [ ] Tous les tests passent (pytest)
- [ ] CI verte sur GitHub Actions
- [ ] README à jour
- [ ] .env.example à jour
- [ ] Pas de secrets dans le code
- [ ] Documentation à jour dans docs/

### Commandes de livraison

```bash
# Tag + release
git tag -a v1.0.0 -m "Release 1.0.0 — MVP analyse de sentiment"
git push origin v1.0.0

# Build (optionnel — packaging)
pip freeze > requirements-lock.txt
```
