"""
C3 — Pipeline de nettoyage avancé multi-sources
Agrège 3+ sources (IMDB 50K, SST-2 67K, Rotten Tomatoes 10K)
Score qualité, détection langue, normalisation, rapport détaillé.
"""
import re
import html
import unicodedata
from pathlib import Path
from datetime import datetime

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_DIR / "reviews_clean.csv"
REPORT_FILE = PROCESSED_DIR / "cleaning_report.txt"

CONTRACTIONS = {
    "won't": "will not", "can't": "cannot", "n't": " not",
    "'re": " are", "'s": " is", "'d": " would", "'ll": " will",
    "'ve": " have", "'m": " am",
}


def load_all_sources() -> pd.DataFrame:
    """Charge et agrège toutes les sources brutes avec traçabilité."""
    frames = []

    # Source 1 : IMDB CSV (Kaggle) — ~50 000 reviews
    imdb_file = RAW_DIR / "imdb_reviews_raw.csv"
    if imdb_file.exists():
        df = pd.read_csv(imdb_file)
        df = df.rename(columns={"review": "review_text"})
        df["source"] = "csv_kaggle_imdb"
        df["source_file"] = str(imdb_file)
        frames.append(df[["review_text", "sentiment", "source", "source_file"]])
        print(f"[OK] IMDB Kaggle       : {len(df):>6d} lignes")

    # Source 2 : SST-2 Stanford — ~67 000 phrases
    sst2_file = RAW_DIR / "sst2_reviews_raw.csv"
    if sst2_file.exists():
        df = pd.read_csv(sst2_file)
        df["source"] = "sst2_stanford"
        df["source_file"] = str(sst2_file)
        frames.append(df[["review_text", "sentiment", "source", "source_file"]])
        print(f"[OK] SST-2 Stanford    : {len(df):>6d} lignes")

    # Source 3 : Rotten Tomatoes Cornell — ~10 600 reviews
    rt_file = RAW_DIR / "rottentomatoes_reviews_raw.csv"
    if rt_file.exists():
        df = pd.read_csv(rt_file)
        df["source"] = "rotten_tomatoes"
        df["source_file"] = str(rt_file)
        frames.append(df[["review_text", "sentiment", "source", "source_file"]])
        print(f"[OK] Rotten Tomatoes   : {len(df):>6d} lignes")


    # Source 4 : Amazon Reviews — ~50 000 reviews
    amazon_file = RAW_DIR / "amazon_reviews_raw.csv"
    if amazon_file.exists():
        df = pd.read_csv(amazon_file)
        df["source"] = "amazon_reviews"
        df["source_file"] = str(amazon_file)
        frames.append(df[["review_text", "sentiment", "source", "source_file"]])
        print(f"[OK] Amazon Reviews    : {len(df):>6d} lignes")

    # Source 5 : Yelp Reviews — ~50 000 reviews
    yelp_file = RAW_DIR / "yelp_reviews_raw.csv"
    if yelp_file.exists():
        df = pd.read_csv(yelp_file)
        df["source"] = "yelp_reviews"
        df["source_file"] = str(yelp_file)
        frames.append(df[["review_text", "sentiment", "source", "source_file"]])
        print(f"[OK] Yelp Reviews      : {len(df):>6d} lignes")

    # Source 6 : OMDB API (plots enrichissement)
    omdb_file = RAW_DIR / "omdb_movies_raw.csv"
    if omdb_file.exists():
        df = pd.read_csv(omdb_file)
        if "plot" in df.columns:
            df = df.rename(columns={"plot": "review_text"})
            df["source"] = "api_omdb"
            df["sentiment"] = None
            df["source_file"] = str(omdb_file)
            frames.append(df[["review_text", "sentiment", "source", "source_file"]])
            print(f"[OK] OMDB API          : {len(df):>6d} lignes")

    # Source 5 : Scraping IMDB
    scraping_file = RAW_DIR / "scraped_reviews_raw.csv"
    if scraping_file.exists():
        df = pd.read_csv(scraping_file)
        if "review_text" in df.columns:
            if "rating" in df.columns:
                df["sentiment"] = df["rating"].apply(
                    lambda r: "positive" if pd.notna(r) and r >= 7
                    else ("negative" if pd.notna(r) and r <= 4 else None)
                )
            else:
                df["sentiment"] = None
            df["source"] = "scraping_imdb"
            df["source_file"] = str(scraping_file)
            frames.append(df[["review_text", "sentiment", "source", "source_file"]])
            print(f"[OK] Scraping IMDB     : {len(df):>6d} lignes")

    if not frames:
        raise FileNotFoundError("Aucune source dans data/raw/")

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n[TOTAL] {len(combined):>6d} lignes agrégées depuis {len(frames)} sources")
    return combined


def clean_text(text: str) -> str:
    """Pipeline de normalisation texte."""
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unicodedata.normalize("NFKD", text)
    for contraction, expansion in CONTRACTIONS.items():
        text = text.replace(contraction, expansion)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^\w\s.,!?'\"\-;:()&]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def compute_quality_score(text: str) -> int:
    """Score de qualité 0-100."""
    if not text or len(text) < 10:
        return 0
    score = 0
    words = text.split()
    word_count = len(words)

    if word_count >= 50: score += 30
    elif word_count >= 20: score += 20
    elif word_count >= 10: score += 10
    else: score += 5

    unique = len(set(w.lower() for w in words))
    score += min(int(unique / max(word_count, 1) * 50), 25)

    score += ("." in text) * 5 + ("," in text) * 5 + ("!" in text or "?" in text) * 5

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 5]
    if len(sentences) >= 5: score += 15
    elif len(sentences) >= 3: score += 10
    elif len(sentences) >= 2: score += 5

    upper_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if upper_ratio < 0.3: score += 15
    elif upper_ratio < 0.5: score += 8

    return min(score, 100)


def detect_english(text: str) -> bool:
    """Détection anglais par mots courants."""
    en_words = {"the", "is", "was", "are", "and", "of", "to", "in", "it", "for",
                "that", "this", "with", "not", "but", "have", "has", "be", "from",
                "or", "an", "will", "my", "all", "would", "there", "what", "about"}
    words = set(text.lower().split()[:50])
    return len(words & en_words) >= 2


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Pipeline de nettoyage complet."""
    stats = {"initial": len(df), "by_source_initial": df["source"].value_counts().to_dict()}

    df = df.dropna(subset=["review_text"])
    df = df[df["review_text"].str.strip() != ""]
    stats["after_nulls"] = len(df)

    df["review_text"] = df["review_text"].apply(clean_text)

    df = df.drop_duplicates(subset=["review_text"])
    stats["after_dedup"] = len(df)

    df = df[df["review_text"].str.len() >= 20]
    stats["after_length"] = len(df)

    df["is_english"] = df["review_text"].apply(detect_english)
    non_english = (~df["is_english"]).sum()
    df = df[df["is_english"]].drop(columns=["is_english"])
    stats["after_lang"] = len(df)
    stats["non_english_removed"] = non_english

    df["sentiment"] = df["sentiment"].apply(
        lambda x: x.strip().lower() if isinstance(x, str) else None
    )
    valid = {"positive", "negative", None}
    df = df[df["sentiment"].apply(lambda x: x in valid)]
    stats["final"] = len(df)

    df["quality_score"] = df["review_text"].apply(compute_quality_score)
    df["text_length"] = df["review_text"].str.len()
    df["word_count"] = df["review_text"].str.split().str.len()

    stats["avg_quality"] = round(df["quality_score"].mean(), 1)
    stats["low_quality"] = int((df["quality_score"] < 30).sum())

    df = df.reset_index(drop=True)
    df.insert(0, "id", range(1, len(df) + 1))

    stats["by_source_final"] = df["source"].value_counts().to_dict()
    labeled = df[df["sentiment"].notna()]
    stats["by_sentiment_final"] = labeled["sentiment"].value_counts().to_dict() if len(labeled) > 0 else {}
    stats["labeled_count"] = len(labeled)
    stats["unlabeled_count"] = len(df) - len(labeled)

    return df, stats


def print_report(stats: dict):
    lines = [
        "=" * 70,
        "RAPPORT DE NETTOYAGE DÉTAILLÉ",
        "=" * 70,
        "",
        f"  Lignes initiales           : {stats['initial']:>8d}",
        f"  Sources initiales          : {stats['by_source_initial']}",
        f"  Après suppression nulls    : {stats['after_nulls']:>8d} (-{stats['initial'] - stats['after_nulls']})",
        f"  Après dédoublonnage        : {stats['after_dedup']:>8d} (-{stats['after_nulls'] - stats['after_dedup']})",
        f"  Après filtre longueur      : {stats['after_length']:>8d} (-{stats['after_dedup'] - stats['after_length']})",
        f"  Non-anglais supprimés      : {stats['non_english_removed']:>8d}",
        f"  Après filtre langue        : {stats['after_lang']:>8d}",
        f"  Dataset final              : {stats['final']:>8d} lignes",
        "",
        f"  Sources finales            : {stats['by_source_final']}",
        f"  Sentiments                 : {stats.get('by_sentiment_final', {})}",
        f"  Avis labellisés            : {stats['labeled_count']:>8d}",
        f"  Avis non labellisés        : {stats['unlabeled_count']:>8d}",
        f"  Score qualité moyen        : {stats['avg_quality']}/100",
        f"  Avis basse qualité (<30)   : {stats['low_quality']:>8d}",
        "=" * 70,
    ]
    text = "\n".join(lines)
    print(text)
    REPORT_FILE.write_text(text, encoding="utf-8")
    print(f"\n[OK] Rapport sauvegardé : {REPORT_FILE}")


def main():
    print("=" * 70)
    print(f"NETTOYAGE MULTI-SOURCES — {datetime.now().isoformat()}")
    print("=" * 70)

    df = load_all_sources()
    df_clean, stats = clean_dataset(df)

    export_cols = ["id", "review_text", "sentiment", "source", "quality_score", "text_length", "word_count"]
    df_clean[export_cols].to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] Dataset nettoyé : {OUTPUT_FILE}")
    print_report(stats)


if __name__ == "__main__":
    main()
