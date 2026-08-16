"""
C1 — Collecte depuis un fichier CSV (Kaggle IMDB Reviews)
Source : https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "imdb_reviews_raw.csv"
LOCAL_SOURCE = RAW_DIR / "IMDB_Dataset.csv"


def collect_from_csv() -> pd.DataFrame:
    """Charge le dataset IMDB depuis un fichier CSV local."""
    if not LOCAL_SOURCE.exists():
        print(f"[ERREUR] Fichier source introuvable : {LOCAL_SOURCE}")
        print("  Téléchargez le dataset depuis Kaggle et placez-le dans data/raw/")
        sys.exit(1)
    try:
        df = pd.read_csv(LOCAL_SOURCE)
        print(f"[OK] Fichier chargé : {LOCAL_SOURCE}")
        print(f"     Lignes : {len(df)} | Colonnes : {list(df.columns)}")
        return df
    except Exception as e:
        print(f"[ERREUR] Lecture fichier : {e}")
        sys.exit(1)


def main():
    print("=" * 60)
    print(f"COLLECTE CSV — {datetime.now().isoformat()}")
    print("=" * 60)
    df = collect_from_csv()
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[OK] Sauvegardé : {OUTPUT_FILE} ({len(df)} lignes)")
    print("=" * 60)


if __name__ == "__main__":
    main()
