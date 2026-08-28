"""
C3 — Nettoyage et agrégation des données
Règles : suppression doublons, gestion nulls, normalisation texte,
suppression avis trop courts, homogénéisation formats.
"""
import re
from pathlib import Path
from datetime import datetime
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = RAW_DIR / "imdb_reviews_raw.csv"
OUTPUT_FILE = PROCESSED_DIR / "reviews_clean.csv"


def load_raw_data() -> pd.DataFrame:
    """Charge toutes les sources brutes et les agrège."""
    frames = []

    # Source 1 : IMDB CSV
    if INPUT_FILE.exists():
        df_imdb = pd.read_csv(INPUT_FILE)
        df_imdb["source"] = "csv_imdb"
        df_imdb = df_imdb.rename(columns={"review": "review_text"})
        frames.append(df_imdb)
        print(f"[OK] CSV IMDB chargé : {len(df_imdb)} lignes")

    # Source 2 : scraping
    scraping_file = RAW_DIR / "scraped_reviews_raw.csv"
    if scraping_file.exists():
        df_scrap = pd.read_csv(scraping_file)
        df_scrap = df_scrap.rename(columns={"text": "review_text"})
        df_scrap["source"] = "scraping"
        df_scrap["sentiment"] = None  # pas de label, sera prédit par le modèle
        frames.append(df_scrap[["review_text", "sentiment", "source"]])
        print(f"[OK] Scraping chargé : {len(df_scrap)} lignes")

    # Source 3 : API TMDB (overviews comme avis simulés)
    tmdb_file = RAW_DIR / "tmdb_movies_raw.csv"
    if tmdb_file.exists():
        df_tmdb = pd.read_csv(tmdb_file)
        df_tmdb = df_tmdb.rename(columns={"overview": "review_text"})
        df_tmdb["source"] = "api_tmdb"
        df_tmdb["sentiment"] = None
        frames.append(df_tmdb[["review_text", "sentiment", "source"]])
        print(f"[OK] TMDB chargé : {len(df_tmdb)} lignes")

    if not frames:
        raise FileNotFoundError("Aucune source de données trouvée dans data/raw/")

    return pd.concat(frames, ignore_index=True)


def clean_text(text: str) -> str:
    """Normalise un texte d'avis."""
    if not isinstance(text, str):
        return ""
    # Supprimer les balises HTML résiduelles
    text = re.sub(r"<[^>]+>", " ", text)
    # Supprimer les caractères spéciaux excessifs (garder ponctuation de base)
    text = re.sub(r"[^\w\s.,!?'\"-]", "", text)
    # Normaliser les espaces multiples
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Applique toutes les règles de nettoyage."""
    stats = {"initial": len(df)}

    # 1. Supprimer les doublons exacts
    df = df.drop_duplicates(subset=["review_text"])
    stats["apres_dedup"] = len(df)

    # 2. Supprimer les lignes sans texte
    df = df.dropna(subset=["review_text"])
    df = df[df["review_text"].str.strip() != ""]
    stats["apres_nulls"] = len(df)

    # 3. Normaliser le texte
    df["review_text"] = df["review_text"].apply(clean_text)

    # 4. Supprimer les avis trop courts (< 20 caractères)
    df = df[df["review_text"].str.len() >= 20]
    stats["apres_court"] = len(df)

    # 5. Normaliser les sentiments
    df["sentiment"] = df["sentiment"].apply(
        lambda x: x.strip().lower() if isinstance(x, str) else None
    )
    valid_sentiments = {"positive", "negative", None}
    df = df[df["sentiment"].apply(lambda x: x in valid_sentiments)]
    stats["final"] = len(df)

    # 6. Ajouter un ID unique
    df = df.reset_index(drop=True)
    df.insert(0, "id", range(1, len(df) + 1))

    # Rapport de nettoyage
    print("\n--- Rapport de nettoyage ---")
    print(f"  Lignes initiales     : {stats['initial']}")
    print(f"  Après dé-doublonnage : {stats['apres_dedup']} (-{stats['initial'] - stats['apres_dedup']})")
    print(f"  Après suppression nulls : {stats['apres_nulls']} (-{stats['apres_dedup'] - stats['apres_nulls']})")
    print(f"  Après filtre longueur : {stats['apres_court']} (-{stats['apres_nulls'] - stats['apres_court']})")
    print(f"  Dataset final        : {stats['final']} lignes")
    print(f"  Colonnes             : {list(df.columns)}")

    return df


def main():
    print("=" * 60)
    print(f"NETTOYAGE DATASET — {datetime.now().isoformat()}")
    print("=" * 60)

    df = load_raw_data()
    df_clean = clean_dataset(df)
    df_clean.to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] Dataset nettoyé sauvegardé : {OUTPUT_FILE}")
    if "sentiment" in df_clean.columns:
        labeled = df_clean[df_clean["sentiment"].notna()]
        print(f"     Avis labellisés : {len(labeled)} / {len(df_clean)}")
        if len(labeled) > 0:
            print(f"     Distribution : {labeled['sentiment'].value_counts().to_dict()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
