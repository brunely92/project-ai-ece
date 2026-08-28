# Registre des traitements RGPD — C4

## Identification du traitement

| Champ | Valeur |
|-------|--------|
| **Responsable** | Étudiant ECE (projet académique) |
| **Finalité** | Analyse de sentiment d'avis de films pour certification RNCP |
| **Base légale** | Intérêt légitime (projet académique, données publiques) |
| **Durée conservation** | Durée du projet + 6 mois après soutenance |

## Données traitées

| Donnée | Catégorie | Donnée personnelle ? | Traitement |
|--------|-----------|---------------------|------------|
| Texte d'avis | Contenu | Non (avis publics anonymes) | Stockage, analyse NLP |
| Pseudonyme auteur | Identifiant | Potentiellement (pseudonyme) | Stockage, pas d'exploitation |
| Métadonnées film | Référence | Non | Stockage, affichage |
| Prédiction IA | Résultat | Non | Stockage, affichage |

## Données personnelles identifiées

- **Pseudonymes** : les avis peuvent contenir des pseudonymes d'auteurs.
  - Mesure : pas d'exploitation des pseudonymes dans le modèle IA.
  - Procédure : possibilité d'anonymisation (remplacement par ID générique).

## Procédures de conformité

### Droit d'accès
Les données étant publiques (Kaggle, TMDB), le droit d'accès est garanti par les sources originales.

### Droit de suppression
Procédure : suppression en base via requête SQL.
```sql
DELETE FROM reviews WHERE author = 'nom_a_supprimer';
DELETE FROM predictions WHERE review_id NOT IN (SELECT id FROM reviews);
```

### Tri et suppression périodique
- Fréquence : à la fin du projet
- Action : suppression complète de la base SQLite
- Commande : `rm data/movies_reviews.sqlite`

## Sécurité des données

- Base SQLite locale (pas d'accès réseau)
- Pas de données sensibles dans les logs
- Secrets (clés API) dans `.env` exclus de Git
- Accès API protégé par clé d'authentification

## Références

- [CNIL — RGPD](https://www.cnil.fr/fr/rgpd-de-quoi-parle-t-on)
- [Règlement (UE) 2016/679](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
