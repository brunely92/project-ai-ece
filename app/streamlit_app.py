"""
C10/C17 — Application Streamlit intégrant le service IA
Pages : Analyse de sentiment, Statistiques, Recherche
"""
import os
import requests
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_SECRET_KEY", "dev-key-change-me")
HEADERS = {"x-api-key": API_KEY}

st.set_page_config(
    page_title="Analyse de Sentiment — Avis de Films",
    page_icon="🎬",
    layout="wide",
)


def api_call(method: str, endpoint: str, **kwargs) -> dict | None:
    """Appel sécurisé à l'API avec gestion d'erreurs."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10, **kwargs)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, timeout=30, **kwargs)
        else:
            return None

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.error("Erreur d'authentification. Vérifiez votre clé API.")
        elif response.status_code == 404:
            st.warning("Ressource non trouvée.")
        else:
            st.error(f"Erreur API : {response.status_code} — {response.text}")
    except requests.ConnectionError:
        st.error("Impossible de contacter l'API. Vérifiez que le serveur est lancé.")
    except requests.Timeout:
        st.error("L'API met trop de temps à répondre. Réessayez.")
    except Exception as e:
        st.error(f"Erreur inattendue : {e}")
    return None


# ── Navigation ──
page = st.sidebar.selectbox(
    "Navigation",
    ["🎯 Analyse de sentiment", "📊 Statistiques", "🔍 Recherche"],
)

# ── Page 1 : Analyse de sentiment ──
if page == "🎯 Analyse de sentiment":
    st.title("🎬 Analyse de Sentiment — Avis de Films")
    st.markdown("Saisissez un avis de film et obtenez son sentiment prédit par notre modèle IA.")
    st.caption("ℹ️ Résultat généré par intelligence artificielle (modèle DistilBERT).")

    text = st.text_area(
        label="Votre avis (en anglais)",
        placeholder="This movie was absolutely fantastic!",
        height=120,
        max_chars=5000,
    )

    if st.button("Analyser le sentiment", type="primary"):
        if not text or len(text.strip()) < 5:
            st.warning("Veuillez saisir un avis d'au moins 5 caractères.")
        else:
            with st.spinner("Analyse en cours..."):
                result = api_call("POST", "/predict", json={"text": text})

            if result:
                sentiment = result["sentiment"]
                score = result["score"]
                time_ms = result["processing_time_ms"]

                col1, col2, col3 = st.columns(3)
                with col1:
                    color = "🟢" if sentiment == "positive" else "🔴"
                    st.metric("Sentiment", f"{color} {sentiment.upper()}")
                with col2:
                    st.metric("Confiance", f"{score * 100:.1f}%")
                with col3:
                    st.metric("Temps", f"{time_ms:.0f} ms")

# ── Page 2 : Statistiques ──
elif page == "📊 Statistiques":
    st.title("📊 Statistiques du dataset")

    stats = api_call("GET", "/stats")
    if stats:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total avis", stats["total_reviews"])
            st.metric("Longueur moyenne", f"{stats['avg_review_length']} car.")

        with col2:
            if stats.get("by_sentiment"):
                st.subheader("Distribution des sentiments")
                df_sent = pd.DataFrame(
                    list(stats["by_sentiment"].items()),
                    columns=["Sentiment", "Nombre"],
                )
                st.bar_chart(df_sent.set_index("Sentiment"))

        if stats.get("by_source"):
            st.subheader("Avis par source")
            df_src = pd.DataFrame(
                list(stats["by_source"].items()),
                columns=["Source", "Nombre"],
            )
            st.dataframe(df_src, use_container_width=True)

# ── Page 3 : Recherche ──
elif page == "🔍 Recherche":
    st.title("🔍 Recherche d'avis")

    query = st.text_input(
        label="Mot-clé de recherche",
        placeholder="fantastic, boring, acting...",
    )

    if query and len(query) >= 2:
        result = api_call("GET", f"/search?q={query}")
        if result:
            st.info(f"{result['count']} résultat(s) pour « {result['query']} »")
            if result["reviews"]:
                for r in result["reviews"]:
                    sentiment_badge = "🟢" if r.get("sentiment") == "positive" else "🔴" if r.get("sentiment") == "negative" else "⚪"
                    with st.expander(f"{sentiment_badge} Avis #{r['id']} — {r['source']}"):
                        st.write(r["review_text"])
            else:
                st.warning("Aucun résultat trouvé.")
    elif query:
        st.warning("Saisissez au moins 2 caractères.")
