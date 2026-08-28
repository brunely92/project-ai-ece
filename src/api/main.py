"""
C5 — API REST de mise à disposition des données
C9 — API exposant le modèle d'intelligence artificielle

Framework : FastAPI
Auth : API key via header x-api-key
Documentation : OpenAPI auto (/docs)
"""
import os
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──
DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
API_KEY = os.getenv("API_SECRET_KEY", "dev-key-change-me")

# ── App FastAPI ──
app = FastAPI(
    title="API Analyse de Sentiment — Avis de Films",
    description="API REST pour accéder aux données et prédire le sentiment d'avis de films.",
    version="1.0.0",
)

# ── Auth ──
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    """Vérifie la clé API fournie dans le header x-api-key."""
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Clé API invalide ou manquante")
    return api_key


# ── DB helper ──
def get_db():
    """Retourne une connexion SQLite."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Base de données introuvable")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Modèles Pydantic ──
class PredictRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=5000, description="Texte de l'avis à analyser")


class PredictResponse(BaseModel):
    sentiment: str
    score: float
    model: str
    processing_time_ms: float


class ReviewOut(BaseModel):
    id: int
    review_text: str
    sentiment: Optional[str]
    source: str


# ── C5 : Endpoints données ──

@app.get("/health", tags=["Système"])
def health_check():
    """Vérifie que l'API et la base de données sont opérationnelles."""
    try:
        conn = get_db()
        cursor = conn.execute("SELECT COUNT(*) FROM reviews")
        count = cursor.fetchone()[0]
        conn.close()
        return {"status": "ok", "database": "connected", "reviews_count": count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/reviews", tags=["Données"], dependencies=[Depends(verify_api_key)])
def list_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Liste les avis avec pagination."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT id, review_text, sentiment, source FROM reviews LIMIT ? OFFSET ?",
        (limit, offset),
    )
    reviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"count": len(reviews), "offset": offset, "reviews": reviews}


@app.get("/reviews/{review_id}", tags=["Données"], dependencies=[Depends(verify_api_key)])
def get_review(review_id: int):
    """Récupère un avis par son ID."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT id, review_text, sentiment, source FROM reviews WHERE id = ?",
        (review_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Avis #{review_id} introuvable")
    return dict(row)


@app.get("/search", tags=["Données"], dependencies=[Depends(verify_api_key)])
def search_reviews(q: str = Query(..., min_length=2, description="Mot-clé de recherche")):
    """Recherche des avis contenant un mot-clé."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT id, review_text, sentiment, source FROM reviews WHERE review_text LIKE ? LIMIT 20",
        (f"%{q}%",),
    )
    reviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"query": q, "count": len(reviews), "reviews": reviews}


@app.get("/stats", tags=["Données"], dependencies=[Depends(verify_api_key)])
def get_stats():
    """Statistiques globales du dataset."""
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    by_sentiment = conn.execute(
        "SELECT sentiment, COUNT(*) as nb FROM reviews WHERE sentiment IS NOT NULL GROUP BY sentiment"
    ).fetchall()
    by_source = conn.execute(
        "SELECT source, COUNT(*) as nb FROM reviews GROUP BY source"
    ).fetchall()
    avg_len = conn.execute(
        "SELECT ROUND(AVG(LENGTH(review_text)), 0) FROM reviews"
    ).fetchone()[0]

    conn.close()
    return {
        "total_reviews": total,
        "by_sentiment": {row["sentiment"]: row["nb"] for row in by_sentiment},
        "by_source": {row["source"]: row["nb"] for row in by_source},
        "avg_review_length": avg_len,
    }


# ── C9 : Endpoint modèle IA ──

# Chargement lazy du modèle
_model = None


def get_model():
    """Charge le modèle HuggingFace une seule fois (singleton)."""
    global _model
    if _model is None:
        try:
            from transformers import pipeline
            model_name = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")
            _model = pipeline("sentiment-analysis", model=model_name)
            print(f"[OK] Modèle chargé : {model_name}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur chargement modèle : {e}")
    return _model


@app.post("/predict", response_model=PredictResponse, tags=["IA"], dependencies=[Depends(verify_api_key)])
def predict_sentiment(request: PredictRequest):
    """
    Prédit le sentiment d'un texte (positif/négatif).
    Utilise le modèle HuggingFace distilbert-base-uncased-finetuned-sst-2-english.
    """
    # Validation type (C21 - prévention incident)
    if not isinstance(request.text, str):
        raise HTTPException(status_code=422, detail="Le champ 'text' doit être une chaîne de caractères")

    start = time.time()
    model = get_model()
    result = model(request.text[:512])[0]  # Tronquer à 512 tokens
    elapsed = (time.time() - start) * 1000

    return PredictResponse(
        sentiment=result["label"].lower(),
        score=round(result["score"], 4),
        model=os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english"),
        processing_time_ms=round(elapsed, 2),
    )
