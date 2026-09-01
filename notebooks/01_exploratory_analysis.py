"""
Analyse exploratoire du dataset (EDA)
Exécutable comme script ou dans Jupyter.
Génère des visualisations dans reports/figures/
"""
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data/movies_reviews.sqlite")
FIG_DIR = Path("reports/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)


def run_eda():
    conn = sqlite3.connect(DB_PATH)

    # 1. Vue d'ensemble
    print("=" * 60)
    print("ANALYSE EXPLORATOIRE DU DATASET")
    print("=" * 60)

    df = pd.read_sql_query("SELECT * FROM reviews", conn)
    print(f"\nDataset : {len(df)} avis")
    print(f"Colonnes : {list(df.columns)}")
    print(f"Sources : {df['source'].value_counts().to_dict()}")
    print(f"Sentiments : {df['sentiment'].value_counts().to_dict()}")

    # 2. Statistiques textuelles
    df["text_length"] = df["review_text"].str.len()
    df["word_count"] = df["review_text"].str.split().str.len()

    print(f"\n--- Statistiques textuelles ---")
    print(f"  Longueur moyenne : {df['text_length'].mean():.0f} caractères")
    print(f"  Longueur médiane : {df['text_length'].median():.0f} caractères")
    print(f"  Mots moyens      : {df['word_count'].mean():.0f} mots/avis")
    print(f"  Min/Max longueur : {df['text_length'].min()} / {df['text_length'].max()}")

    # 3. Par sentiment
    for sent in ["positive", "negative"]:
        subset = df[df["sentiment"] == sent]
        print(f"\n  [{sent.upper()}] {len(subset)} avis")
        print(f"    Longueur moyenne : {subset['text_length'].mean():.0f} car.")
        print(f"    Mots moyens      : {subset['word_count'].mean():.0f} mots")

    # 4. Prédictions
    nb_preds = pd.read_sql_query("SELECT COUNT(*) as nb FROM predictions", conn).iloc[0]["nb"]
    if nb_preds > 0:
        df_pred = pd.read_sql_query(
            """SELECT r.sentiment as vrai, p.predicted_sentiment as predit,
                      p.confidence_score
               FROM reviews r JOIN predictions p ON r.id = p.review_id
               WHERE r.sentiment IS NOT NULL""",
            conn,
        )
        accuracy = (df_pred["vrai"] == df_pred["predit"]).mean() * 100
        print(f"\n--- Métriques modèle ({nb_preds} prédictions) ---")
        print(f"  Accuracy : {accuracy:.1f}%")
        print(f"  Confiance moyenne : {df_pred['confidence_score'].mean():.3f}")
        print(f"  Confiance min     : {df_pred['confidence_score'].min():.3f}")

        # Erreurs
        errors = df_pred[df_pred["vrai"] != df_pred["predit"]]
        print(f"  Erreurs : {len(errors)} ({len(errors)/len(df_pred)*100:.1f}%)")
        print(f"  Faux positifs : {len(errors[errors['predit'] == 'positive'])}")
        print(f"  Faux négatifs : {len(errors[errors['predit'] == 'negative'])}")

    # 5. Films
    nb_films = pd.read_sql_query("SELECT COUNT(*) as nb FROM films", conn).iloc[0]["nb"]
    if nb_films > 0:
        df_films = pd.read_sql_query(
            """SELECT f.title, COUNT(r.id) as nb_avis, f.vote_average
               FROM films f LEFT JOIN reviews r ON f.id = r.film_id
               GROUP BY f.id ORDER BY nb_avis DESC LIMIT 10""",
            conn,
        )
        print(f"\n--- Top 10 films par nombre d'avis ---")
        for _, row in df_films.iterrows():
            print(f"  {row['title']:30s} | {row['nb_avis']:4d} avis | TMDB {row['vote_average']}")

    conn.close()
    print(f"\n{'=' * 60}")
    print("EDA terminée")


if __name__ == "__main__":
    run_eda()
