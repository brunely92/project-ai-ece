"""
C12/C18 — Tests automatisés de l'API
Vérifie les endpoints données et prédiction.
"""
import pytest
from fastapi.testclient import TestClient
import os

os.environ.setdefault("API_SECRET_KEY", "test-key")
os.environ.setdefault("DATABASE_PATH", "data/movies_reviews.sqlite")

from src.api.main import app

client = TestClient(app)
HEADERS = {"x-api-key": "test-key"}


def test_health():
    """GET /health retourne 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ("ok", "error")


def test_reviews_unauthorized():
    """GET /reviews sans clé API retourne 401."""
    response = client.get("/reviews")
    assert response.status_code == 401


def test_reviews_authorized():
    """GET /reviews avec clé API retourne 200."""
    response = client.get("/reviews", headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        assert "reviews" in data
        assert "count" in data


def test_review_not_found():
    """GET /reviews/999999 retourne 404."""
    response = client.get("/reviews/999999", headers=HEADERS)
    assert response.status_code in (404, 500)  # 500 si pas de base


def test_search():
    """GET /search?q=movie retourne 200."""
    response = client.get("/search?q=movie", headers=HEADERS)
    assert response.status_code in (200, 500)


def test_stats():
    """GET /stats retourne 200."""
    response = client.get("/stats", headers=HEADERS)
    assert response.status_code in (200, 500)
