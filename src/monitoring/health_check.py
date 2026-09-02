"""
C20 — Health check applicatif.
Interroge /health et /monitoring/metrics, vérifie les seuils de monitoring
(docs/monitoring.md) et ajoute un rapport à l'historique logs/health_report.json.
"""
import json
import os
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_SECRET_KEY", "dev-key-change-me")
HEADERS = {"x-api-key": API_KEY}

REPORT_PATH = Path("logs/health_report.json")
MAX_HISTORY = 100

# Seuils repris de docs/monitoring.md
THRESHOLDS = {
    "min_accuracy_pct": 70,
    "min_avg_confidence": 0.6,
    "max_low_confidence_pct": 20,
}


def check_health() -> dict:
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=10)
        return {"reachable": True, "status_code": r.status_code, "body": r.json()}
    except requests.RequestException as e:
        return {"reachable": False, "status_code": None, "error": str(e)}


def check_metrics() -> dict:
    try:
        r = requests.get(f"{API_BASE_URL}/monitoring/metrics", headers=HEADERS, timeout=10)
        return {"reachable": True, "status_code": r.status_code, "body": r.json()}
    except requests.RequestException as e:
        return {"reachable": False, "status_code": None, "error": str(e)}


def evaluate(health: dict, metrics: dict) -> tuple[str, list[str]]:
    """Retourne (statut_global, liste_d_alertes) selon les seuils de monitoring.md."""
    alerts = []

    if not health.get("reachable") or health.get("status_code") != 200:
        alerts.append("API /health injoignable ou en erreur")
    elif health.get("body", {}).get("status") != "ok":
        alerts.append("API /health signale un statut non-ok")

    if not metrics.get("reachable"):
        alerts.append("API /monitoring/metrics injoignable")
    else:
        body = metrics.get("body", {})
        if body.get("status") == "no_predictions":
            alerts.append("Aucune prédiction en base (batch_predict non lancé)")
        else:
            accuracy = body.get("accuracy_pct")
            if accuracy is not None and accuracy < THRESHOLDS["min_accuracy_pct"]:
                alerts.append(f"Accuracy basse : {accuracy}% < {THRESHOLDS['min_accuracy_pct']}%")

            avg_conf = body.get("avg_confidence")
            if avg_conf is not None and avg_conf < THRESHOLDS["min_avg_confidence"]:
                alerts.append(f"Confiance moyenne basse : {avg_conf} < {THRESHOLDS['min_avg_confidence']}")

            total = body.get("total_predictions") or 0
            low_conf = body.get("low_confidence_count") or 0
            if total > 0:
                low_conf_pct = round(low_conf / total * 100, 1)
                if low_conf_pct > THRESHOLDS["max_low_confidence_pct"]:
                    alerts.append(
                        f"Trop de prédictions peu confiantes : {low_conf_pct}% "
                        f"> {THRESHOLDS['max_low_confidence_pct']}%"
                    )

    status = "ok" if not alerts else "degraded"
    return status, alerts


def append_to_history(report: dict):
    REPORT_PATH.parent.mkdir(exist_ok=True)
    history = []
    if REPORT_PATH.exists():
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []

    history.append(report)
    history = history[-MAX_HISTORY:]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def main():
    print("=" * 60)
    print(f"HEALTH CHECK — {datetime.now().isoformat()}")
    print("=" * 60)

    health = check_health()
    metrics = check_metrics()
    status, alerts = evaluate(health, metrics)

    report = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "health_reachable": health.get("reachable"),
        "health_status_code": health.get("status_code"),
        "metrics_reachable": metrics.get("reachable"),
        "accuracy_pct": metrics.get("body", {}).get("accuracy_pct"),
        "avg_confidence": metrics.get("body", {}).get("avg_confidence"),
        "total_predictions": metrics.get("body", {}).get("total_predictions"),
        "alerts": alerts,
    }

    append_to_history(report)

    print(f"[{'OK' if status == 'ok' else 'DEGRADED'}] Statut global : {status}")
    if alerts:
        for a in alerts:
            print(f"  [ALERTE] {a}")
    else:
        print("  Aucune alerte.")
    print(f"\n[OK] Rapport ajouté à : {REPORT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
