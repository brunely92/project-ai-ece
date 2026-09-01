"""
C11/C20 — Middleware de monitoring intégré à l'API
Intercepte chaque requête pour loguer : endpoint, status, latence, taille.
"""
import time
import logging
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("api_monitor")
logger.setLevel(logging.INFO)

if not logger.handlers:
    fh = logging.FileHandler(LOG_DIR / "api.log")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%dT%H:%M:%S"))
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%dT%H:%M:%S"))
    logger.addHandler(ch)

# Seuils d'alerte
LATENCY_THRESHOLD_MS = 1000
ALERT_ENDPOINTS = {}  # compteur erreurs par endpoint


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware qui logue chaque requête avec métriques de performance."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        endpoint = f"{request.method} {request.url.path}"

        try:
            response = await call_next(request)
            latency_ms = (time.time() - start) * 1000
            status = response.status_code

            # Log structuré (sans données personnelles)
            msg = f"endpoint={endpoint} | status={status} | latency_ms={latency_ms:.1f}"

            if status >= 500:
                logger.error(msg)
                ALERT_ENDPOINTS[endpoint] = ALERT_ENDPOINTS.get(endpoint, 0) + 1
            elif status >= 400:
                logger.warning(msg)
            else:
                logger.info(msg)

            # Alertes
            if latency_ms > LATENCY_THRESHOLD_MS:
                logger.warning(f"ALERTE_LATENCE | {endpoint} | {latency_ms:.0f}ms > {LATENCY_THRESHOLD_MS}ms")

            return response

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.error(f"endpoint={endpoint} | error={type(e).__name__}: {e} | latency_ms={latency_ms:.1f}")
            raise
