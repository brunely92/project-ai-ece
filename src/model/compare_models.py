"""
Comparaison de 3 approches de sentiment analysis sur un échantillon d'avis labellisés :
HuggingFace DistilBERT (pré-entraîné) vs TF-IDF+LogisticRegression (custom, entraîné sur
nos données via src.model.train_model) vs TextBlob (lexique/règles).
"""
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
OUTPUT_PATH = REPORTS_DIR / "model_comparison.json"
SAMPLE_SIZE = 2000


def load_sample() -> pd.DataFrame:
    if not DB_PATH.exists():
        raise SystemExit(f"[ERREUR] Base introuvable : {DB_PATH}. Lancez d'abord src.db.import_data")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT review_text, sentiment FROM reviews WHERE sentiment IS NOT NULL", conn
    )
    conn.close()
    n = min(SAMPLE_SIZE, len(df))
    return df.sample(n=n, random_state=42).reset_index(drop=True)


def eval_predictions(y_true, y_pred, elapsed_sec, n):
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, pos_label="positive", zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, pos_label="positive", zero_division=0), 4),
        "f1_score": round(f1_score(y_true, y_pred, pos_label="positive", zero_division=0), 4),
        "total_time_sec": round(elapsed_sec, 2),
        "avg_latency_ms": round(elapsed_sec * 1000 / n, 2),
    }


def run_huggingface(texts):
    from transformers import pipeline

    model_name = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")
    classifier = pipeline("sentiment-analysis", model=model_name, truncation=True, max_length=512)

    preds = []
    start = time.time()
    batch_size = 64
    for i in range(0, len(texts), batch_size):
        batch = [t[:512] for t in texts[i:i + batch_size]]
        results = classifier(batch)
        preds.extend(r["label"].lower() for r in results)
        print(f"  [HuggingFace] {min(i + batch_size, len(texts))}/{len(texts)}")
    elapsed = time.time() - start
    return preds, elapsed


def run_custom(texts):
    model = joblib.load(MODELS_DIR / "tfidf_logreg.joblib")
    vectorizer = joblib.load(MODELS_DIR / "tfidf_vectorizer.joblib")

    start = time.time()
    X = vectorizer.transform(texts)
    preds = list(model.predict(X))
    elapsed = time.time() - start
    return preds, elapsed


def run_textblob(texts):
    from textblob import TextBlob

    start = time.time()
    preds = []
    for t in texts:
        polarity = TextBlob(t).sentiment.polarity
        preds.append("positive" if polarity >= 0 else "negative")
    elapsed = time.time() - start
    return preds, elapsed


def main():
    REPORTS_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print(f"COMPARAISON DE 3 MODELES DE SENTIMENT ANALYSIS — {datetime.now().isoformat()}")
    print("=" * 70)

    df = load_sample()
    texts = df["review_text"].tolist()
    y_true = df["sentiment"].tolist()
    n = len(texts)
    print(f"[INFO] Échantillon : {n} avis labellisés")

    results = {}

    print("\n[1/3] HuggingFace DistilBERT...")
    hf_preds, hf_time = run_huggingface(texts)
    results["huggingface_distilbert"] = eval_predictions(y_true, hf_preds, hf_time, n)

    print("\n[2/3] TF-IDF + LogisticRegression (custom)...")
    custom_preds, custom_time = run_custom(texts)
    results["tfidf_logreg_custom"] = eval_predictions(y_true, custom_preds, custom_time, n)

    print("[3/3] TextBlob...")
    tb_preds, tb_time = run_textblob(texts)
    results["textblob"] = eval_predictions(y_true, tb_preds, tb_time, n)

    print("\n" + "=" * 70)
    print("TABLEAU COMPARATIF")
    print("=" * 70)
    header = f"{'Modèle':<25}{'Accuracy':>10}{'Precision':>11}{'Recall':>9}{'F1':>9}{'Latence(ms)':>14}"
    print(header)
    print("-" * len(header))
    for name, m in results.items():
        print(
            f"{name:<25}{m['accuracy']:>10.4f}{m['precision']:>11.4f}"
            f"{m['recall']:>9.4f}{m['f1_score']:>9.4f}{m['avg_latency_ms']:>14.2f}"
        )

    output = {
        "sample_size": n,
        "generated_at": datetime.now().isoformat(),
        "models": results,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Résultats sauvegardés : {OUTPUT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
