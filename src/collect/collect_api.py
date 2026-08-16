"""
C1 — Collecte depuis une API REST (TMDB - The Movie Database)
Documentation : https://developer.themoviedb.org/docs
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "tmdb_movies_raw.csv"
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"


def check_api_key():
    if not TMDB_API_KEY or TMDB_API_KEY == "replace_with_your_tmdb_api_key":
        print("[ERREUR] Clé API TMDB non configurée.")
        print("  1. Créez un compte sur https://www.themoviedb.org/")
        print("  2. Obtenez une clé API dans Paramètres > API")
        print("  3. Ajoutez TMDB_API_KEY=votre_clé dans .env")
        sys.exit(1)


def fetch_popular_movies(pages: int = 5) -> list[dict]:
    """Récupère les films populaires depuis l'API TMDB."""
    all_movies = []
    for page in range(1, pages + 1):
        try:
            response = requests.get(
                f"{TMDB_BASE_URL}/movie/popular",
                params={"api_key": TMDB_API_KEY, "language": "en-US", "page": page},
                timeout=15,
            )
            response.raise_for_status()
            movies = response.json().get("results", [])
            all_movies.extend(movies)
            print(f"[OK] Page {page}/{pages} — {len(movies)} films")
            time.sleep(0.3)
        except requests.Timeout:
            print(f"[WARN] Timeout page {page}")
        except requests.HTTPError as e:
            print(f"[ERREUR] HTTP {e.response.status_code} page {page}")
        except requests.RequestException as e:
            print(f"[ERREUR] Réseau page {page} : {e}")
    return all_movies


def movies_to_dataframe(movies: list[dict]) -> pd.DataFrame:
    records = []
    for m in movies:
        records.append({
            "tmdb_id": m.get("id"),
            "title": m.get("title"),
            "original_title": m.get("original_title"),
            "release_date": m.get("release_date"),
            "vote_average": m.get("vote_average"),
            "vote_count": m.get("vote_count"),
            "popularity": m.get("popularity"),
            "genre_ids": str(m.get("genre_ids", [])),
            "overview": m.get("overview"),
            "original_language": m.get("original_language"),
        })
    return pd.DataFrame(records)


def main():
    print("=" * 60)
    print(f"COLLECTE API TMDB — {datetime.now().isoformat()}")
    print("=" * 60)
    check_api_key()
    movies = fetch_popular_movies(pages=5)
    if not movies:
        print("[ERREUR] Aucun film récupéré.")
        sys.exit(1)
    df = movies_to_dataframe(movies)
    df = df.drop_duplicates(subset=["tmdb_id"])
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"[OK] Sauvegardé : {OUTPUT_FILE} ({len(df)} films)")
    print("=" * 60)


if __name__ == "__main__":
    main()
