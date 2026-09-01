"""
C1 — Collecte depuis l'API OMDB (Open Movie Database)
Source : https://www.omdbapi.com/ (clé gratuite, 1000 requêtes/jour)

Enrichit les films avec : réalisateur, acteurs, awards, box office,
runtime, rated, metascore, imdb rating, imdb votes.
"""
import os
import sys
import time
import csv
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = RAW_DIR / "omdb_movies_raw.csv"
LOG_FILE = Path("logs/collect_omdb.log")
LOG_FILE.parent.mkdir(exist_ok=True)

OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
OMDB_BASE_URL = "http://www.omdbapi.com/"

# Films à enrichir (titres connus du dataset IMDB)
TARGET_FILMS = [
    "The Shawshank Redemption", "The Dark Knight", "Inception", "Pulp Fiction",
    "Forrest Gump", "The Matrix", "Fight Club", "The Godfather", "Interstellar",
    "Titanic", "The Avengers", "Joker", "Parasite", "Gladiator", "The Lion King",
    "Schindler's List", "The Lord of the Rings: The Return of the King",
    "Star Wars", "Jurassic Park", "The Silence of the Lambs", "Goodfellas",
    "Saving Private Ryan", "The Green Mile", "Terminator 2: Judgment Day",
    "Back to the Future", "The Prestige", "The Departed", "Whiplash",
    "Django Unchained", "The Wolf of Wall Street", "Mad Max: Fury Road",
    "Blade Runner 2049", "Get Out", "Black Panther", "Avengers: Endgame",
    "Spirited Away", "Coco", "Inside Out", "Toy Story", "Finding Nemo",
]


def log(level: str, msg: str):
    """Journalise avec timestamp dans fichier et console."""
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{ts} | {level:5s} | {msg}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if level in ("ERROR", "WARN"):
        print(f"[{level}] {msg}")


def fetch_movie(title: str, retries: int = 3) -> dict | None:
    """
    Récupère les détails d'un film depuis OMDB avec retry et backoff.
    """
    for attempt in range(1, retries + 1):
        try:
            params = {"apikey": OMDB_API_KEY, "t": title, "plot": "short", "r": "json"}
            response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get("Response") == "True":
                log("INFO", f"OK {title} (attempt {attempt})")
                return data
            else:
                log("WARN", f"OMDB not found: {title} — {data.get('Error')}")
                return None

        except requests.Timeout:
            log("WARN", f"Timeout {title} (attempt {attempt}/{retries})")
            time.sleep(2 ** attempt)
        except requests.HTTPError as e:
            log("ERROR", f"HTTP {e.response.status_code} {title}")
            return None
        except requests.RequestException as e:
            log("ERROR", f"Network error {title}: {e}")
            time.sleep(2 ** attempt)

    log("ERROR", f"Failed after {retries} retries: {title}")
    return None


def parse_movie(data: dict) -> dict:
    """Extrait les champs utiles de la réponse OMDB."""
    def safe_int(val):
        try:
            return int(val.replace(",", "").replace("N/A", "0"))
        except (ValueError, AttributeError):
            return 0

    def safe_float(val):
        try:
            return float(val.replace("N/A", "0"))
        except (ValueError, AttributeError):
            return 0.0

    return {
        "title": data.get("Title", ""),
        "year": data.get("Year", ""),
        "rated": data.get("Rated", ""),
        "runtime": data.get("Runtime", "").replace(" min", ""),
        "genre": data.get("Genre", ""),
        "director": data.get("Director", ""),
        "actors": data.get("Actors", ""),
        "plot": data.get("Plot", ""),
        "language": data.get("Language", ""),
        "country": data.get("Country", ""),
        "awards": data.get("Awards", ""),
        "imdb_rating": safe_float(data.get("imdbRating", "0")),
        "imdb_votes": safe_int(data.get("imdbVotes", "0")),
        "metascore": safe_int(data.get("Metascore", "0")),
        "box_office": data.get("BoxOffice", "N/A"),
        "imdb_id": data.get("imdbID", ""),
        "type": data.get("Type", ""),
        "source": "omdb_api",
        "collected_at": datetime.now().isoformat(),
    }


def generate_demo_omdb() -> list[dict]:
    """Données OMDB de démonstration si pas de clé API."""
    demo = [
        {"title": "The Shawshank Redemption", "year": "1994", "rated": "R", "runtime": "142", "genre": "Drama", "director": "Frank Darabont", "actors": "Tim Robbins, Morgan Freeman", "plot": "Over the course of several years, two convicts form a friendship.", "language": "English", "country": "United States", "awards": "Nominated for 7 Oscars", "imdb_rating": 9.3, "imdb_votes": 2800000, "metascore": 82, "box_office": "$28,767,189", "imdb_id": "tt0111161", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "The Dark Knight", "year": "2008", "rated": "PG-13", "runtime": "152", "genre": "Action, Crime, Drama", "director": "Christopher Nolan", "actors": "Christian Bale, Heath Ledger", "plot": "Batman raises the stakes in his war on crime.", "language": "English", "country": "United States, United Kingdom", "awards": "Won 2 Oscars", "imdb_rating": 9.0, "imdb_votes": 2700000, "metascore": 84, "box_office": "$533,345,358", "imdb_id": "tt0468569", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "Inception", "year": "2010", "rated": "PG-13", "runtime": "148", "genre": "Action, Adventure, Sci-Fi", "director": "Christopher Nolan", "actors": "Leonardo DiCaprio, Joseph Gordon-Levitt", "plot": "A thief who steals corporate secrets through dream-sharing technology.", "language": "English, Japanese, French", "country": "United States, United Kingdom", "awards": "Won 4 Oscars", "imdb_rating": 8.8, "imdb_votes": 2400000, "metascore": 74, "box_office": "$292,576,195", "imdb_id": "tt1375666", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "Pulp Fiction", "year": "1994", "rated": "R", "runtime": "154", "genre": "Crime, Drama", "director": "Quentin Tarantino", "actors": "John Travolta, Uma Thurman, Samuel L. Jackson", "plot": "The lives of two mob hitmen, a boxer, and a pair of diner bandits intertwine.", "language": "English, Spanish, French", "country": "United States", "awards": "Won 1 Oscar", "imdb_rating": 8.9, "imdb_votes": 2100000, "metascore": 94, "box_office": "$107,928,762", "imdb_id": "tt0110912", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "Forrest Gump", "year": "1994", "rated": "PG-13", "runtime": "142", "genre": "Drama, Romance", "director": "Robert Zemeckis", "actors": "Tom Hanks, Robin Wright, Gary Sinise", "plot": "The history of the United States from the 1950s to the 70s unfolds from the perspective of an Alabama man.", "language": "English", "country": "United States", "awards": "Won 6 Oscars", "imdb_rating": 8.8, "imdb_votes": 2100000, "metascore": 82, "box_office": "$330,455,270", "imdb_id": "tt0109830", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "The Matrix", "year": "1999", "rated": "R", "runtime": "136", "genre": "Action, Sci-Fi", "director": "Lana Wachowski, Lilly Wachowski", "actors": "Keanu Reeves, Laurence Fishburne", "plot": "A computer programmer discovers that reality as he knows it is a simulation.", "language": "English", "country": "United States, Australia", "awards": "Won 4 Oscars", "imdb_rating": 8.7, "imdb_votes": 1900000, "metascore": 73, "box_office": "$171,479,930", "imdb_id": "tt0133093", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "Fight Club", "year": "1999", "rated": "R", "runtime": "139", "genre": "Drama", "director": "David Fincher", "actors": "Brad Pitt, Edward Norton, Helena Bonham Carter", "plot": "An insomniac office worker and a devil-may-care soap maker form an underground fight club.", "language": "English", "country": "United States, Germany", "awards": "Nominated for 1 Oscar", "imdb_rating": 8.8, "imdb_votes": 2200000, "metascore": 66, "box_office": "$37,030,102", "imdb_id": "tt0137523", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "The Godfather", "year": "1972", "rated": "R", "runtime": "175", "genre": "Crime, Drama", "director": "Francis Ford Coppola", "actors": "Marlon Brando, Al Pacino, James Caan", "plot": "The aging patriarch of an organized crime dynasty transfers control to his reluctant son.", "language": "English, Italian, Latin", "country": "United States", "awards": "Won 3 Oscars", "imdb_rating": 9.2, "imdb_votes": 1900000, "metascore": 100, "box_office": "$136,381,073", "imdb_id": "tt0068646", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "Interstellar", "year": "2014", "rated": "PG-13", "runtime": "169", "genre": "Adventure, Drama, Sci-Fi", "director": "Christopher Nolan", "actors": "Matthew McConaughey, Anne Hathaway", "plot": "Explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", "language": "English", "country": "United States, United Kingdom, Canada", "awards": "Won 1 Oscar", "imdb_rating": 8.7, "imdb_votes": 1900000, "metascore": 74, "box_office": "$188,020,017", "imdb_id": "tt0816692", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
        {"title": "Titanic", "year": "1997", "rated": "PG-13", "runtime": "194", "genre": "Drama, Romance", "director": "James Cameron", "actors": "Leonardo DiCaprio, Kate Winslet", "plot": "A seventeen-year-old aristocrat falls in love aboard the ill-fated R.M.S. Titanic.", "language": "English, Swedish, Italian, French", "country": "United States, Mexico", "awards": "Won 11 Oscars", "imdb_rating": 7.9, "imdb_votes": 1200000, "metascore": 75, "box_office": "$674,292,608", "imdb_id": "tt0120338", "type": "movie", "source": "omdb_demo", "collected_at": datetime.now().isoformat()},
    ]
    return demo


def main():
    print("=" * 60)
    print(f"COLLECTE OMDB API — {datetime.now().isoformat()}")
    print("=" * 60)

    if OMDB_API_KEY and OMDB_API_KEY != "replace_with_your_omdb_api_key":
        print(f"[INFO] Clé OMDB détectée — collecte de {len(TARGET_FILMS)} films")
        movies = []
        for i, title in enumerate(TARGET_FILMS):
            data = fetch_movie(title)
            if data:
                movies.append(parse_movie(data))
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(TARGET_FILMS)}] films traités")
            time.sleep(0.5)  # Rate limiting
    else:
        print("[WARN] Clé OMDB non configurée — données de démonstration")
        print("       Pour une clé gratuite : https://www.omdbapi.com/apikey.aspx")
        movies = generate_demo_omdb()

    if not movies:
        print("[ERREUR] Aucun film récupéré")
        sys.exit(1)

    # Sauvegarder en CSV
    import pandas as pd
    df = pd.DataFrame(movies)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\n[OK] {len(movies)} films sauvegardés dans {OUTPUT_FILE}")
    print(f"     Colonnes : {list(df.columns)}")
    log("INFO", f"Collecte terminée : {len(movies)} films")
    print("=" * 60)


if __name__ == "__main__":
    main()
