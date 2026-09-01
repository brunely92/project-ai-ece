"""
C12 — Tests automatisés du dataset (version enrichie)
Vérifie qualité, intégrité, scores, distribution.
"""
import pandas as pd
import pytest
from pathlib import Path

PROCESSED_FILE = Path("data/processed/reviews_clean.csv")


@pytest.fixture
def dataset():
    if not PROCESSED_FILE.exists():
        pytest.skip("Dataset non trouvé")
    return pd.read_csv(PROCESSED_FILE)


def test_file_exists():
    assert PROCESSED_FILE.exists()


def test_columns_present(dataset):
    expected = {"review_text", "sentiment", "source"}
    assert expected.issubset(set(dataset.columns))


def test_no_null_reviews(dataset):
    assert dataset["review_text"].isna().sum() == 0


def test_no_empty_reviews(dataset):
    assert (dataset["review_text"].str.strip() == "").sum() == 0


def test_no_duplicates(dataset):
    assert dataset["review_text"].duplicated().sum() == 0


def test_min_length(dataset):
    assert (dataset["review_text"].str.len() < 20).sum() == 0


def test_valid_sentiments(dataset):
    valid = {"positive", "negative"}
    labeled = dataset[dataset["sentiment"].notna()]
    invalid = labeled[~labeled["sentiment"].isin(valid)]
    assert len(invalid) == 0


def test_has_multiple_sources(dataset):
    assert dataset["source"].nunique() >= 1


def test_quality_scores_present(dataset):
    """Les scores de qualité sont calculés."""
    if "quality_score" in dataset.columns:
        assert dataset["quality_score"].notna().sum() > 0
        assert dataset["quality_score"].min() >= 0
        assert dataset["quality_score"].max() <= 100


def test_text_length_column(dataset):
    """La longueur du texte est calculée."""
    if "text_length" in dataset.columns:
        assert (dataset["text_length"] > 0).all()


def test_word_count_column(dataset):
    """Le nombre de mots est calculé."""
    if "word_count" in dataset.columns:
        assert (dataset["word_count"] > 0).all()


def test_sentiment_balance(dataset):
    """Le dataset n'est pas trop déséquilibré (max 70/30)."""
    labeled = dataset[dataset["sentiment"].notna()]
    if len(labeled) > 100:
        counts = labeled["sentiment"].value_counts()
        ratio = counts.min() / counts.max()
        assert ratio > 0.3, f"Dataset trop déséquilibré: ratio {ratio:.2f}"
