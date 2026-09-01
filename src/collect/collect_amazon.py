"""
C1 — Collecte Amazon Product Reviews (subset 50K)
Source : https://huggingface.co/datasets/amazon_polarity
Référence : McAuley & Leskovec, 2013 — "Hidden Factors and Hidden Topics"

Dataset massif de 3.6M reviews Amazon. On extrait un subset de 50 000
pour le projet. Les reviews contiennent un titre et un texte complet
avec label positif/négatif.
"""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "amazon_reviews_raw.csv"
LOG_FILE = Path("logs/collect_amazon.log")
LOG_FILE.parent.mkdir(exist_ok=True)

SUBSET_SIZE = 50_000


def log(level, msg):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {level:5s} | {msg}\n")
    print(f"[{level}] {msg}")


def collect_amazon() -> pd.DataFrame:
    try:
        from datasets import load_dataset
    except ImportError:
        log("ERROR", "pip install datasets")
        sys.exit(1)

    log("INFO", f"Téléchargement Amazon Reviews (subset {SUBSET_SIZE:,})...")

    try:
        dataset = load_dataset(
            "amazon_polarity",
            split=f"train[:{SUBSET_SIZE}]",
        )
    except Exception as e:
        log("ERROR", f"Erreur : {e}")
        sys.exit(1)

    df = dataset.to_pandas()

    # Combiner titre + contenu pour un texte plus riche
    df["review_text"] = df["title"].fillna("") + ". " + df["content"].fillna("")
    df["review_text"] = df["review_text"].str.strip(". ")
    df["sentiment"] = df["label"].map({0: "negative", 1: "positive"})
    df["source"] = "amazon_reviews"
    df["source_url"] = "https://huggingface.co/datasets/amazon_polarity"
    df["collected_at"] = datetime.now().isoformat()

    df = df[["review_text", "sentiment", "source", "source_url", "collected_at"]]
    log("INFO", f"Collecté : {len(df)} reviews")
    return df


def main():
    print("=" * 60)
    print(f"COLLECTE AMAZON REVIEWS — {datetime.now().isoformat()}")
    print("=" * 60)

    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        print(f"[INFO] Fichier existant : {OUTPUT_FILE} ({len(existing)} lignes)")
        return

    df = collect_amazon()
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] {len(df):,} reviews sauvegardées dans {OUTPUT_FILE}")
    print(f"     Distribution : {df['sentiment'].value_counts().to_dict()}")
    log("INFO", f"Terminé : {len(df)} reviews")
    print("=" * 60)


if __name__ == "__main__":
    main()
