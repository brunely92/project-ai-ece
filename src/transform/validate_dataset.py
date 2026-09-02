"""
C3 — Validation qualité du dataset nettoyé
Contrôles : colonnes, types, nulls, doublons, longueurs, distribution.
"""
import sys
from pathlib import Path
import pandas as pd

PROCESSED_FILE = Path("data/processed/reviews_clean.csv")


def validate():
    """Exécute tous les contrôles qualité sur le dataset nettoyé."""
    if not PROCESSED_FILE.exists():
        print(f"[ERREUR] Fichier introuvable : {PROCESSED_FILE}")
        print("         Lancez d'abord : python -m src.transform.clean_dataset")
        sys.exit(1)

    df = pd.read_csv(PROCESSED_FILE)
    errors = []

    print("=" * 60)
    print("VALIDATION QUALITÉ DU DATASET")
    print("=" * 60)

    # 1. Colonnes attendues
    expected_cols = {"id", "review_text", "sentiment", "source"}
    actual_cols = set(df.columns)
    if not expected_cols.issubset(actual_cols):
        missing = expected_cols - actual_cols
        errors.append(f"Colonnes manquantes : {missing}")
    print(f"[{'OK' if not errors else 'KO'}] Colonnes : {list(df.columns)}")

    # 2. Pas de doublons sur review_text
    dupes = df["review_text"].duplicated().sum()
    if dupes > 0:
        errors.append(f"{dupes} doublons trouvés")
    print(f"[{'OK' if dupes == 0 else 'KO'}] Doublons : {dupes}")

    # 3. Pas de review_text null ou vide
    nulls = df["review_text"].isna().sum()
    empties = (df["review_text"].str.strip() == "").sum()
    if nulls + empties > 0:
        errors.append(f"{nulls} nulls + {empties} vides")
    print(f"[OK] Nulls texte : {nulls} | Vides : {empties}")

    # 4. Longueur minimale
    too_short = (df["review_text"].str.len() < 20).sum()
    if too_short > 0:
        errors.append(f"{too_short} avis < 20 caractères")
    print(f"[{'OK' if too_short == 0 else 'KO'}] Avis trop courts (< 20 car) : {too_short}")

    # 5. Sentiments valides
    valid = {"positive", "negative"}
    labeled = df[df["sentiment"].notna()]
    invalid = labeled[~labeled["sentiment"].isin(valid)]
    if len(invalid) > 0:
        errors.append(f"{len(invalid)} sentiments invalides")
    print(f"[OK] Sentiments valides : {len(labeled)} labellisés sur {len(df)} total")

    # 6. Distribution
    print("\n--- Distribution ---")
    print(f"  Par source : {df['source'].value_counts().to_dict()}")
    if len(labeled) > 0:
        print(f"  Par sentiment : {labeled['sentiment'].value_counts().to_dict()}")
    print(f"  Longueur moyenne : {df['review_text'].str.len().mean():.0f} caractères")
    print(f"  Longueur min/max : {df['review_text'].str.len().min()} / {df['review_text'].str.len().max()}")

    # Résultat
    print(f"\n{'=' * 60}")
    if errors:
        print(f"[ÉCHEC] {len(errors)} erreur(s) détectée(s) :")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("[SUCCÈS] Dataset validé — prêt pour import en base")
    print("=" * 60)


if __name__ == "__main__":
    validate()
