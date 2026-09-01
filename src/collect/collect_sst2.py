"""
C1 — Collecte depuis Stanford Sentiment Treebank v2 (SST-2)
Source : https://huggingface.co/datasets/stanfordnlp/sst2
Référence : Socher et al., 2013 — "Recursive Deep Models for Semantic Compositionality"

Dataset académique de référence en analyse de sentiment.
~67 000 phrases de critiques de films annotées positive/negative.
"""
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "sst2_reviews_raw.csv"
LOG_FILE = Path("logs/collect_sst2.log")
LOG_FILE.parent.mkdir(exist_ok=True)


def log(level: str, msg: str):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | {level:5s} | {msg}\n")
    print(f"[{level}] {msg}")


def collect_sst2() -> pd.DataFrame:
    """
    Télécharge le dataset SST-2 depuis HuggingFace Hub.
    Splits : train (~67K) + validation (~872).
    """
    try:
        from datasets import load_dataset
    except ImportError:
        log("ERROR", "La librairie 'datasets' n'est pas installée.")
        print("         pip install datasets")
        sys.exit(1)

    log("INFO", "Téléchargement SST-2 depuis HuggingFace Hub...")

    try:
        dataset = load_dataset("stanfordnlp/sst2")
    except Exception as e:
        log("ERROR", f"Erreur téléchargement : {e}")
        sys.exit(1)

    frames = []

    # Train split
    if "train" in dataset:
        df_train = dataset["train"].to_pandas()
        df_train["split"] = "train"
        frames.append(df_train)
        log("INFO", f"Train : {len(df_train)} phrases")

    # Validation split
    if "validation" in dataset:
        df_val = dataset["validation"].to_pandas()
        df_val["split"] = "validation"
        frames.append(df_val)
        log("INFO", f"Validation : {len(df_val)} phrases")

    df = pd.concat(frames, ignore_index=True)

    # Normaliser les colonnes
    df = df.rename(columns={"sentence": "review_text"})
    df["sentiment"] = df["label"].map({0: "negative", 1: "positive"})
    df["source"] = "sst2_stanford"
    df["source_url"] = "https://huggingface.co/datasets/stanfordnlp/sst2"
    df["collected_at"] = datetime.now().isoformat()

    # Garder colonnes utiles
    df = df[["review_text", "sentiment", "source", "split", "source_url", "collected_at"]]

    return df


def main():
    print("=" * 60)
    print(f"COLLECTE SST-2 STANFORD — {datetime.now().isoformat()}")
    print("=" * 60)

    if OUTPUT_FILE.exists():
        existing = pd.read_csv(OUTPUT_FILE)
        print(f"[INFO] Fichier existant : {OUTPUT_FILE} ({len(existing)} lignes)")
        print("[INFO] Pour recréer, supprimez le fichier et relancez.")
        return

    df = collect_sst2()
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] {len(df)} phrases sauvegardées dans {OUTPUT_FILE}")
    print(f"     Distribution : {df['sentiment'].value_counts().to_dict()}")
    print(f"     Splits       : {df['split'].value_counts().to_dict()}")
    log("INFO", f"Collecte terminée : {len(df)} phrases")
    print("=" * 60)


if __name__ == "__main__":
    main()
