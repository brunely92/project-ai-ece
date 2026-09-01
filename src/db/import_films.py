"""
C1/C4 — Import des métadonnées films depuis l'API TMDB en base de données.
Enrichit la table films et lie les reviews aux films via recherche titre.
"""
import os
import sys
import time
import sqlite3
import re
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Mapping genre_id → genre_name (TMDB standard)
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western",
}


def fetch_movies(pages: int = 10) -> list[dict]:
    """Récupère des films depuis TMDB (popular + top_rated)."""
    if not TMDB_API_KEY or TMDB_API_KEY == "replace_with_your_tmdb_api_key":
        print("[WARN] Clé TMDB non configurée — utilisation de données de démonstration")
        return generate_demo_films()

    all_movies = []
    for category in ["popular", "top_rated"]:
        for page in range(1, pages + 1):
            try:
                response = requests.get(
                    f"{TMDB_BASE_URL}/movie/{category}",
                    params={"api_key": TMDB_API_KEY, "language": "en-US", "page": page},
                    timeout=15,
                )
                response.raise_for_status()
                movies = response.json().get("results", [])
                all_movies.extend(movies)
                time.sleep(0.25)
            except Exception as e:
                print(f"[WARN] {category} page {page}: {e}")
                continue
        print(f"[OK] TMDB {category}: {len(all_movies)} films cumulés")

    # Dédoublonner par tmdb_id
    seen = set()
    unique = []
    for m in all_movies:
        if m["id"] not in seen:
            seen.add(m["id"])
            unique.append(m)
    return unique


def generate_demo_films() -> list[dict]:
    """Films de démonstration si pas de clé TMDB."""
    films = [
        {"id": 1, "title": "The Shawshank Redemption", "release_date": "1994-09-23", "vote_average": 8.7, "vote_count": 25000, "popularity": 85.0, "genre_ids": [18, 80], "overview": "A banker convicted of murder forms a friendship over a quarter century.", "original_language": "en"},
        {"id": 2, "title": "The Dark Knight", "release_date": "2008-07-18", "vote_average": 8.5, "vote_count": 30000, "popularity": 90.0, "genre_ids": [28, 80, 18], "overview": "Batman raises the stakes in his war on crime.", "original_language": "en"},
        {"id": 3, "title": "Inception", "release_date": "2010-07-16", "vote_average": 8.4, "vote_count": 34000, "popularity": 88.0, "genre_ids": [28, 878, 12], "overview": "A thief who steals corporate secrets through dream-sharing technology.", "original_language": "en"},
        {"id": 4, "title": "Pulp Fiction", "release_date": "1994-10-14", "vote_average": 8.5, "vote_count": 26000, "popularity": 75.0, "genre_ids": [53, 80], "overview": "The lives of two mob hitmen, a boxer, and a pair of diner bandits intertwine.", "original_language": "en"},
        {"id": 5, "title": "Forrest Gump", "release_date": "1994-07-06", "vote_average": 8.5, "vote_count": 25000, "popularity": 80.0, "genre_ids": [35, 18, 10749], "overview": "The presidencies of Kennedy and Johnson unfold through the perspective of an Alabama man.", "original_language": "en"},
        {"id": 6, "title": "The Matrix", "release_date": "1999-03-31", "vote_average": 8.2, "vote_count": 24000, "popularity": 82.0, "genre_ids": [28, 878], "overview": "A computer programmer discovers the world is a simulation.", "original_language": "en"},
        {"id": 7, "title": "Fight Club", "release_date": "1999-10-15", "vote_average": 8.4, "vote_count": 27000, "popularity": 78.0, "genre_ids": [18], "overview": "An insomniac and a devil-may-care soap maker form an underground fight club.", "original_language": "en"},
        {"id": 8, "title": "The Godfather", "release_date": "1972-03-14", "vote_average": 8.7, "vote_count": 19000, "popularity": 70.0, "genre_ids": [18, 80], "overview": "The aging patriarch of an organized crime dynasty transfers control to his reluctant son.", "original_language": "en"},
        {"id": 9, "title": "Interstellar", "release_date": "2014-11-07", "vote_average": 8.4, "vote_count": 32000, "popularity": 95.0, "genre_ids": [12, 18, 878], "overview": "Explorers travel through a wormhole in space to ensure humanity's survival.", "original_language": "en"},
        {"id": 10, "title": "Titanic", "release_date": "1997-12-19", "vote_average": 7.9, "vote_count": 23000, "popularity": 76.0, "genre_ids": [18, 10749], "overview": "A seventeen-year-old aristocrat falls in love aboard the ill-fated R.M.S. Titanic.", "original_language": "en"},
        {"id": 11, "title": "The Avengers", "release_date": "2012-05-04", "vote_average": 7.7, "vote_count": 29000, "popularity": 92.0, "genre_ids": [28, 12, 878], "overview": "Earth's mightiest heroes must come together to fight a global threat.", "original_language": "en"},
        {"id": 12, "title": "Joker", "release_date": "2019-10-04", "vote_average": 8.2, "vote_count": 22000, "popularity": 85.0, "genre_ids": [80, 53, 18], "overview": "A mentally troubled comedian embarks on a downward spiral of revolution.", "original_language": "en"},
        {"id": 13, "title": "Parasite", "release_date": "2019-05-30", "vote_average": 8.5, "vote_count": 16000, "popularity": 70.0, "genre_ids": [35, 53, 18], "overview": "Greed and class discrimination threaten a symbiotic relationship between families.", "original_language": "ko"},
        {"id": 14, "title": "Gladiator", "release_date": "2000-05-05", "vote_average": 8.1, "vote_count": 16000, "popularity": 72.0, "genre_ids": [28, 18, 12], "overview": "A former Roman General sets out to exact vengeance against the emperor.", "original_language": "en"},
        {"id": 15, "title": "The Lion King", "release_date": "1994-06-24", "vote_average": 8.3, "vote_count": 17000, "popularity": 74.0, "genre_ids": [16, 18, 10751], "overview": "A young lion prince flees his kingdom only to learn the true meaning of responsibility.", "original_language": "en"},
    ]
    return films


def import_films_to_db(films: list[dict]):
    """Insère les films dans la base de données."""
    conn = sqlite3.connect(DB_PATH)
    imported = 0

    for m in films:
        genres = ", ".join(GENRE_MAP.get(g, "Unknown") for g in m.get("genre_ids", []))
        try:
            conn.execute(
                """INSERT OR IGNORE INTO films
                   (tmdb_id, title, original_title, release_date, vote_average,
                    vote_count, popularity, genre_ids, overview, original_language)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    m.get("id"), m.get("title"), m.get("original_title", m.get("title")),
                    m.get("release_date"), m.get("vote_average"), m.get("vote_count"),
                    m.get("popularity"), genres, m.get("overview"),
                    m.get("original_language"),
                ),
            )
            imported += 1
        except Exception as e:
            print(f"[WARN] Film {m.get('title')}: {e}")

    conn.commit()
    print(f"[OK] {imported} films importés")

    # Lier les reviews aux films via recherche de titre dans le texte
    link_reviews_to_films(conn)
    conn.close()


def link_reviews_to_films(conn: sqlite3.Connection):
    """Lie les reviews aux films si le titre du film apparaît dans le texte."""
    films = conn.execute("SELECT id, title FROM films").fetchall()
    linked = 0

    for film_id, title in films:
        # Chercher le titre dans les reviews (insensible à la casse)
        clean_title = title.replace("'", "''")
        try:
            cursor = conn.execute(
                f"""UPDATE reviews SET film_id = ?
                    WHERE film_id IS NULL
                    AND LOWER(review_text) LIKE LOWER(?)""",
                (film_id, f"%{title.lower()}%"),
            )
            count = cursor.rowcount
            if count > 0:
                linked += count
                print(f"  → {title}: {count} avis liés")
        except Exception:
            pass

    conn.commit()
    print(f"[OK] {linked} avis liés à des films")


def main():
    print("=" * 60)
    print(f"IMPORT FILMS TMDB — {datetime.now().isoformat()}")
    print("=" * 60)

    if not DB_PATH.exists():
        print("[ERREUR] Base de données introuvable. Lancez d'abord import_data.py")
        sys.exit(1)

    films = fetch_movies(pages=5)
    print(f"[OK] {len(films)} films récupérés")

    import_films_to_db(films)

    # Vérification
    conn = sqlite3.connect(DB_PATH)
    nb_films = conn.execute("SELECT COUNT(*) FROM films").fetchone()[0]
    nb_linked = conn.execute("SELECT COUNT(*) FROM reviews WHERE film_id IS NOT NULL").fetchone()[0]
    conn.close()

    print(f"\n--- Résultat ---")
    print(f"  Films en base    : {nb_films}")
    print(f"  Avis liés à un film : {nb_linked}")
    print("=" * 60)


if __name__ == "__main__":
    main()
