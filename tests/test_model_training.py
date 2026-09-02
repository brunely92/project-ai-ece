"""
Tests du modèle custom entraîné (TF-IDF + LogisticRegression).
Les artefacts (models/*.joblib) sont gitignorés et absents en CI : ce module est
skippé entièrement tant que le modèle n'a pas été entraîné localement
(python -m src.model.train_model).
"""
import json
from pathlib import Path

import pytest

MODEL_PATH = Path("models/tfidf_logreg.joblib")
VECTORIZER_PATH = Path("models/tfidf_vectorizer.joblib")
METRICS_PATH = Path("reports/model_evaluation.json")

pytestmark = pytest.mark.skipif(
    not (MODEL_PATH.exists() and VECTORIZER_PATH.exists() and METRICS_PATH.exists()),
    reason="Modèle custom non entraîné localement (lancez: python -m src.model.train_model)",
)


def test_model_file_exists():
    assert MODEL_PATH.exists()


def test_vectorizer_file_exists():
    assert VECTORIZER_PATH.exists()


def test_metrics_file_exists():
    assert METRICS_PATH.exists()


@pytest.fixture
def metrics():
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_accuracy_above_80_pct(metrics):
    assert metrics["accuracy"] > 0.80


def test_metrics_fields_present(metrics):
    for field in ("precision", "recall", "f1_score", "n_train", "n_test"):
        assert field in metrics


def test_model_loadable():
    import joblib

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    assert hasattr(model, "predict")
    assert hasattr(vectorizer, "transform")


def test_model_predicts_valid_sentiment():
    import joblib

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    X = vectorizer.transform(["This movie was absolutely fantastic and brilliant!"])
    pred = model.predict(X)[0]
    assert pred in ("positive", "negative")
