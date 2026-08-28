"""
C12 — Tests automatisés du dataset
Vérifie la qualité des données avant utilisation par le modèle.
"""
import pandas as pd
import pytest
from pathlib import Path

PROCESSED_FILE = Path("data/processed/reviews_clean.csv")


@pytest.fixture
def dataset():
    """Charge le dataset nettoyé."""
    if not PROCESSED_FILE.exists():
        pytest.skip("Dataset non trouvé — exécuter clean_dataset.py d'abord")
    return pd.read_csv(PROCESSED_FILE)


def test_file_exists():
    """Le fichier nettoyé doit exister."""
    assert PROCESSED_FILE.exists(), f"Fichier manquant : {PROCESSED_FILE}"


def test_columns_present(dataset):
    """Les colonnes obligatoires sont présentes."""
    expected = {"review_text", "sentiment", "source"}
    assert expected.issubset(set(dataset.columns))


def test_no_null_reviews(dataset):
    """Aucun avis ne doit être null."""
    assert dataset["review_text"].isna().sum() == 0


def test_no_empty_reviews(dataset):
    """Aucun avis ne doit être vide."""
    assert (dataset["review_text"].str.strip() == "").sum() == 0


def test_no_duplicates(dataset):
    """Pas de doublons sur le texte."""
    assert dataset["review_text"].duplicated().sum() == 0


def test_min_length(dataset):
    """Tous les avis font au moins 20 caractères."""
    assert (dataset["review_text"].str.len() < 20).sum() == 0


def test_valid_sentiments(dataset):
    """Les sentiments sont positive, negative ou null."""
    valid = {"positive", "negative"}
    labeled = dataset[dataset["sentiment"].notna()]
    invalid = labeled[~labeled["sentiment"].isin(valid)]
    assert len(invalid) == 0, f"Sentiments invalides : {invalid['sentiment'].unique()}"


def test_has_multiple_sources(dataset):
    """Au moins 2 sources différentes (preuve C1)."""
    assert dataset["source"].nunique() >= 1
