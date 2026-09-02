"""
C5/C9 — API REST complète
Endpoints données + modèle IA + monitoring + batch + comparaison modèles
"""
import os
import re
import sqlite3
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.api.middleware import MonitoringMiddleware

load_dotenv()

DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
API_KEY = os.getenv("API_SECRET_KEY", "dev-key-change-me")

app = FastAPI(
    title="SentimentFlick — API Analyse de Sentiment",
    description=(
        "API REST pour l'analyse de sentiment d'avis de films.\n\n"
        "**Fonctionnalités :**\n"
        "- Accès aux données (avis, films, statistiques)\n"
        "- Prédiction de sentiment par IA (HuggingFace DistilBERT)\n"
        "- Analyse batch de plusieurs avis\n"
        "- Comparaison multi-modèles (DistilBERT vs TextBlob)\n"
        "- Métriques de monitoring\n\n"
        "**Authentification :** header `x-api-key`"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Intégrer le middleware de monitoring
app.add_middleware(MonitoringMiddleware)

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Clé API invalide ou manquante")
    return api_key


def get_db():
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Base de données introuvable")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symboles/pictogrammes divers, émojis récents
    "\U00002600-\U000027BF"  # symboles divers, dingbats
    "\U0001F1E6-\U0001F1FF"  # drapeaux (indicateurs régionaux)
    "\U0001F000-\U0001F0FF"  # tuiles mahjong/cartes
    "\U0000FE0F"             # variation selector (rendu emoji)
    "]+",
    flags=re.UNICODE,
)


def strip_emojis(text: str) -> str:
    """Retire les emojis avant l'envoi au modèle (incident fix/incident-encoding :
    certains caractères unicode faisaient planter la prédiction)."""
    cleaned = EMOJI_PATTERN.sub("", text).strip()
    return cleaned if cleaned else text


# ── Modèles Pydantic ──

class PredictRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=5000, description="Texte de l'avis à analyser")

class BatchPredictRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=20, description="Liste de textes (max 20)")

class PredictResponse(BaseModel):
    sentiment: str
    score: float
    model: str
    processing_time_ms: float

class CompareResponse(BaseModel):
    text: str
    models: dict

class WordImpact(BaseModel):
    word: str
    impact: float

class ExplainResponse(BaseModel):
    text: str
    sentiment: str
    score: float
    top_words: list[WordImpact]
    model: str
    processing_time_ms: float


# ── Modèles IA (lazy loading) ──

_hf_model = None
_textblob_available = None


def get_hf_model():
    global _hf_model
    if _hf_model is None:
        from transformers import pipeline
        model_name = os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english")
        _hf_model = pipeline("sentiment-analysis", model=model_name, truncation=True, max_length=512)
        print(f"[OK] Modèle HuggingFace chargé : {model_name}")
    return _hf_model


def get_textblob_prediction(text: str) -> dict:
    """Prédiction avec TextBlob (modèle de comparaison)."""
    global _textblob_available
    if _textblob_available is None:
        try:
            from textblob import TextBlob
            _textblob_available = True
        except ImportError:
            _textblob_available = False

    if not _textblob_available:
        return {"sentiment": "unavailable", "score": 0, "model": "TextBlob (non installé)"}

    from textblob import TextBlob
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    sentiment = "positive" if polarity >= 0 else "negative"
    score = abs(polarity)
    return {"sentiment": sentiment, "score": round(score, 4), "model": "TextBlob"}


_custom_model = None
_custom_vectorizer = None


def get_custom_model():
    """Charge (une seule fois) le modèle custom TF-IDF + LogisticRegression entraîné
    via `python -m src.model.train_model`."""
    global _custom_model, _custom_vectorizer
    if _custom_model is None:
        model_path = Path("models/tfidf_logreg.joblib")
        vectorizer_path = Path("models/tfidf_vectorizer.joblib")
        if not model_path.exists() or not vectorizer_path.exists():
            raise HTTPException(
                status_code=503,
                detail="Modèle custom non entraîné. Lancez : python -m src.model.train_model",
            )
        import joblib

        _custom_model = joblib.load(model_path)
        _custom_vectorizer = joblib.load(vectorizer_path)
        print("[OK] Modèle custom (TF-IDF + LogisticRegression) chargé")
    return _custom_model, _custom_vectorizer


# ══════════════════════════════════════════
# ENDPOINTS DONNÉES (C5)
# ══════════════════════════════════════════

@app.get("/health", tags=["Système"])
def health_check():
    """Vérifie que l'API et la base de données sont opérationnelles."""
    try:
        conn = get_db()
        reviews = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        films = conn.execute("SELECT COUNT(*) FROM films").fetchone()[0]
        predictions = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        conn.close()
        return {
            "status": "ok",
            "database": "connected",
            "tables": {"reviews": reviews, "films": films, "predictions": predictions},
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/reviews", tags=["Données"], dependencies=[Depends(verify_api_key)])
def list_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sentiment: Optional[str] = Query(default=None, description="Filtrer par sentiment"),
):
    """Liste les avis avec pagination et filtre optionnel."""
    conn = get_db()
    query = "SELECT id, review_text, sentiment, source, film_id FROM reviews"
    params = []
    if sentiment:
        query += " WHERE sentiment = ?"
        params.append(sentiment)
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor = conn.execute(query, params)
    reviews = [dict(row) for row in cursor.fetchall()]
    total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    conn.close()
    return {"total": total, "count": len(reviews), "offset": offset, "reviews": reviews}


@app.get("/reviews/{review_id}", tags=["Données"], dependencies=[Depends(verify_api_key)])
def get_review(review_id: int):
    """Récupère un avis avec ses prédictions et son film associé."""
    conn = get_db()
    review = conn.execute(
        "SELECT id, review_text, sentiment, source, film_id FROM reviews WHERE id = ?",
        (review_id,),
    ).fetchone()
    if not review:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Avis #{review_id} introuvable")

    result = dict(review)

    # Ajouter les prédictions
    preds = conn.execute(
        "SELECT predicted_sentiment, confidence_score, model_version, predicted_at FROM predictions WHERE review_id = ?",
        (review_id,),
    ).fetchall()
    result["predictions"] = [dict(p) for p in preds]

    # Ajouter le film si lié
    if result.get("film_id"):
        film = conn.execute("SELECT title, vote_average, genre_ids FROM films WHERE id = ?", (result["film_id"],)).fetchone()
        result["film"] = dict(film) if film else None

    conn.close()
    return result


@app.get("/search", tags=["Données"], dependencies=[Depends(verify_api_key)])
def search_reviews(
    q: str = Query(..., min_length=2, description="Mot-clé de recherche"),
    sentiment: Optional[str] = Query(default=None),
):
    """Recherche dans les avis avec filtre sentiment optionnel."""
    conn = get_db()
    query = "SELECT id, review_text, sentiment, source FROM reviews WHERE review_text LIKE ?"
    params = [f"%{q}%"]
    if sentiment:
        query += " AND sentiment = ?"
        params.append(sentiment)
    query += " LIMIT 20"
    cursor = conn.execute(query, params)
    reviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"query": q, "count": len(reviews), "reviews": reviews}


@app.get("/stats", tags=["Données"], dependencies=[Depends(verify_api_key)])
def get_stats():
    """Statistiques globales enrichies."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    by_sent = conn.execute("SELECT sentiment, COUNT(*) FROM reviews WHERE sentiment IS NOT NULL GROUP BY sentiment").fetchall()
    by_src = conn.execute("SELECT source, COUNT(*) FROM reviews GROUP BY source").fetchall()
    avg_len = conn.execute("SELECT ROUND(AVG(LENGTH(review_text)), 0) FROM reviews").fetchone()[0]
    nb_films = conn.execute("SELECT COUNT(*) FROM films").fetchone()[0]
    nb_linked = conn.execute("SELECT COUNT(*) FROM reviews WHERE film_id IS NOT NULL").fetchone()[0]
    nb_preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]

    accuracy = None
    if nb_preds > 0:
        accuracy = conn.execute(
            """SELECT ROUND(SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
               FROM reviews r JOIN predictions p ON r.id = p.review_id WHERE r.sentiment IS NOT NULL"""
        ).fetchone()[0]

    conn.close()
    return {
        "total_reviews": total,
        "by_sentiment": {r[0]: r[1] for r in by_sent},
        "by_source": {r[0]: r[1] for r in by_src},
        "avg_review_length": avg_len,
        "total_films": nb_films,
        "reviews_linked_to_films": nb_linked,
        "total_predictions": nb_preds,
        "model_accuracy": accuracy,
    }


# ══════════════════════════════════════════
# ENDPOINTS FILMS (C1/C4)
# ══════════════════════════════════════════

@app.get("/films", tags=["Films"], dependencies=[Depends(verify_api_key)])
def list_films(limit: int = Query(default=20, ge=1, le=100)):
    """Liste les films avec nombre d'avis et sentiment agrégé."""
    conn = get_db()
    films = conn.execute(
        """SELECT f.id, f.title, f.vote_average, f.genre_ids, f.release_date,
                  COUNT(r.id) as nb_reviews,
                  ROUND(SUM(CASE WHEN r.sentiment='positive' THEN 1.0 ELSE 0.0 END) / NULLIF(COUNT(r.id),0) * 100, 1) as pct_positive
           FROM films f
           LEFT JOIN reviews r ON f.id = r.film_id
           GROUP BY f.id
           ORDER BY nb_reviews DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return {"count": len(films), "films": [dict(f) for f in films]}


@app.get("/films/{film_id}", tags=["Films"], dependencies=[Depends(verify_api_key)])
def get_film(film_id: int):
    """Détail d'un film avec ses avis."""
    conn = get_db()
    film = conn.execute("SELECT * FROM films WHERE id = ?", (film_id,)).fetchone()
    if not film:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Film #{film_id} introuvable")
    reviews = conn.execute(
        "SELECT id, review_text, sentiment FROM reviews WHERE film_id = ? LIMIT 10",
        (film_id,),
    ).fetchall()
    conn.close()
    return {"film": dict(film), "reviews": [dict(r) for r in reviews]}


# ══════════════════════════════════════════
# ENDPOINTS IA (C9)
# ══════════════════════════════════════════

@app.post("/predict", response_model=PredictResponse, tags=["IA"], dependencies=[Depends(verify_api_key)])
def predict_sentiment(request: PredictRequest):
    """Prédit le sentiment d'un texte (positif/négatif)."""
    if not isinstance(request.text, str):
        raise HTTPException(status_code=422, detail="Le champ 'text' doit être une chaîne de caractères")

    start = time.time()
    model = get_hf_model()
    clean_text = strip_emojis(request.text)
    result = model(clean_text[:512])[0]
    elapsed = (time.time() - start) * 1000

    return PredictResponse(
        sentiment=result["label"].lower(),
        score=round(result["score"], 4),
        model=os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english"),
        processing_time_ms=round(elapsed, 2),
    )


@app.post("/predict/batch", tags=["IA"], dependencies=[Depends(verify_api_key)])
def predict_batch(request: BatchPredictRequest):
    """Prédit le sentiment de plusieurs textes en un appel (max 20)."""
    model = get_hf_model()
    start = time.time()
    results = model([t[:512] for t in request.texts])
    elapsed = (time.time() - start) * 1000

    predictions = []
    for text, result in zip(request.texts, results):
        predictions.append({
            "text": text[:100] + "..." if len(text) > 100 else text,
            "sentiment": result["label"].lower(),
            "score": round(result["score"], 4),
        })

    return {
        "count": len(predictions),
        "processing_time_ms": round(elapsed, 2),
        "predictions": predictions,
    }


@app.post("/predict/compare", tags=["IA"], dependencies=[Depends(verify_api_key)])
def compare_models(request: PredictRequest):
    """Compare la prédiction de HuggingFace vs TextBlob sur le même texte."""
    # HuggingFace
    start = time.time()
    hf_model = get_hf_model()
    hf_result = hf_model(request.text[:512])[0]
    hf_time = (time.time() - start) * 1000

    # TextBlob
    start = time.time()
    tb_result = get_textblob_prediction(request.text)
    tb_time = (time.time() - start) * 1000

    return {
        "text": request.text[:200],
        "models": {
            "huggingface_distilbert": {
                "sentiment": hf_result["label"].lower(),
                "score": round(hf_result["score"], 4),
                "time_ms": round(hf_time, 2),
            },
            "textblob": {
                "sentiment": tb_result["sentiment"],
                "score": tb_result["score"],
                "time_ms": round(tb_time, 2),
            },
        },
        "agreement": hf_result["label"].lower() == tb_result["sentiment"],
    }


@app.post("/predict/explain", response_model=ExplainResponse, tags=["IA"], dependencies=[Depends(verify_api_key)])
def explain_prediction(request: PredictRequest):
    """Prédit le sentiment et identifie les 5 mots les plus influents (méthode d'occlusion :
    on retire chaque mot un par un et on mesure l'impact sur le score de la prédiction d'origine)."""
    start = time.time()
    model = get_hf_model()
    text = request.text[:512]
    words = text.split()

    base_result = model(text)[0]
    base_sentiment = base_result["label"].lower()
    base_score = base_result["score"]

    # Limiter le nombre de mots analysés pour borner le temps de traitement
    max_words = min(len(words), 60)
    variants = []
    for i in range(max_words):
        remaining = words[:i] + words[i + 1:]
        variants.append(" ".join(remaining) if remaining else ".")

    variant_results = model(variants) if variants else []

    impacts = []
    for word, result in zip(words[:max_words], variant_results):
        # Probabilité du label d'origine dans la variante (sans le mot retiré)
        if result["label"].lower() == base_sentiment:
            variant_score = result["score"]
        else:
            variant_score = 1 - result["score"]
        # Impact positif = le mot soutient la prédiction d'origine
        impacts.append({"word": word, "impact": round(base_score - variant_score, 4)})

    top_words = sorted(impacts, key=lambda x: abs(x["impact"]), reverse=True)[:5]
    elapsed = (time.time() - start) * 1000

    return ExplainResponse(
        text=text[:200],
        sentiment=base_sentiment,
        score=round(base_score, 4),
        top_words=[WordImpact(**w) for w in top_words],
        model=os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english"),
        processing_time_ms=round(elapsed, 2),
    )


@app.get("/model/info", tags=["IA"], dependencies=[Depends(verify_api_key)])
def model_info():
    """Informations sur le modèle IA et ses performances mesurées en base."""
    conn = get_db()
    nb_preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    accuracy = None
    if nb_preds > 0:
        accuracy = conn.execute(
            """SELECT ROUND(SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
               FROM reviews r JOIN predictions p ON r.id = p.review_id WHERE r.sentiment IS NOT NULL"""
        ).fetchone()[0]
    conn.close()

    return {
        "model_name": os.getenv("MODEL_NAME", "distilbert-base-uncased-finetuned-sst-2-english"),
        "task": "sentiment-analysis",
        "framework": "HuggingFace Transformers (PyTorch)",
        "parameters": "66M",
        "size_mb": 260,
        "labels": ["positive", "negative"],
        "max_tokens": 512,
        "total_predictions": nb_preds,
        "measured_accuracy_pct": accuracy,
    }


@app.post("/predict/custom", response_model=PredictResponse, tags=["IA"], dependencies=[Depends(verify_api_key)])
def predict_custom(request: PredictRequest):
    """Prédit le sentiment avec le modèle custom TF-IDF + LogisticRegression,
    entraîné sur le corpus multi-sources du projet (voir src/model/train_model.py)."""
    start = time.time()
    model, vectorizer = get_custom_model()
    X = vectorizer.transform([request.text])
    sentiment = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    classes = list(model.classes_)
    score = proba[classes.index(sentiment)]
    elapsed = (time.time() - start) * 1000

    return PredictResponse(
        sentiment=sentiment,
        score=round(float(score), 4),
        model="tfidf_logreg_custom",
        processing_time_ms=round(elapsed, 2),
    )


@app.get("/models/comparison", tags=["IA"], dependencies=[Depends(verify_api_key)])
def models_comparison():
    """Retourne la comparaison HuggingFace vs modèle custom vs TextBlob
    générée par `python -m src.model.compare_models`."""
    comparison_path = Path("reports/model_comparison.json")
    if not comparison_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Comparaison non disponible. Lancez : python -m src.model.compare_models",
        )
    with open(comparison_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════
# ENDPOINTS MONITORING (C20)
# ══════════════════════════════════════════

@app.get("/monitoring/metrics", tags=["Monitoring"], dependencies=[Depends(verify_api_key)])
def get_metrics():
    """Retourne les métriques du modèle et de l'API."""
    conn = get_db()

    nb_preds = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    if nb_preds == 0:
        conn.close()
        return {"status": "no_predictions", "message": "Lancez batch_predict.py d'abord"}

    accuracy = conn.execute(
        """SELECT ROUND(SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
           FROM reviews r JOIN predictions p ON r.id = p.review_id WHERE r.sentiment IS NOT NULL"""
    ).fetchone()[0]

    avg_conf = conn.execute("SELECT ROUND(AVG(confidence_score), 4) FROM predictions").fetchone()[0]
    min_conf = conn.execute("SELECT ROUND(MIN(confidence_score), 4) FROM predictions").fetchone()[0]

    low_conf = conn.execute("SELECT COUNT(*) FROM predictions WHERE confidence_score < 0.6").fetchone()[0]

    confusion = conn.execute(
        """SELECT r.sentiment, p.predicted_sentiment, COUNT(*)
           FROM reviews r JOIN predictions p ON r.id = p.review_id
           WHERE r.sentiment IS NOT NULL
           GROUP BY r.sentiment, p.predicted_sentiment"""
    ).fetchall()

    conn.close()

    matrix = {}
    for true_label, pred_label, count in confusion:
        if true_label not in matrix:
            matrix[true_label] = {}
        matrix[true_label][pred_label] = count

    return {
        "total_predictions": nb_preds,
        "accuracy_pct": accuracy,
        "avg_confidence": avg_conf,
        "min_confidence": min_conf,
        "low_confidence_count": low_conf,
        "confusion_matrix": matrix,
    }


@app.get("/monitoring/logs", tags=["Monitoring"], dependencies=[Depends(verify_api_key)])
def get_logs(limit: int = Query(default=50, ge=1, le=500)):
    """Retourne les N dernières lignes du fichier de log de l'API (logs/api.log)."""
    log_file = Path("logs/api.log")
    if not log_file.exists():
        return {"count": 0, "logs": []}
    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.strip() for line in f if line.strip()]
    last_lines = lines[-limit:]
    return {"count": len(last_lines), "logs": last_lines}


@app.get("/monitoring/alerts", tags=["Monitoring"], dependencies=[Depends(verify_api_key)])
def get_alerts():
    """Retourne les alertes actives (latence > 1000ms, erreurs 5xx) détectées dans les logs récents."""
    from src.api.middleware import ALERT_ENDPOINTS

    log_file = Path("logs/api.log")
    alerts = []
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            recent_lines = f.readlines()[-500:]
        for line in recent_lines:
            if "ALERTE" in line or "| ERROR |" in line:
                alerts.append(line.strip())

    return {
        "active_alerts_count": len(alerts),
        "alerts": alerts[-20:],
        "error_counts_by_endpoint": ALERT_ENDPOINTS,
    }
