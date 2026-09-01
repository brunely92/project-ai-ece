"""
C3 — Pipeline de nettoyage avancé
- Agrégation multi-sources (CSV, API, scraping)
- Normalisation texte (HTML, unicode, contractions)
- Score de qualité par ligne (0-100)
- Détection de langue (filtre anglais)
- Rapport de nettoyage détaillé avec métriques avant/après
"""
import re
import unicodedata
from pathlib import Path
from datetime import datetime
from collections import Counter

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = PROCESSED_DIR / "reviews_clean.csv"
REPORT_FILE = PROCESSED_DIR / "cleaning_report.txt"

# Contractions anglaises courantes
CONTRACTIONS = {
    "won't": "will not", "can't": "cannot", "n't": " not",
    "'re": " are", "'s": " is", "'d": " would", "'ll": " will",
    "'ve": " have", "'m": " am",
}


def load_all_sources() -> pd.DataFrame:
    """Charge et agrège toutes les sources brutes avec traçabilité."""
    frames = []

    # Source 1 : IMDB CSV (Kaggle)
    imdb_file = RAW_DIR / "imdb_reviews_raw.csv"
    if imdb_file.exists():
        df = pd.read_csv(imdb_file)
        df = df.rename(columns={"review": "review_text"})
        df["source"] = "csv_kaggle"
        df["source_file"] = str(imdb_file)
        frames.append(df[["review_text", "sentiment", "source", "source_file"]])
        print(f"[OK] CSV Kaggle     : {len(df):>6d} lignes ({imdb_file.name})")

    # Source 2 : OMDB API
    omdb_file = RAW_DIR / "omdb_movies_raw.csv"
    if omdb_file.exists():
        df = pd.read_csv(omdb_file)
        if "plot" in df.columns:
            df = df.rename(columns={"plot": "review_text"})
            df["source"] = "api_omdb"
            df["sentiment"] = None
            df["source_file"] = str(omdb_file)
            frames.append(df[["review_text", "sentiment", "source", "source_file"]])
            print(f"[OK] OMDB API       : {len(df):>6d} lignes ({omdb_file.name})")

    # Source 3 : Scraping IMDB
    scraping_file = RAW_DIR / "scraped_reviews_raw.csv"
    if scraping_file.exists():
        df = pd.read_csv(scraping_file)
        if "review_text" in df.columns:
            df["source"] = "scraping_imdb"
            # Déduire le sentiment depuis le rating si disponible
            if "rating" in df.columns:
                df["sentiment"] = df["rating"].apply(
                    lambda r: "positive" if pd.notna(r) and r >= 7
                    else ("negative" if pd.notna(r) and r <= 4 else None)
                )
            else:
                df["sentiment"] = None
            df["source_file"] = str(scraping_file)
            frames.append(df[["review_text", "sentiment", "source", "source_file"]])
            print(f"[OK] Scraping IMDB  : {len(df):>6d} lignes ({scraping_file.name})")

    # Source 4 : TMDB API
    tmdb_file = RAW_DIR / "tmdb_movies_raw.csv"
    if tmdb_file.exists():
        df = pd.read_csv(tmdb_file)
        if "overview" in df.columns:
            df = df.rename(columns={"overview": "review_text"})
            df["source"] = "api_tmdb"
            df["sentiment"] = None
            df["source_file"] = str(tmdb_file)
            frames.append(df[["review_text", "sentiment", "source", "source_file"]])
            print(f"[OK] TMDB API       : {len(df):>6d} lignes ({tmdb_file.name})")

    if not frames:
        raise FileNotFoundError("Aucune source dans data/raw/")

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n[TOTAL] {len(combined)} lignes agrégées depuis {len(frames)} sources")
    return combined


def clean_text(text: str) -> str:
    """Pipeline de normalisation texte avancé."""
    if not isinstance(text, str):
        return ""

    # 1. Décoder les entités HTML (&amp; → &, &#39; → ', etc.)
    import html
    text = html.unescape(text)

    # 2. Supprimer les balises HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # 3. Normaliser unicode (accents, caractères spéciaux)
    text = unicodedata.normalize("NFKD", text)

    # 4. Expanser les contractions
    for contraction, expansion in CONTRACTIONS.items():
        text = text.replace(contraction, expansion)

    # 5. Supprimer URLs
    text = re.sub(r"https?://\S+", "", text)

    # 6. Supprimer caractères non imprimables
    text = re.sub(r"[^\w\s.,!?'\"\-;:()&]", "", text)

    # 7. Normaliser espaces et sauts de ligne
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def compute_quality_score(text: str) -> int:
    """
    Score de qualité d'un avis (0-100).
    Critères : longueur, vocabulaire, ponctuation, structure.
    """
    if not text or len(text) < 10:
        return 0

    score = 0
    words = text.split()
    word_count = len(words)

    # Longueur (0-30 points)
    if word_count >= 50:
        score += 30
    elif word_count >= 20:
        score += 20
    elif word_count >= 10:
        score += 10
    else:
        score += 5

    # Diversité vocabulaire (0-25 points)
    unique_words = len(set(w.lower() for w in words))
    diversity = unique_words / max(word_count, 1)
    score += min(int(diversity * 50), 25)

    # Ponctuation présente (0-15 points)
    has_period = "." in text
    has_comma = "," in text
    has_excl_or_quest = "!" in text or "?" in text
    score += (has_period * 5) + (has_comma * 5) + (has_excl_or_quest * 5)

    # Phrases multiples (0-15 points)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    if len(sentences) >= 5:
        score += 15
    elif len(sentences) >= 3:
        score += 10
    elif len(sentences) >= 2:
        score += 5

    # Pas de CAPS LOCK abusif (0-15 points)
    upper_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if upper_ratio < 0.3:
        score += 15
    elif upper_ratio < 0.5:
        score += 8

    return min(score, 100)


def detect_english(text: str) -> bool:
    """Détection simple de l'anglais basée sur les mots courants."""
    english_words = {"the", "is", "was", "are", "and", "of", "to", "in", "it", "for",
                     "that", "this", "with", "not", "but", "have", "has", "had", "be",
                     "from", "or", "an", "will", "my", "all", "would", "there", "their",
                     "what", "about", "which", "when", "one", "very", "after", "can", "do"}
    words = set(text.lower().split()[:50])
    matches = words & english_words
    return len(matches) >= 3


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Pipeline de nettoyage complet avec métriques détaillées."""
    stats = {"initial": len(df), "by_source_initial": df["source"].value_counts().to_dict()}

    # 1. Supprimer les lignes sans texte
    df = df.dropna(subset=["review_text"])
    df = df[df["review_text"].str.strip() != ""]
    stats["after_nulls"] = len(df)

    # 2. Normaliser le texte
    df["review_text"] = df["review_text"].apply(clean_text)

    # 3. Supprimer les doublons (après nettoyage)
    df = df.drop_duplicates(subset=["review_text"])
    stats["after_dedup"] = len(df)

    # 4. Filtre longueur minimum
    df = df[df["review_text"].str.len() >= 20]
    stats["after_length"] = len(df)

    # 5. Détection de langue (filtre anglais)
    df["is_english"] = df["review_text"].apply(detect_english)
    non_english = (~df["is_english"]).sum()
    df = df[df["is_english"]].drop(columns=["is_english"])
    stats["after_lang"] = len(df)
    stats["non_english_removed"] = non_english

    # 6. Normaliser sentiments
    df["sentiment"] = df["sentiment"].apply(
        lambda x: x.strip().lower() if isinstance(x, str) else None
    )
    valid = {"positive", "negative", None}
    df = df[df["sentiment"].apply(lambda x: x in valid)]
    stats["final"] = len(df)

    # 7. Calculer le score de qualité
    df["quality_score"] = df["review_text"].apply(compute_quality_score)
    stats["avg_quality"] = round(df["quality_score"].mean(), 1)
    stats["low_quality"] = (df["quality_score"] < 30).sum()

    # 8. Statistiques textuelles
    df["text_length"] = df["review_text"].str.len()
    df["word_count"] = df["review_text"].str.split().str.len()

    # 9. IDs et colonnes finales
    df = df.reset_index(drop=True)
    df.insert(0, "id", range(1, len(df) + 1))

    stats["by_source_final"] = df["source"].value_counts().to_dict()
    stats["by_sentiment_final"] = df[df["sentiment"].notna()]["sentiment"].value_counts().to_dict()

    return df, stats


def print_report(stats: dict):
    """Affiche et sauvegarde un rapport de nettoyage détaillé."""
    report = []
    report.append("=" * 60)
    report.append("RAPPORT DE NETTOYAGE DÉTAILLÉ")
    report.append("=" * 60)
    report.append(f"")
    report.append(f"  Lignes initiales         : {stats['initial']}")
    report.append(f"  Sources initiales        : {stats['by_source_initial']}")
    report.append(f"  Après suppression nulls  : {stats['after_nulls']} (-{stats['initial'] - stats['after_nulls']})")
    report.append(f"  Après dédoublonnage      : {stats['after_dedup']} (-{stats['after_nulls'] - stats['after_dedup']})")
    report.append(f"  Après filtre longueur    : {stats['after_length']} (-{stats['after_dedup'] - stats['after_length']})")
    report.append(f"  Non-anglais supprimés    : {stats['non_english_removed']}")
    report.append(f"  Après filtre langue      : {stats['after_lang']} (-{stats['after_length'] - stats['after_lang']})")
    report.append(f"  Dataset final            : {stats['final']} lignes")
    report.append(f"")
    report.append(f"  Sources finales          : {stats['by_source_final']}")
    report.append(f"  Sentiments               : {stats.get('by_sentiment_final', {})}")
    report.append(f"  Score qualité moyen      : {stats['avg_quality']}/100")
    report.append(f"  Avis basse qualité (<30) : {stats['low_quality']}")
    report.append("=" * 60)

    text = "\n".join(report)
    print(text)

    # Sauvegarder le rapport
    REPORT_FILE.write_text(text, encoding="utf-8")
    print(f"\n[OK] Rapport sauvegardé : {REPORT_FILE}")


def main():
    print("=" * 60)
    print(f"NETTOYAGE AVANCÉ — {datetime.now().isoformat()}")
    print("=" * 60)

    df = load_all_sources()
    df_clean, stats = clean_dataset(df)

    # Sauvegarder (sans les colonnes techniques)
    export_cols = ["id", "review_text", "sentiment", "source", "quality_score", "text_length", "word_count"]
    df_clean[export_cols].to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] Dataset nettoyé : {OUTPUT_FILE}")
    print_report(stats)


if __name__ == "__main__":
    main()
