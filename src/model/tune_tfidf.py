"""
C8 — Justification expérimentale du paramétrage TF-IDF + Régression Logistique.

Compare plusieurs réglages (ngram_range, max_features) avec EXACTEMENT le protocole
de src/model/train_model.py : split 80/20 stratifié, random_state=42.

Usage :
    python -m src.model.tune_tfidf                 # corpus complet (base SQLite)
    python -m src.model.tune_tfidf --sample 50000  # échantillon stratifié, plus rapide
Sortie : reports/tfidf_tuning.json
"""
import argparse
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
OUT = Path("reports/tfidf_tuning.json")

CONFIGS = [
    ((1, 1), 50000),
    ((1, 2), 50000),
    ((1, 3), 5000),
    ((1, 3), 20000),
    ((1, 3), 50000),   # réglage retenu en production
    ((1, 3), 100000),
]
PROBES = ["not very good", "not good at all", "not bad at all", "waste of time"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=0, help="taille d'échantillon (0 = corpus complet)")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT review_text, sentiment FROM reviews WHERE sentiment IS NOT NULL", conn)
    conn.close()
    if args.sample and args.sample < len(df):
        df, _ = train_test_split(df, train_size=args.sample, random_state=42, stratify=df["sentiment"])
    print(f"[INFO] {len(df)} avis utilisés")

    X_tr, X_te, y_tr, y_te = train_test_split(
        df["review_text"], df["sentiment"], test_size=0.2, random_state=42, stratify=df["sentiment"]
    )
    results = []
    for ngram, mf in CONFIGS:
        t0 = time.time()
        vec = TfidfVectorizer(max_features=mf, ngram_range=ngram)
        model = LogisticRegression(max_iter=1000).fit(vec.fit_transform(X_tr), y_tr)
        acc = accuracy_score(y_te, model.predict(vec.transform(X_te)))
        probes = {p: str(model.predict(vec.transform([p]))[0]) for p in PROBES}
        row = {
            "ngram_range": list(ngram), "max_features": mf,
            "accuracy": round(acc, 4), "n_iter": int(model.n_iter_[0]),
            "seconds": round(time.time() - t0, 1), "probes": probes,
        }
        results.append(row)
        print(row, flush=True)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"generated_at": datetime.now().isoformat(),
                               "n_reviews": len(df), "results": results}, indent=2), encoding="utf-8")
    print(f"[OK] Résultats : {OUT}")


if __name__ == "__main__":
    main()
