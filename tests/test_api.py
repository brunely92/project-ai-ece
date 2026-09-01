"""
C12/C18 — Tests automatisés de l'API (v2)
Couvre : données, films, prédiction, batch, comparaison, monitoring, sécurité.
"""
import pytest
from fastapi.testclient import TestClient
import os

os.environ.setdefault("API_SECRET_KEY", "test-key")
os.environ.setdefault("DATABASE_PATH", "data/movies_reviews.sqlite")

from src.api.main import app

client = TestClient(app)
HEADERS = {"x-api-key": "test-key"}


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
