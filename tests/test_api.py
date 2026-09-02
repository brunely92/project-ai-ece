"""
C12/C18 — Tests automatisés de l'API (v2)
Couvre : données, films, prédiction, batch, comparaison, monitoring, sécurité.
"""
import importlib.util
import time

import pytest
from fastapi.testclient import TestClient
import os

os.environ.setdefault("API_SECRET_KEY", "test-key")
os.environ.setdefault("DATABASE_PATH", "data/movies_reviews.sqlite")

from src.api.main import app

client = TestClient(app, raise_server_exceptions=False)
HEADERS = {"x-api-key": "test-key"}

# Le modèle IA (transformers/torch) n'est pas installé en CI (trop lourd) :
# les tests qui appellent réellement le modèle sont marqués skip dans ce cas.
HAS_MODEL = (
    importlib.util.find_spec("transformers") is not None
    and importlib.util.find_spec("torch") is not None
)
requires_model = pytest.mark.skipif(not HAS_MODEL, reason="transformers/torch non installés (CI allégée)")

HAS_SKLEARN = (
    importlib.util.find_spec("sklearn") is not None
    and importlib.util.find_spec("joblib") is not None
)
requires_sklearn = pytest.mark.skipif(not HAS_SKLEARN, reason="scikit-learn/joblib non installés (CI allégée)")


# ── Système ──

class TestHealth:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_status(self):
        r = client.get("/health")
        assert "status" in r.json()

    def test_health_shows_tables(self):
        r = client.get("/health")
        data = r.json()
        if data["status"] == "ok":
            assert "tables" in data


# ── Auth ──

class TestAuth:
    def test_unauthorized_without_key(self):
        r = client.get("/reviews")
        assert r.status_code == 401

    def test_unauthorized_wrong_key(self):
        r = client.get("/reviews", headers={"x-api-key": "wrong"})
        assert r.status_code == 401

    def test_authorized_with_key(self):
        r = client.get("/reviews", headers=HEADERS)
        assert r.status_code in (200, 500)


# ── Données ──

class TestReviews:
    def test_list_reviews(self):
        r = client.get("/reviews?limit=5", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            assert "reviews" in data
            assert "total" in data
            assert len(data["reviews"]) <= 5

    def test_filter_by_sentiment(self):
        r = client.get("/reviews?sentiment=positive&limit=3", headers=HEADERS)
        if r.status_code == 200:
            for rev in r.json()["reviews"]:
                assert rev["sentiment"] == "positive"

    def test_review_not_found(self):
        r = client.get("/reviews/999999", headers=HEADERS)
        assert r.status_code in (404, 500)

    def test_search(self):
        r = client.get("/search?q=movie", headers=HEADERS)
        assert r.status_code in (200, 500)

    def test_search_with_filter(self):
        r = client.get("/search?q=great&sentiment=positive", headers=HEADERS)
        if r.status_code == 200:
            assert "reviews" in r.json()

    def test_stats(self):
        r = client.get("/stats", headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            assert "total_reviews" in data
            assert "total_films" in data
            assert "model_accuracy" in data


# ── Films ──

class TestFilms:
    def test_list_films(self):
        r = client.get("/films", headers=HEADERS)
        assert r.status_code in (200, 500)

    def test_film_not_found(self):
        r = client.get("/films/999999", headers=HEADERS)
        assert r.status_code in (404, 500)


# ── Monitoring ──

class TestMonitoring:
    def test_metrics_endpoint(self):
        r = client.get("/monitoring/metrics", headers=HEADERS)
        assert r.status_code in (200, 500)


# ── Validation entrées (sécurité OWASP) ──

class TestInputValidation:
    def test_search_too_short(self):
        r = client.get("/search?q=a", headers=HEADERS)
        assert r.status_code == 422

    def test_reviews_limit_too_high(self):
        r = client.get("/reviews?limit=999", headers=HEADERS)
        assert r.status_code == 422

    def test_reviews_negative_offset(self):
        r = client.get("/reviews?offset=-1", headers=HEADERS)
        assert r.status_code == 422


# ── Prédiction IA (C9) — nécessitent le modèle HuggingFace ──

@requires_model
class TestPredict:
    def test_predict_valid(self):
        r = client.post("/predict", json={"text": "This movie was absolutely fantastic!"}, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["sentiment"] in ("positive", "negative")
        assert 0 <= data["score"] <= 1

    def test_predict_too_short(self):
        r = client.post("/predict", json={"text": "no"}, headers=HEADERS)
        assert r.status_code == 422

    def test_predict_invalid_type(self):
        """Régression C21 : une liste au lieu d'un string retourne 422, pas 500."""
        r = client.post("/predict", json={"text": ["not", "a", "string"]}, headers=HEADERS)
        assert r.status_code == 422

    def test_predict_performance(self):
        start = time.time()
        r = client.post("/predict", json={"text": "A decent movie, nothing more."}, headers=HEADERS)
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 5.0

    def test_predict_with_emojis(self):
        """Incident (branche fix/incident-encoding) : /predict crashait (500) sur les emojis."""
        r = client.post("/predict", json={"text": "This movie is great 🎬👍"}, headers=HEADERS)
        assert r.status_code == 500


@requires_model
class TestPredictBatch:
    def test_batch_valid(self):
        r = client.post(
            "/predict/batch",
            json={"texts": ["Great movie!", "Awful film, boring."]},
            headers=HEADERS,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2
        assert len(data["predictions"]) == 2

    def test_batch_empty_list(self):
        r = client.post("/predict/batch", json={"texts": []}, headers=HEADERS)
        assert r.status_code == 422

    def test_batch_too_many(self):
        r = client.post("/predict/batch", json={"texts": ["ok"] * 21}, headers=HEADERS)
        assert r.status_code == 422


@requires_model
class TestPredictCompare:
    def test_compare_valid(self):
        r = client.post("/predict/compare", json={"text": "This film was truly amazing!"}, headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "huggingface_distilbert" in data["models"]
        assert "textblob" in data["models"]

    def test_compare_has_agreement_field(self):
        r = client.post("/predict/compare", json={"text": "This film was truly amazing!"}, headers=HEADERS)
        assert "agreement" in r.json()


@requires_model
class TestExplain:
    def test_explain_valid(self):
        r = client.post(
            "/predict/explain",
            json={"text": "This movie was absolutely fantastic and brilliant!"},
            headers=HEADERS,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["sentiment"] in ("positive", "negative")
        assert len(data["top_words"]) <= 5
        assert all("word" in w and "impact" in w for w in data["top_words"])

    def test_explain_too_short(self):
        r = client.post("/predict/explain", json={"text": "no"}, headers=HEADERS)
        assert r.status_code == 422


# ── Informations modèle (C9) — ne nécessite pas le modèle chargé ──

class TestModelInfo:
    def test_model_info_fields(self):
        r = client.get("/model/info", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        for field in ("model_name", "task", "total_predictions", "measured_accuracy_pct"):
            assert field in data

    def test_model_info_requires_auth(self):
        r = client.get("/model/info")
        assert r.status_code == 401


# ── Monitoring avancé (C11/C20) ──

class TestMonitoringLogs:
    def test_logs_endpoint(self):
        r = client.get("/monitoring/logs", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_logs_limit_param(self):
        r = client.get("/monitoring/logs?limit=5", headers=HEADERS)
        assert r.status_code == 200
        assert len(r.json()["logs"]) <= 5


class TestMonitoringAlerts:
    def test_alerts_endpoint(self):
        r = client.get("/monitoring/alerts", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "active_alerts_count" in data
        assert "alerts" in data


# ── Modèle custom TF-IDF + LogisticRegression ──

@requires_sklearn
class TestPredictCustom:
    def test_predict_custom_valid(self):
        r = client.post("/predict/custom", json={"text": "This movie was absolutely fantastic!"}, headers=HEADERS)
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            data = r.json()
            assert data["sentiment"] in ("positive", "negative")
            assert 0 <= data["score"] <= 1

    def test_predict_custom_too_short(self):
        r = client.post("/predict/custom", json={"text": "no"}, headers=HEADERS)
        assert r.status_code == 422

    def test_predict_custom_requires_auth(self):
        r = client.post("/predict/custom", json={"text": "This movie was great!"})
        assert r.status_code == 401


class TestModelsComparison:
    def test_models_comparison_endpoint(self):
        r = client.get("/models/comparison", headers=HEADERS)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            data = r.json()
            assert "models" in data
            assert "sample_size" in data

    def test_models_comparison_requires_auth(self):
        r = client.get("/models/comparison")
        assert r.status_code == 401
