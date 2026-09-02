"""
Entraînement d'un modèle custom sur nos données — TF-IDF + Régression Logistique.
Complète le modèle HuggingFace pré-entraîné (voir docs/benchmark.md) par un modèle
entraîné spécifiquement sur le corpus multi-sources du projet.
"""
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports")
MODEL_PATH = MODELS_DIR / "tfidf_logreg.joblib"
VECTORIZER_PATH = MODELS_DIR / "tfidf_vectorizer.joblib"
METRICS_PATH = REPORTS_DIR / "model_evaluation.json"


def load_labeled_reviews() -> pd.DataFrame:
    if not DB_PATH.exists():
        raise SystemExit(f"[ERREUR] Base introuvable : {DB_PATH}. Lancez d'abord src.db.import_data")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT review_text, sentiment FROM reviews WHERE sentiment IS NOT NULL", conn
    )
    conn.close()
    return df


def main():
    MODELS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print(f"ENTRAINEMENT MODELE CUSTOM — TF-IDF + LogisticRegression — {datetime.now().isoformat()}")
    print("=" * 70)

    df = load_labeled_reviews()
    print(f"[INFO] {len(df)} avis labellisés chargés depuis {DB_PATH}")

    X, y = df["review_text"], df["sentiment"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[INFO] Split 80/20 stratifié : {len(X_train)} train / {len(X_test)} test")

    vectorizer = TfidfVectorizer(max_features=50000, ngram_range=(1, 3))
    model = LogisticRegression(max_iter=1000)

    print("[INFO] Vectorisation TF-IDF (max_features=50000, ngrams 1-3)...")
    start = time.time()
    X_train_vec = vectorizer.fit_transform(X_train)
    vec_time = time.time() - start
    print(f"[OK] Vectorisation terminée en {vec_time:.1f}s — vocabulaire : {len(vectorizer.vocabulary_)} termes")

    print("[INFO] Entraînement LogisticRegression...")
    start = time.time()
    model.fit(X_train_vec, y_train)
    train_time = time.time() - start
    print(f"[OK] Entraînement terminé en {train_time:.1f}s")

    X_test_vec = vectorizer.transform(X_test)
    y_pred = model.predict(X_test_vec)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, pos_label="positive")
    recall = recall_score(y_test, y_pred, pos_label="positive")
    f1 = f1_score(y_test, y_pred, pos_label="positive")
    report = classification_report(y_test, y_pred, output_dict=True)

    print("\n" + "=" * 70)
    print("RESULTATS SUR LE JEU DE TEST")
    print("=" * 70)
    print(f"  Accuracy  : {accuracy:.4f}")
    print(f"  Precision : {precision:.4f}")
    print(f"  Recall    : {recall:.4f}")
    print(f"  F1-score  : {f1:.4f}")
    print()
    print(classification_report(y_test, y_pred))

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    print(f"[OK] Modèle sauvegardé     : {MODEL_PATH}")
    print(f"[OK] Vectorizer sauvegardé : {VECTORIZER_PATH}")

    metrics = {
        "model": "TF-IDF (max_features=50000, ngram_range=(1,3)) + LogisticRegression(max_iter=1000)",
        "trained_at": datetime.now().isoformat(),
        "n_samples_total": len(df),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "vocabulary_size": len(vectorizer.vocabulary_),
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "classification_report": report,
        "vectorization_time_sec": round(vec_time, 2),
        "training_time_sec": round(train_time, 2),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[OK] Métriques sauvegardées : {METRICS_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
