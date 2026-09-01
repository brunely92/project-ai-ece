"""
C1 — Collecte depuis Rotten Tomatoes Movie Reviews (Cornell University)
Source : https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes
Référence : Pang & Lee, 2005 — "Seeing Stars: Exploiting Class Relationships
            for Sentiment Categorization with Respect to Rating Scales"

Dataset académique de référence pour le sentiment analysis.
~10 600 critiques de films annotées positive/negative.
"""
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "rottentomatoes_reviews_raw.csv"
LOG_FILE = Path("logs/collect_rottentomatoes.log")
LOG_FILE.parent.mkdir(exist_ok=True)


def log(level: str, msg: str):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {level:5s} | {msg}\n")
    print(f"[{level}] {msg}")


def collect_rotten_tomatoes() -> pd.DataFrame:
    """
    Télécharge le dataset Rotten Tomatoes depuis HuggingFace Hub.
    Splits : train (~8530) + validation (~1066) + test (~1066).
    """
    try:
        from datasets import load_dataset
    except ImportError:
        log("ERROR", "La librairie 'datasets' n'est pas installée.")
        print("         pip install datasets")
        sys.exit(1)

    log("INFO", "Téléchargement Rotten Tomatoes depuis HuggingFace Hub...")

    try:
        dataset = load_dataset("cornell-movie-review-data/rotten_tomatoes")
    except Exception as e:
        log("ERROR", f"Erreur téléchargement : {e}")
        sys.exit(1)

    frames = []
    for split_name in ["train", "validation", "test"]:
        if split_name in dataset:
            df_split = dataset[split_name].to_pandas()
            df_split["split"] = split_name
            frames.append(df_split)
            log("INFO", f"{split_name} : {len(df_split)} reviews")

    df = pd.concat(frames, ignore_index=True)

    # Normaliser les colonnes
    df = df.rename(columns={"text": "review_text"})
    df["sentiment"] = df["label"].map({0: "negative", 1: "positive"})
    df["source"] = "rotten_tomatoes_cornell"
    df["source_url"] = "https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes"
    df["collected_at"] = datetime.now().isoformat()

    df = df[["review_text", "sentiment", "source", "split", "source_url", "collected_at"]]

    return df


def main():
    print("=" * 60)
    print(f"COLLECTE ROTTEN TOMATOES — {datetime.now().isoformat()}")
    print("=" * 60)

    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        print(f"[INFO] Fichier existant : {OUTPUT_FILE} ({len(existing)} lignes)")
        print("[INFO] Pour recréer, supprimez le fichier et relancez.")
        return

    df = collect_rotten_tomatoes()
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] {len(df)} reviews sauvegardées dans {OUTPUT_FILE}")
    print(f"     Distribution : {df['sentiment'].value_counts().to_dict()}")
    print(f"     Splits       : {df['split'].value_counts().to_dict()}")
    log("INFO", f"Collecte terminée : {len(df)} reviews")
    print("=" * 60)


if __name__ == "__main__":
    main()
