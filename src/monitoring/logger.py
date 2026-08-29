"""
C11/C20 — Monitoring et journalisation
Logs structurés pour API et modèle IA.
Format : timestamp | endpoint | status | latency_ms | details
Seuils d'alerte configurés.
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from functools import wraps

# Répertoire de logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Logger structuré
logger = logging.getLogger("sentiment_api")
logger.setLevel(logging.INFO)

# Handler fichier
file_handler = logging.FileHandler(LOG_DIR / "api.log")
file_handler.setLevel(logging.INFO)

# Handler console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Format structuré (sans données personnelles)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# ── Seuils d'alerte ──
THRESHOLDS = {
    "latency_ms": 1000,       # Alerte si latence > 1000ms
    "error_rate_pct": 5,      # Alerte si taux erreurs 5xx > 5%
    "empty_prediction": 0,    # Alerte si prédiction vide > 0
    "low_confidence": 0.5,    # Warning si score confiance < 0.5
}


def log_request(endpoint: str, status: int, latency_ms: float, details: str = ""):
    """Journalise une requête API."""
    msg = f"endpoint={endpoint} | status={status} | latency_ms={latency_ms:.1f}"
    if details:
        msg += f" | {details}"

    # Log selon le statut
    if status >= 500:
        logger.error(msg)
    elif status >= 400:
        logger.warning(msg)
    else:
        logger.info(msg)

    # Vérification seuils
    if latency_ms > THRESHOLDS["latency_ms"]:
        logger.warning(f"ALERTE LATENCE | {endpoint} | {latency_ms:.0f}ms > seuil {THRESHOLDS['latency_ms']}ms")


def log_prediction(text_length: int, sentiment: str, score: float, latency_ms: float):
    """Journalise une prédiction du modèle (sans le texte pour RGPD)."""
    msg = f"endpoint=/predict | prediction={sentiment} | score={score:.4f} | latency_ms={latency_ms:.1f} | text_length={text_length}"
    logger.info(msg)

    # Alerte score bas
    if score < THRESHOLDS["low_confidence"]:
        logger.warning(f"ALERTE CONFIANCE | score={score:.4f} < seuil {THRESHOLDS['low_confidence']}")

    # Alerte latence
    if latency_ms > THRESHOLDS["latency_ms"]:
        logger.warning(f"ALERTE LATENCE PREDICT | {latency_ms:.0f}ms > seuil {THRESHOLDS['latency_ms']}ms")


def log_error(endpoint: str, error: str):
    """Journalise une erreur (sans données personnelles)."""
    logger.error(f"endpoint={endpoint} | error={error}")
