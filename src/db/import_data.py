"""
C4 — Création de la base de données et import du dataset nettoyé
SGBD : SQLite (justification : projet local, léger, sans serveur)
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path("data/movies_reviews.sqlite")
SCHEMA_PATH = Path("src/sql/schema.sql")
PROCESSED_FILE = Path("data/processed/reviews_clean.csv")


def create_database():
    """Crée la base de données à partir du schéma SQL."""
    if not SCHEMA_PATH.exists():
        print(f"[ERREUR] Schéma introuvable : {SCHEMA_PATH}")
        sys.exit(1)

    schema = SCHEMA_PATH.read_text()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.close()
    print(f"[OK] Base de données créée : {DB_PATH}")


def import_reviews(conn: sqlite3.Connection) -> dict:
    """Importe les avis nettoyés dans la table reviews."""
    if not PROCESSED_FILE.exists():
        print(f"[ERREUR] Dataset introuvable : {PROCESSED_FILE}")
        print("         Lancez d'abord : python -m src.transform.clean_dataset")
        sys.exit(1)

    df = pd.read_csv(PROCESSED_FILE)
    imported = 0
    rejected = 0

    for _, row in df.iterrows():
        try:
            conn.execute(
                """INSERT INTO reviews (review_text, sentiment, source, imported_at)
                   VALUES (?, ?, ?, ?)""",
                (
                    row["review_text"],
                    row.get("sentiment") if pd.notna(row.get("sentiment")) else None,
                    row["source"],
                    datetime.now().isoformat(),
                ),
            )
            imported += 1
        except Exception as e:
            print(f"[WARN] Ligne rejetée : {e}")
            rejected += 1

    conn.commit()
    return {"imported": imported, "rejected": rejected}


def import_sources(conn: sqlite3.Connection):
    """Enregistre les sources de collecte."""
    sources = [
        ("csv_imdb", "csv", "https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews", "Dataset IMDB Kaggle"),
        ("api_tmdb", "api", "https://api.themoviedb.org/3/movie/popular", "API TMDB films populaires"),
        ("scraping", "scraping", "https://quotes.toscrape.com", "Scraping citations web"),
    ]
    for name, stype, url, desc in sources:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO sources (name, type, url, description, collected_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, stype, url, desc, datetime.now().isoformat()),
            )
        except Exception as e:
            print(f"[WARN] Source {name} : {e}")
    conn.commit()
    print("[OK] Sources de collecte enregistrées")


def verify_import(conn: sqlite3.Connection):
    """Vérifie le contenu de la base après import."""
    print("\n--- Vérification import ---")
    for table in ["sources", "films", "reviews", "predictions"]:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  Table {table:12s} : {count} lignes")

    cursor = conn.execute(
        "SELECT source, COUNT(*) as nb FROM reviews GROUP BY source ORDER BY nb DESC"
    )
    print("\n  Par source :")
    for row in cursor:
        print(f"    {row[0]:15s} : {row[1]} avis")

    cursor = conn.execute(
        "SELECT sentiment, COUNT(*) as nb FROM reviews WHERE sentiment IS NOT NULL GROUP BY sentiment"
    )
    print("\n  Par sentiment :")
    for row in cursor:
        print(f"    {row[0]:15s} : {row[1]} avis")


def main():
    print("=" * 60)
    print(f"IMPORT BASE DE DONNÉES — {datetime.now().isoformat()}")
    print("=" * 60)

    # Supprimer la base existante pour un import propre
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("[INFO] Base existante supprimée")

    create_database()

    conn = sqlite3.connect(DB_PATH)
    import_sources(conn)
    result = import_reviews(conn)
    print(f"\n[OK] Import terminé : {result['imported']} importés, {result['rejected']} rejetés")

    verify_import(conn)
    conn.close()
    print("=" * 60)


if __name__ == "__main__":
    main()
