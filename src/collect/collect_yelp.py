"""
C1 — Collecte Yelp Reviews (subset 50K)
Source : https://huggingface.co/datasets/yelp_polarity
Référence : Zhang, Zhao & LeCun, 2015 — "Character-level Convolutional
            Networks for Text Classification"

Dataset de 560K reviews Yelp. On extrait 50 000 pour le projet.
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "yelp_reviews_raw.csv"
LOG_FILE = Path("logs/collect_yelp.log")
LOG_FILE.parent.mkdir(exist_ok=True)

SUBSET_SIZE = 50_000


def log(level, msg):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {level:5s} | {msg}\n")
    print(f"[{level}] {msg}")


def collect_yelp() -> pd.DataFrame:
    try:
        from datasets import load_dataset
    except ImportError:
        log("ERROR", "pip install datasets")
        sys.exit(1)

    log("INFO", f"Téléchargement Yelp Reviews (subset {SUBSET_SIZE:,})...")

    try:
        dataset = load_dataset(
            "fancyzhx/yelp_polarity",
            split=f"train[:{SUBSET_SIZE}]",
        )
    except Exception as e:
        log("ERROR", f"Erreur : {e}")
        sys.exit(1)

    df = dataset.to_pandas()

    df = df.rename(columns={"text": "review_text"})
    df["sentiment"] = df["label"].map({0: "negative", 1: "positive"})
    df["source"] = "yelp_reviews"
    df["source_url"] = "https://huggingface.co/datasets/yelp_polarity"
    df["collected_at"] = datetime.now().isoformat()

    df = df[["review_text", "sentiment", "source", "source_url", "collected_at"]]
    log("INFO", f"Collecté : {len(df)} reviews")
    return df


def main():
    print("=" * 60)
    print(f"COLLECTE YELP REVIEWS — {datetime.now().isoformat()}")
    print("=" * 60)

    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        print(f"[INFO] Fichier existant : {OUTPUT_FILE} ({len(existing)} lignes)")
        return

    df = collect_yelp()
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] {len(df):,} reviews sauvegardées dans {OUTPUT_FILE}")
    print(f"     Distribution : {df['sentiment'].value_counts().to_dict()}")
    log("INFO", f"Terminé : {len(df)} reviews")
    print("=" * 60)


if __name__ == "__main__":
    main()
