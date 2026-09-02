"""
C10/C17 — Application Streamlit enrichie
Pages : Analyse, Statistiques, Recherche, Dashboard IA, Explorer les films,
Comparaison de modèles, Analyse avancée
"""
import json
import os
import re
import sqlite3
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_SECRET_KEY", "dev-key-change-me")
DB_PATH = Path(os.getenv("DATABASE_PATH", "data/movies_reviews.sqlite"))
HEADERS = {"x-api-key": API_KEY}

st.set_page_config(
    page_title="Analyse de Sentiment — Avis de Films",
    page_icon="🎬",
    layout="wide",
)


def api_call(method, endpoint, **kwargs):
    """Appel sécurisé à l'API."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, timeout=10, **kwargs)
        elif method == "POST":
            r = requests.post(url, headers=HEADERS, timeout=30, **kwargs)
        else:
            return None
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 401:
            st.error("Erreur d'authentification API.")
        else:
            st.error(f"Erreur API : {r.status_code}")
    except requests.ConnectionError:
        st.error("API indisponible. Lancez : uvicorn src.api.main:app --reload")
    except requests.Timeout:
        st.error("L'API met trop de temps. Réessayez.")
    return None


def get_db():
    """Connexion directe à SQLite pour les dashboards."""
    if DB_PATH.exists():
        return sqlite3.connect(DB_PATH)
    return None


# ── Navigation ──
page = st.sidebar.selectbox(
    "Navigation",
    ["🎯 Analyse de sentiment", "📊 Statistiques", "🔍 Recherche",
     "🤖 Dashboard IA", "🎥 Explorer les films", "🧪 Comparaison de modèles",
     "📈 Analyse avancée"],
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

    col_btn, col_example = st.columns([1, 2])
    with col_btn:
        analyze = st.button("Analyser le sentiment", type="primary")
    with col_example:
        example = st.selectbox("Ou choisir un exemple :", [
            "",
            "This movie was absolutely brilliant, a masterpiece!",
            "Terrible waste of time, boring and predictable.",
            "Not bad, but not great either. Average at best.",
            "The visuals were stunning but the story made no sense.",
        ], label_visibility="collapsed")

    if example and not text:
        text = example

    if analyze and text:
        if len(text.strip()) < 5:
            st.warning("Saisissez au moins 5 caractères.")
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

                # Barre de confiance visuelle
                bar_color = "#16A34A" if sentiment == "positive" else "#DC2626"
                st.markdown(
                    f'<div style="background:#E5E7EB;border-radius:8px;height:20px;margin-top:10px">'
                    f'<div style="background:{bar_color};width:{score*100:.0f}%;height:20px;border-radius:8px"></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

# ── Page 2 : Statistiques ──
elif page == "📊 Statistiques":
    st.title("📊 Statistiques du dataset")
    stats = api_call("GET", "/stats")
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total avis", f"{stats['total_reviews']:,}")
        c2.metric("Positifs", stats.get("by_sentiment", {}).get("positive", 0))
        c3.metric("Négatifs", stats.get("by_sentiment", {}).get("negative", 0))
        c4.metric("Longueur moy.", f"{stats.get('avg_review_length', 0)} car.")

        col1, col2 = st.columns(2)
        with col1:
            if stats.get("by_sentiment"):
                st.subheader("Distribution des sentiments")
                df_sent = pd.DataFrame(
                    list(stats["by_sentiment"].items()), columns=["Sentiment", "Nombre"]
                )
                st.bar_chart(df_sent.set_index("Sentiment"))
        with col2:
            if stats.get("by_source"):
                st.subheader("Avis par source")
                df_src = pd.DataFrame(
                    list(stats["by_source"].items()), columns=["Source", "Nombre"]
                )
                st.bar_chart(df_src.set_index("Source"))

# ── Page 3 : Recherche ──
elif page == "🔍 Recherche":
    st.title("🔍 Recherche d'avis")
    query = st.text_input("Mot-clé", placeholder="fantastic, boring, acting...")

    if query and len(query) >= 2:
        result = api_call("GET", f"/search?q={query}")
        if result:
            st.info(f"{result['count']} résultat(s) pour « {result['query']} »")

            if result.get("reviews"):
                df_export = pd.DataFrame(result["reviews"])
                safe_query = re.sub(r"[^a-zA-Z0-9]+", "_", query).strip("_") or "recherche"
                st.download_button(
                    "📥 Exporter les résultats en CSV",
                    data=df_export.to_csv(index=False).encode("utf-8"),
                    file_name=f"recherche_{safe_query}.csv",
                    mime="text/csv",
                )

            for r in result.get("reviews", []):
                badge = "🟢" if r.get("sentiment") == "positive" else "🔴"
                with st.expander(f"{badge} Avis #{r['id']} — {r['source']}"):
                    st.write(r["review_text"][:500] + ("..." if len(r["review_text"]) > 500 else ""))

# ── Page 4 : Dashboard IA ──
elif page == "🤖 Dashboard IA":
    st.title("🤖 Dashboard Intelligence Artificielle")

    conn = get_db()
    if conn:
        # Vérifier si des prédictions existent
        nb_pred = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]

        if nb_pred == 0:
            st.warning("Aucune prédiction en base. Lancez : python -m src.model.batch_predict")
        else:
            st.success(f"{nb_pred} prédictions en base")

            c1, c2, c3 = st.columns(3)

            # Accuracy globale
            accuracy = conn.execute(
                """SELECT ROUND(SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                   FROM reviews r JOIN predictions p ON r.id = p.review_id
                   WHERE r.sentiment IS NOT NULL"""
            ).fetchone()[0]
            c1.metric("Accuracy globale", f"{accuracy}%")

            # Score confiance moyen
            avg_conf = conn.execute("SELECT ROUND(AVG(confidence_score) * 100, 1) FROM predictions").fetchone()[0]
            c2.metric("Confiance moyenne", f"{avg_conf}%")

            c3.metric("Prédictions", f"{nb_pred}")

            # Distribution confiance
            st.subheader("Distribution des scores de confiance")
            df_conf = pd.read_sql_query(
                """SELECT
                    CASE
                        WHEN confidence_score >= 0.99 THEN '99-100%'
                        WHEN confidence_score >= 0.95 THEN '95-99%'
                        WHEN confidence_score >= 0.90 THEN '90-95%'
                        WHEN confidence_score >= 0.80 THEN '80-90%'
                        ELSE '50-80%'
                    END AS tranche,
                    COUNT(*) AS nb
                FROM predictions
                GROUP BY tranche
                ORDER BY MIN(confidence_score) DESC""",
                conn,
            )
            st.bar_chart(df_conf.set_index("tranche"))

            # Matrice de confusion
            st.subheader("Matrice de confusion")
            df_matrix = pd.read_sql_query(
                """SELECT r.sentiment as Réel, p.predicted_sentiment as Prédit, COUNT(*) as Nombre
                   FROM reviews r JOIN predictions p ON r.id = p.review_id
                   WHERE r.sentiment IS NOT NULL
                   GROUP BY r.sentiment, p.predicted_sentiment""",
                conn,
            )
            if not df_matrix.empty:
                pivot = df_matrix.pivot(index="Réel", columns="Prédit", values="Nombre").fillna(0).astype(int)
                st.dataframe(pivot, use_container_width=True)

            # Prédictions les moins confiantes
            st.subheader("Prédictions les moins confiantes")
            df_low = pd.read_sql_query(
                """SELECT r.id, SUBSTR(r.review_text, 1, 100) as extrait,
                          r.sentiment as vrai, p.predicted_sentiment as predit,
                          ROUND(p.confidence_score, 3) as confiance
                   FROM reviews r JOIN predictions p ON r.id = p.review_id
                   WHERE r.sentiment IS NOT NULL
                   ORDER BY p.confidence_score ASC
                   LIMIT 10""",
                conn,
            )
            st.dataframe(df_low, use_container_width=True, hide_index=True)

        conn.close()
    else:
        st.error("Base de données introuvable.")

    # Alertes actives (C20)
    st.subheader("🚨 Alertes actives")
    alerts_data = api_call("GET", "/monitoring/alerts")
    if alerts_data:
        st.metric("Alertes actives", alerts_data["active_alerts_count"])
        if alerts_data["alerts"]:
            st.dataframe(
                pd.DataFrame({"alerte": alerts_data["alerts"]}),
                use_container_width=True, hide_index=True,
            )
        else:
            st.success("Aucune alerte active.")

    # Historique des health checks (C20)
    st.subheader("🩺 Historique des health checks")
    health_path = Path("logs/health_report.json")
    if health_path.exists():
        with open(health_path, "r", encoding="utf-8") as f:
            health_history = json.load(f)
        if health_history:
            df_health = pd.DataFrame(health_history)
            st.dataframe(df_health, use_container_width=True, hide_index=True)
        else:
            st.info("Historique vide.")
    else:
        st.info("Aucun health check enregistré. Lancez : python -m src.monitoring.health_check")

# ── Page 5 : Explorer les films ──
elif page == "🎥 Explorer les films":
    st.title("🎥 Explorer les films")

    conn = get_db()
    if conn:
        nb_films = conn.execute("SELECT COUNT(*) FROM films").fetchone()[0]

        if nb_films == 0:
            st.warning("Aucun film en base. Lancez : python -m src.db.import_films")
        else:
            st.success(f"{nb_films} films en base")

            # Films avec le plus d'avis
            st.subheader("Films les plus commentés")
            df_films = pd.read_sql_query(
                """SELECT f.title, f.vote_average as note_tmdb, f.genre_ids as genres,
                          COUNT(r.id) as nb_avis,
                          ROUND(SUM(CASE WHEN r.sentiment = 'positive' THEN 1.0 ELSE 0.0 END) / COUNT(r.id) * 100, 1) as pct_positif
                   FROM films f
                   INNER JOIN reviews r ON f.id = r.film_id
                   GROUP BY f.id
                   HAVING nb_avis >= 2
                   ORDER BY nb_avis DESC
                   LIMIT 20""",
                conn,
            )
            if not df_films.empty:
                st.dataframe(df_films, use_container_width=True, hide_index=True)
            else:
                st.info("Aucun avis lié à un film. Lancez import_films.py pour enrichir les données.")

            # Liste des films
            st.subheader("Catalogue de films")
            df_all = pd.read_sql_query(
                "SELECT title, vote_average, genre_ids, release_date FROM films ORDER BY vote_average DESC",
                conn,
            )
            st.dataframe(df_all, use_container_width=True, hide_index=True)

        conn.close()
    else:
        st.error("Base de données introuvable.")

# ── Page 6 : Comparaison de modèles ──
elif page == "🧪 Comparaison de modèles":
    st.title("🧪 Comparaison de modèles")
    st.markdown(
        "Comparaison entre le modèle **HuggingFace DistilBERT** (pré-entraîné), un modèle "
        "**custom TF-IDF + Régression Logistique** (entraîné sur nos données) et **TextBlob** (lexical)."
    )

    comparison = api_call("GET", "/models/comparison")
    if comparison:
        models_data = comparison["models"]
        df_compare = pd.DataFrame(models_data).T
        df_compare.index.name = "Modèle"

        st.caption(f"Échantillon : {comparison['sample_size']} avis — généré le {comparison['generated_at'][:19]}")
        st.dataframe(df_compare, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Accuracy par modèle")
            st.bar_chart(df_compare["accuracy"])
        with col2:
            st.subheader("Latence moyenne (ms/avis)")
            st.bar_chart(df_compare["avg_latency_ms"])
    else:
        st.warning("Comparaison indisponible. Lancez : python -m src.model.compare_models")

# ── Page 7 : Analyse avancée ──
elif page == "📈 Analyse avancée":
    st.title("📈 Analyse avancée")

    conn = get_db()
    if conn:
        # 1. Distribution des scores de qualité
        st.subheader("Distribution des scores de qualité")
        df_quality = pd.read_sql_query(
            "SELECT quality_score FROM reviews WHERE quality_score IS NOT NULL", conn
        )
        if not df_quality.empty:
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.hist(df_quality["quality_score"], bins=20, color="#4C78A8", edgecolor="white")
            ax.set_xlabel("Score de qualité")
            ax.set_ylabel("Nombre d'avis")
            st.pyplot(fig)
        else:
            st.info("Aucun score de qualité en base.")

        st.divider()

        # 2. Mots les plus fréquents par sentiment (table de fréquence, pas de lib wordcloud)
        st.subheader("Mots les plus fréquents par sentiment")
        STOPWORDS = {
            "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be", "been",
            "being", "this", "that", "these", "those", "it", "its", "i", "you", "he", "she",
            "we", "they", "of", "in", "on", "at", "to", "for", "with", "as", "by", "from",
            "about", "into", "over", "so", "if", "than", "then", "too", "very", "just",
            "not", "no", "do", "does", "did", "have", "has", "had", "will", "would", "can",
            "could", "should", "my", "your", "his", "her", "their", "our", "what", "which",
            "who", "when", "where", "why", "how", "all", "movie", "film", "one", "also",
            "there", "out", "up", "down", "more", "most", "some", "them", "his", "her",
        }

        @st.cache_data(ttl=600)
        def word_frequencies(sentiment: str, sample_size: int = 2000, top_n: int = 20):
            sample_conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(
                "SELECT review_text FROM reviews WHERE sentiment = ? ORDER BY RANDOM() LIMIT ?",
                sample_conn, params=(sentiment, sample_size),
            )
            sample_conn.close()
            counter = Counter()
            for text in df["review_text"]:
                words = re.findall(r"[a-zA-Z']{3,}", text.lower())
                counter.update(w for w in words if w not in STOPWORDS)
            return pd.DataFrame(counter.most_common(top_n), columns=["mot", "occurrences"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🟢 Avis positifs**")
            st.bar_chart(word_frequencies("positive").set_index("mot"))
        with col2:
            st.markdown("**🔴 Avis négatifs**")
            st.bar_chart(word_frequencies("negative").set_index("mot"))

        st.divider()

        # 3. Mots les plus discriminants du modèle custom TF-IDF + LogisticRegression
        st.subheader("Mots les plus discriminants (modèle custom TF-IDF + LogReg)")
        model_path = Path("models/tfidf_logreg.joblib")
        vectorizer_path = Path("models/tfidf_vectorizer.joblib")
        if model_path.exists() and vectorizer_path.exists():
            import joblib

            model = joblib.load(model_path)
            vectorizer = joblib.load(vectorizer_path)
            feature_names = vectorizer.get_feature_names_out()
            coefs = model.coef_[0]
            top_positive_idx = coefs.argsort()[-10:][::-1]
            top_negative_idx = coefs.argsort()[:10]

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Top 10 mots → {model.classes_[1]}**")
                st.dataframe(
                    pd.DataFrame({"mot": feature_names[top_positive_idx], "coefficient": coefs[top_positive_idx]}),
                    use_container_width=True, hide_index=True,
                )
            with col2:
                st.markdown(f"**Top 10 mots → {model.classes_[0]}**")
                st.dataframe(
                    pd.DataFrame({"mot": feature_names[top_negative_idx], "coefficient": coefs[top_negative_idx]}),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.warning("Modèle custom non entraîné. Lancez : python -m src.model.train_model")

        st.divider()

        # 4. Corrélation note du film vs sentiment moyen des avis
        st.subheader("Corrélation note du film vs sentiment moyen des avis")
        df_corr = pd.read_sql_query(
            """SELECT f.title, COALESCE(f.imdb_rating, f.vote_average) as note,
                      ROUND(SUM(CASE WHEN r.sentiment='positive' THEN 1.0 ELSE 0.0 END) / COUNT(r.id) * 100, 1) as pct_positif,
                      COUNT(r.id) as nb_avis
               FROM films f
               JOIN reviews r ON r.film_id = f.id
               WHERE r.sentiment IS NOT NULL
               GROUP BY f.id
               HAVING nb_avis >= 3 AND note IS NOT NULL""",
            conn,
        )
        if len(df_corr) >= 3:
            correlation = df_corr["note"].corr(df_corr["pct_positif"])
            st.metric("Coefficient de corrélation (Pearson)", f"{correlation:.3f}")

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.scatter(df_corr["note"], df_corr["pct_positif"], color="#4C78A8", alpha=0.7)
            ax.set_xlabel("Note du film (TMDB — IMDB non disponible en base actuellement)")
            ax.set_ylabel("% d'avis positifs")
            st.pyplot(fig)
            st.caption(f"Basé sur {len(df_corr)} films ayant au moins 3 avis liés et une note connue.")
        else:
            st.info("Pas assez de films avec avis liés et note connue pour calculer une corrélation.")

        conn.close()
    else:
        st.error("Base de données introuvable.")
