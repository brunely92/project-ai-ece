"""
C8 — Test fonctionnel du service IA
Vérifie que le modèle HuggingFace se charge et produit des prédictions.
"""
import time
import sys


def main():
    print("=" * 60)
    print("TEST SERVICE IA — HuggingFace Sentiment Analysis")
    print("=" * 60)

    try:
        from transformers import pipeline
    except ImportError:
        print("[ERREUR] transformers non installé.")
        print("         pip install transformers torch")
        sys.exit(1)

    # Charger le modèle
    print("[INFO] Chargement du modèle...")
    start = time.time()
    classifier = pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english",
    )
    load_time = time.time() - start
    print(f"[OK] Modèle chargé en {load_time:.1f}s")

    # Tests
    tests = [
        ("This movie was absolutely fantastic!", "POSITIVE"),
        ("Terrible film, waste of time.", "NEGATIVE"),
        ("Not bad, but not great either.", "NEGATIVE"),
        ("I fell asleep halfway through.", "NEGATIVE"),
        ("A masterpiece of modern cinema.", "POSITIVE"),
    ]

    print(f"\n{'Texte':50s} | {'Attendu':10s} | {'Prédit':10s} | {'Score':6s} | {'OK':3s}")
    print("-" * 90)

    passed = 0
    for text, expected in tests:
        start = time.time()
        result = classifier(text)[0]
        latency = (time.time() - start) * 1000

        label = result["label"]
        score = result["score"]
        ok = "✅" if label == expected else "❌"
        if label == expected:
            passed += 1

        print(f"{text:50s} | {expected:10s} | {label:10s} | {score:.4f} | {ok}")

    print(f"\n[RÉSULTAT] {passed}/{len(tests)} tests passés")
    print("=" * 60)


if __name__ == "__main__":
    main()
