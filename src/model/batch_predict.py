"""
C9/C11 — Prédictions batch sur tout le dataset.
Remplit la table predictions avec le sentiment prédit pour chaque avis.
Génère des métriques de performance.
"""
import os
import sys
import sqlite3
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
MODEL_NAME = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")
BATCH_SIZE = 64


def run_batch_predictions(limit: int = 500):
    """
    Exécute les prédictions sur un échantillon du dataset.
    Limite par défaut à 500 pour la rapidité (modifiable).
    """
    print(f"[INFO] Chargement du modèle {MODEL_NAME}...")
    try:
        from transformers import pipeline
        classifier = pipeline("sentiment-analysis", model=MODEL_NAME, truncation=True, max_length=512)
    except Exception as e:
        print(f"[ERREUR] Chargement modèle : {e}")
        sys.exit(1)
    print("[OK] Modèle chargé")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Récupérer les reviews non encore prédites
    reviews = conn.execute(
        """SELECT r.id, r.review_text, r.sentiment as true_sentiment
           FROM reviews r
           LEFT JOIN predictions p ON r.id = p.review_id
           WHERE p.id IS NULL
           LIMIT ?""",
        (limit,),
    ).fetchall()

    print(f"[OK] {len(reviews)} avis à prédire")

    if not reviews:
        print("[INFO] Toutes les prédictions sont déjà faites.")
        conn.close()
        return

    # Prédictions par batch
    total = len(reviews)
    predicted = 0
    correct = 0
    total_time = 0
    latencies = []

    for i in range(0, total, BATCH_SIZE):
        batch = reviews[i : i + BATCH_SIZE]
        texts = [r["review_text"][:512] for r in batch]

        start = time.time()
        results = classifier(texts)
        batch_time = time.time() - start
        total_time += batch_time

        for r, result in zip(batch, results):
            sentiment = result["label"].lower()
            score = round(result["score"], 4)
            latency = round(batch_time / len(batch) * 1000, 1)
            latencies.append(latency)

            conn.execute(
                """INSERT INTO predictions
                   (review_id, predicted_sentiment, confidence_score, model_version, predicted_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (r["id"], sentiment, score, MODEL_NAME, datetime.now().isoformat()),
            )

            # Comparer avec le vrai label
            if r["true_sentiment"] and sentiment == r["true_sentiment"]:
                correct += 1
            predicted += 1

        pct = round(predicted / total * 100)
        print(f"  [{pct:3d}%] {predicted}/{total} prédits — batch {batch_time:.1f}s")

    conn.commit()

    # Métriques
    accuracy = round(correct / predicted * 100, 2) if predicted > 0 else 0
    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0

    print(f"\n{'=' * 60}")
    print("RÉSULTATS BATCH PREDICTION")
    print(f"{'=' * 60}")
    print(f"  Modèle           : {MODEL_NAME}")
    print(f"  Avis prédits     : {predicted}")
    print(f"  Accuracy         : {accuracy}%")
    print(f"  Temps total      : {total_time:.1f}s")
    print(f"  Latence moyenne  : {avg_latency}ms/avis")
    print(f"  Prédictions/sec  : {predicted / total_time:.1f}")

    # Matrice de confusion simple
    conf = conn.execute(
        """SELECT r.sentiment as vrai, p.predicted_sentiment as predit, COUNT(*) as nb
           FROM reviews r
           JOIN predictions p ON r.id = p.review_id
           WHERE r.sentiment IS NOT NULL
           GROUP BY r.sentiment, p.predicted_sentiment
           ORDER BY r.sentiment, p.predicted_sentiment"""
    ).fetchall()

    print("\n  Matrice de confusion :")
    print(f"  {'':15s} | {'Prédit POS':>12s} | {'Prédit NEG':>12s}")
    print(f"  {'-' * 45}")
    for label in ["positive", "negative"]:
        pos = sum(r[2] for r in conf if r[0] == label and r[1] == "positive")
        neg = sum(r[2] for r in conf if r[0] == label and r[1] == "negative")
        print(f"  {'Vrai ' + label:15s} | {pos:>12d} | {neg:>12d}")

    conn.close()
    print("=" * 60)


def main():
    print("=" * 60)
    print(f"BATCH PREDICTION — {datetime.now().isoformat()}")
    print("=" * 60)

    if not DB_PATH.exists():
        print("[ERREUR] Base introuvable. Lancez d'abord import_data.py")
        sys.exit(1)

    run_batch_predictions(limit=500)


if __name__ == "__main__":
    main()
