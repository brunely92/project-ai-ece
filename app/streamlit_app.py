"""
C10/C17 — Application Streamlit (design system custom)
Pages : Analyse, Dashboard, Modèles, Films, Recherche, Avancé

Toute la logique métier (appels API, requêtes SQLite) est inchangée par rapport
aux versions précédentes — seuls le design et l'expérience utilisateur changent.
"""
import json
import os
import re
import sqlite3
import uuid
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

COLORS = {
    "bg": "#0F172A",
    "card": "#1E293B",
    "border": "#334155",
    "text": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "accent": "#6366F1",
    "success": "#10B981",
    "danger": "#EF4444",
}

st.set_page_config(
    page_title="SentimentFlick — Analyse de Sentiment",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="auto",
)


# ══════════════════════════════════════════════════════════════
# DESIGN SYSTEM — CSS custom
# ══════════════════════════════════════════════════════════════

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Chrome Streamlit à masquer */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    [data-testid="stDecoration"] {{ display: none; }}
    [data-testid="stToolbar"] {{ display: none; }}
    [data-testid="stSkillsNudge"] {{ display: none; }}
    [data-testid="stSkillsNudgeAnchor"] {{ display: none; }}
    header {{ background: transparent !important; }}

    /* Fond général */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background-color: {COLORS["bg"]};
    }}
    [data-testid="stHeader"] {{ background: transparent; }}

    h1, h2, h3, h4, h5, p, span, label, li {{
        color: {COLORS["text"]};
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: #0B1120;
        border-right: 1px solid {COLORS["border"]};
    }}
    [data-testid="stSidebarUserContent"] {{
        display: flex;
        flex-direction: column;
        min-height: 92vh;
    }}

    /* Cards (st.container(border=True)) */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {COLORS["card"]};
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 12px !important;
    }}

    /* Boutons */
    .stButton > button {{
        background-color: {COLORS["accent"]};
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.4rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
        color: white;
    }}
    .stDownloadButton > button {{
        background-color: transparent;
        color: {COLORS["accent"]};
        border: 1px solid {COLORS["accent"]};
        border-radius: 8px;
        font-weight: 600;
    }}

    /* Champs de saisie */
    .stTextArea textarea, .stTextInput input {{
        background-color: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
        color: {COLORS["text"]};
    }}
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {COLORS["accent"]};
        box-shadow: 0 0 0 1px {COLORS["accent"]};
    }}
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {{
        color: {COLORS["text_secondary"]} !important;
        opacity: 1 !important;
    }}

    /* Pills (exemples cliquables) — rendues via st.pills = .stButtonGroup */
    .stButtonGroup button {{
        background-color: {COLORS["card"]} !important;
        color: {COLORS["text"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 999px !important;
    }}
    .stButtonGroup button:hover {{
        border-color: {COLORS["accent"]} !important;
        color: {COLORS["accent"]} !important;
    }}
    .stButtonGroup button p {{
        color: inherit !important;
    }}
    .stButtonGroup [aria-checked="true"] {{
        background-color: {COLORS["accent"]}33 !important;
        border-color: {COLORS["accent"]} !important;
        color: {COLORS["accent"]} !important;
    }}

    /* Metrics */
    [data-testid="stMetricValue"] {{ color: {COLORS["text"]}; }}
    [data-testid="stMetricLabel"] {{ color: {COLORS["text_secondary"]}; }}

    /* Dataframes */
    [data-testid="stDataFrame"] {{ border-radius: 10px; overflow: hidden; }}

    /* Navigation radio de la sidebar */
    [data-testid="stSidebar"] [role="radiogroup"] label {{
        border-radius: 8px;
        padding: 0.3rem 0.6rem;
    }}

    a {{ color: {COLORS["accent"]}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════
# Fonctions utilitaires (logique métier inchangée)
# ══════════════════════════════════════════════════════════════

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
            st.error("🔒 Erreur d'authentification API.")
        else:
            st.error(f"⚠️ Erreur API : {r.status_code}")
    except requests.ConnectionError:
        render_api_down()
    except requests.Timeout:
        st.error("⏱️ L'API met trop de temps à répondre. Réessayez.")
    return None


def get_db():
    """Connexion directe à SQLite pour les dashboards."""
    if DB_PATH.exists():
        return sqlite3.connect(DB_PATH)
    return None


def render_api_down():
    st.markdown(
        f"""
        <div style="text-align:center; padding:2.5rem 1rem; background:{COLORS["card"]};
                    border:1px solid {COLORS["border"]}; border-radius:12px;">
            <div style="font-size:2.5rem;">🔌</div>
            <div style="font-size:1.1rem; font-weight:700; margin-top:0.5rem;">API indisponible</div>
            <div style="color:{COLORS["text_secondary"]}; margin-top:0.4rem;">
                Lancez l'API avant de continuer :
            </div>
            <code style="display:inline-block; margin-top:0.6rem; background:{COLORS["bg"]};
                         padding:0.4rem 0.8rem; border-radius:6px; color:{COLORS["accent"]};">
                uvicorn src.api.main:app --reload
            </code>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="text-align:center; padding:2.5rem 1rem;">
            <div style="font-size:2.5rem;">{icon}</div>
            <div style="font-size:1.05rem; font-weight:700; margin-top:0.5rem;">{title}</div>
            {f'<div style="color:{COLORS["text_secondary"]}; margin-top:0.3rem;">{subtitle}</div>' if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sentiment_style(sentiment: str):
    is_pos = sentiment == "positive"
    return (COLORS["success"] if is_pos else COLORS["danger"]), ("😊" if is_pos else "😞")


def render_result_card(result: dict, model_label: str):
    """Grande card de résultat avec barre de confiance animée."""
    sentiment = result["sentiment"]
    score = result["score"]
    time_ms = result.get("processing_time_ms", 0)
    color, icon = sentiment_style(sentiment)
    anim_id = uuid.uuid4().hex[:8]

    with st.container(border=True):
        st.markdown(
            f"""
            <style>
            @keyframes fill_{anim_id} {{ from {{ width: 0%; }} to {{ width: {score * 100:.0f}%; }} }}
            </style>
            <div style="text-align:center; padding:0.6rem 0.4rem;">
                <div style="font-size:0.8rem; color:{COLORS["text_secondary"]}; text-transform:uppercase;
                            letter-spacing:0.5px;">{model_label}</div>
                <div style="font-size:2.1rem; font-weight:800; color:{color}; margin-top:0.3rem;">
                    {icon} {sentiment.upper()}
                </div>
                <div style="background:{COLORS["border"]}; border-radius:999px; height:14px;
                            margin:1rem 0 0.5rem 0; overflow:hidden;">
                    <div style="background:{color}; height:100%; border-radius:999px;
                                width:{score * 100:.0f}%; animation: fill_{anim_id} 0.9s ease-out;"></div>
                </div>
                <div style="color:{COLORS["text_secondary"]}; font-size:0.85rem;">
                    Confiance : <b style="color:{COLORS["text"]};">{score * 100:.1f}%</b>
                    &nbsp;·&nbsp; {time_ms:.0f} ms
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_mini_model_card(name: str, sentiment: str, score: float, time_ms: float):
    color, icon = sentiment_style(sentiment)
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="text-align:center; padding:0.4rem;">
                <div style="font-size:0.75rem; color:{COLORS["text_secondary"]}; min-height:2.2em;">{name}</div>
                <div style="font-size:1.5rem; font-weight:800; color:{color}; margin-top:0.3rem;">{icon} {sentiment.upper()}</div>
                <div style="color:{COLORS["text_secondary"]}; font-size:0.8rem; margin-top:0.3rem;">
                    {score * 100:.1f}% · {time_ms:.1f} ms
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def badge_html(text: str, color: str) -> str:
    return (
        f'<span style="background:{color}22; color:{color}; border:1px solid {color}55; '
        f'padding:2px 10px; border-radius:999px; font-size:0.75rem; font-weight:700;">{text}</span>'
    )


def styled_fig(figsize=(8, 3)):
    """Figure matplotlib pré-thémée pour le fond sombre de l'app."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(COLORS["card"])
    ax.set_facecolor(COLORS["card"])
    ax.tick_params(colors=COLORS["text_secondary"])
    ax.xaxis.label.set_color(COLORS["text"])
    ax.yaxis.label.set_color(COLORS["text"])
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(COLORS["border"])
    return fig, ax


# ══════════════════════════════════════════════════════════════
# Sidebar — Navigation
# ══════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding:0.5rem 0 1.2rem 0; text-align:center;">
            <div style="font-size:1.7rem; font-weight:800;">🎬 SentimentFlick</div>
            <div style="font-size:0.7rem; color:{COLORS["text_secondary"]}; letter-spacing:1.5px; margin-top:0.1rem;">
                SENTIMENT ANALYSIS PLATFORM
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        ["🎯 Analyse", "📊 Dashboard", "🧪 Modèles", "🎥 Films", "🔍 Recherche", "📈 Avancé"],
        label_visibility="collapsed",
    )

    st.markdown(
        f"""
        <div style="margin-top:auto; text-align:center; padding-top:1rem;
                    border-top:1px solid {COLORS["border"]};">
            {badge_html("188K reviews", COLORS["accent"])}
            {badge_html("59 tests", COLORS["success"])}
            {badge_html("17 endpoints", COLORS["accent"])}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# Page 1 : Analyse de sentiment
# ══════════════════════════════════════════════════════════════

if page == "🎯 Analyse":
    st.markdown(
        f"""
        <div style="text-align:center; padding:0.5rem 0 0.8rem 0;">
            {badge_html("v2.0.0 · PHD EDITION", COLORS["accent"])}
            <h1 style="font-size:clamp(1.8rem, 5vw, 2.6rem); font-weight:800; margin:0.7rem 0 0.2rem 0;">
                🎬 SentimentFlick
            </h1>
            <p style="color:{COLORS["text_secondary"]}; font-size:1.05rem; margin:0;">
                Analyse de sentiment d'avis de films, propulsée par l'IA
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.caption("ℹ️ Résultat généré par intelligence artificielle (modèle DistilBERT).")
        text = st.text_area(
            "Votre avis",
            placeholder='Écrivez un avis de film en anglais... ex : "This movie blew me away from start to finish!"',
            height=130,
            max_chars=5000,
            label_visibility="collapsed",
        )

        example_options = [
            "This movie was absolutely brilliant, a masterpiece!",
            "Terrible waste of time, boring and predictable.",
            "Not bad, but not great either. Average at best.",
            "The visuals were stunning but the story made no sense.",
        ]
        picked = st.pills("Exemples", example_options, label_visibility="collapsed")
        if picked and not text:
            text = picked

        col_a, col_b = st.columns([1, 2])
        with col_a:
            analyze = st.button("✨ Analyser le sentiment", type="primary", width='stretch')
        with col_b:
            compare_custom = st.toggle("Comparer avec le modèle custom (TF-IDF + LogReg)")

    if analyze and text:
        if len(text.strip()) < 5:
            st.warning("Saisissez au moins 5 caractères.")
        else:
            with st.spinner("Analyse en cours..."):
                result = api_call("POST", "/predict", json={"text": text})
                custom_result = api_call("POST", "/predict/custom", json={"text": text}) if compare_custom else None

            st.write("")
            if result and compare_custom:
                col1, col2 = st.columns(2)
                with col1:
                    render_result_card(result, "HuggingFace DistilBERT")
                with col2:
                    if custom_result:
                        render_result_card(custom_result, "TF-IDF + LogReg (custom)")
                    else:
                        empty_state("🧪", "Modèle custom indisponible",
                                     "Lancez : python -m src.model.train_model")
            elif result:
                render_result_card(result, result.get("model", "Modèle"))


# ══════════════════════════════════════════════════════════════
# Page 2 : Dashboard
# ══════════════════════════════════════════════════════════════

elif page == "📊 Dashboard":
    st.markdown("## 📊 Dashboard")

    stats = api_call("GET", "/stats")
    conn = get_db()

    if stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1, st.container(border=True):
            st.metric("Total avis", f"{stats['total_reviews']:,}")
        with c2, st.container(border=True):
            st.metric("Accuracy modèle", f"{stats.get('model_accuracy') or 0}%")
        with c3, st.container(border=True):
            st.metric("Films en base", f"{stats.get('total_films', 0):,}")
        with c4, st.container(border=True):
            st.metric("Prédictions", f"{stats.get('total_predictions', 0):,}")

        st.write("")
        col1, col2 = st.columns(2)
        with col1, st.container(border=True):
            st.markdown("**Distribution des sentiments**")
            if stats.get("by_sentiment"):
                df_sent = pd.DataFrame(list(stats["by_sentiment"].items()), columns=["Sentiment", "Nombre"])
                st.bar_chart(df_sent.set_index("Sentiment"), color=COLORS["accent"])
        with col2, st.container(border=True):
            st.markdown("**Avis par source**")
            if stats.get("by_source"):
                df_src = pd.DataFrame(list(stats["by_source"].items()), columns=["Source", "Nombre"])
                st.bar_chart(df_src.set_index("Source"), color=COLORS["success"])
    else:
        render_api_down()

    if conn:
        nb_pred = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]

        if nb_pred == 0:
            st.write("")
            empty_state("🤖", "Aucune prédiction en base",
                         "Lancez : python -m src.model.batch_predict")
        else:
            st.write("")
            st.markdown("### 🧠 Performance du modèle")

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
            df_matrix = pd.read_sql_query(
                """SELECT r.sentiment as Réel, p.predicted_sentiment as Prédit, COUNT(*) as Nombre
                   FROM reviews r JOIN predictions p ON r.id = p.review_id
                   WHERE r.sentiment IS NOT NULL
                   GROUP BY r.sentiment, p.predicted_sentiment""",
                conn,
            )

            col1, col2 = st.columns(2)
            with col1, st.container(border=True):
                st.markdown("**Distribution des scores de confiance**")
                st.bar_chart(df_conf.set_index("tranche"), color=COLORS["accent"])
            with col2, st.container(border=True):
                st.markdown("**Matrice de confusion**")
                if not df_matrix.empty:
                    pivot = df_matrix.pivot(index="Réel", columns="Prédit", values="Nombre").fillna(0).astype(int)
                    total = pivot.values.sum()
                    grid = '<div style="display:grid; grid-template-columns: auto 1fr 1fr; gap:8px;">'
                    grid += f'<div></div><div style="text-align:center;color:{COLORS["text_secondary"]};font-size:0.75rem;">Prédit POS</div>'
                    grid += f'<div style="text-align:center;color:{COLORS["text_secondary"]};font-size:0.75rem;">Prédit NEG</div>'
                    for real in ["positive", "negative"]:
                        grid += f'<div style="color:{COLORS["text_secondary"]};font-size:0.75rem;align-self:center;">Réel {real[:3].upper()}</div>'
                        for pred in ["positive", "negative"]:
                            val = int(pivot.loc[real, pred]) if real in pivot.index and pred in pivot.columns else 0
                            correct = real == pred
                            border = COLORS["success"] if correct else COLORS["danger"]
                            pct = (val / total * 100) if total else 0
                            grid += (
                                f'<div style="background:{border}18; border:1px solid {border}; border-radius:10px; '
                                f'padding:0.8rem; text-align:center;"><div style="font-size:1.3rem; font-weight:800;">{val}</div>'
                                f'<div style="font-size:0.7rem; color:{COLORS["text_secondary"]};">{pct:.1f}%</div></div>'
                            )
                    grid += "</div>"
                    st.markdown(grid, unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("**Prédictions les moins confiantes**")
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
                st.dataframe(df_low, width='stretch', hide_index=True)

        conn.close()
    else:
        empty_state("🗄️", "Base de données introuvable")

    st.write("")
    st.markdown("### 🚨 Monitoring")
    col1, col2 = st.columns(2)
    with col1, st.container(border=True):
        st.markdown("**Alertes actives**")
        alerts_data = api_call("GET", "/monitoring/alerts")
        if alerts_data:
            if alerts_data["alerts"]:
                for a in alerts_data["alerts"]:
                    st.markdown(badge_html(a, COLORS["danger"]), unsafe_allow_html=True)
            else:
                st.markdown(badge_html("✓ Aucune alerte active", COLORS["success"]), unsafe_allow_html=True)
    with col2, st.container(border=True):
        st.markdown("**Historique des health checks**")
        health_path = Path("logs/health_report.json")
        if health_path.exists():
            with open(health_path, "r", encoding="utf-8") as f:
                health_history = json.load(f)
            if health_history:
                df_health = pd.DataFrame(health_history)
                st.dataframe(df_health.tail(10), width='stretch', hide_index=True)
            else:
                st.caption("Historique vide.")
        else:
            st.caption("Aucun health check enregistré. Lancez : python -m src.monitoring.health_check")


# ══════════════════════════════════════════════════════════════
# Page 3 : Comparaison de modèles
# ══════════════════════════════════════════════════════════════

elif page == "🧪 Modèles":
    st.markdown("## 🧪 Comparaison de modèles")
    st.caption(
        "HuggingFace DistilBERT (pré-entraîné) vs modèle custom TF-IDF + Régression Logistique "
        "(entraîné sur nos données) vs TextBlob (lexical)."
    )

    comparison = api_call("GET", "/models/comparison")
    if comparison:
        models_data = comparison["models"]
        df_compare = pd.DataFrame(models_data).T
        df_compare.index.name = "Modèle"
        best_model = df_compare["accuracy"].astype(float).idxmax()

        with st.container(border=True):
            st.caption(f"Échantillon : {comparison['sample_size']} avis — généré le {comparison['generated_at'][:19]}")

            def _highlight_best(row):
                if row.name == best_model:
                    return [f"background-color: {COLORS['success']}33; color: {COLORS['text']}"] * len(row)
                return [""] * len(row)

            styled = df_compare.style.apply(_highlight_best, axis=1)
            st.dataframe(styled, width='stretch')
            st.markdown(
                f"🏆 Meilleur modèle sur cet échantillon : {badge_html(best_model, COLORS['success'])}",
                unsafe_allow_html=True,
            )

        st.write("")
        col1, col2 = st.columns(2)
        with col1, st.container(border=True):
            st.markdown("**Accuracy par modèle**")
            st.bar_chart(df_compare["accuracy"], color=COLORS["accent"])
        with col2, st.container(border=True):
            st.markdown("**Latence moyenne (ms/avis)**")
            st.bar_chart(df_compare["avg_latency_ms"], color=COLORS["success"])
    else:
        empty_state("🧪", "Comparaison indisponible", "Lancez : python -m src.model.compare_models")

    st.write("")
    st.markdown("### 🔬 Tester un texte sur les 3 modèles")
    with st.container(border=True):
        test_text = st.text_input(
            "Texte à tester", placeholder="This film changed the way I see cinema forever...",
            label_visibility="collapsed",
        )
        run_test = st.button("Comparer maintenant", type="primary")

    if run_test and test_text:
        if len(test_text.strip()) < 5:
            st.warning("Saisissez au moins 5 caractères.")
        else:
            with st.spinner("Comparaison en cours..."):
                compare_result = api_call("POST", "/predict/compare", json={"text": test_text})
                custom_result = api_call("POST", "/predict/custom", json={"text": test_text})

            if compare_result:
                hf = compare_result["models"]["huggingface_distilbert"]
                tb = compare_result["models"]["textblob"]
                cols = st.columns(3)
                with cols[0]:
                    render_mini_model_card("HuggingFace DistilBERT", hf["sentiment"], hf["score"], hf["time_ms"])
                with cols[1]:
                    if custom_result:
                        render_mini_model_card(
                            "TF-IDF + LogReg (custom)", custom_result["sentiment"],
                            custom_result["score"], custom_result["processing_time_ms"],
                        )
                    else:
                        empty_state("🧪", "Modèle custom indisponible")
                with cols[2]:
                    if tb["sentiment"] != "unavailable":
                        render_mini_model_card("TextBlob", tb["sentiment"], tb["score"], tb["time_ms"])
                    else:
                        empty_state("📚", "TextBlob non installé")


# ══════════════════════════════════════════════════════════════
# Page 4 : Films
# ══════════════════════════════════════════════════════════════

elif page == "🎥 Films":
    st.markdown("## 🎥 Explorer les films")

    conn = get_db()
    if conn:
        nb_films = conn.execute("SELECT COUNT(*) FROM films").fetchone()[0]

        if nb_films == 0:
            empty_state("🎬", "Aucun film en base", "Lancez : python -m src.db.import_films")
        else:
            st.caption(f"{nb_films} films en base")

            df_films = pd.read_sql_query(
                """SELECT f.title, f.vote_average as note_tmdb, f.genre_ids as genres,
                          COUNT(r.id) as nb_avis,
                          ROUND(SUM(CASE WHEN r.sentiment = 'positive' THEN 1.0 ELSE 0.0 END) / COUNT(r.id) * 100, 1) as pct_positif
                   FROM films f
                   INNER JOIN reviews r ON f.id = r.film_id
                   GROUP BY f.id
                   HAVING nb_avis >= 2
                   ORDER BY nb_avis DESC
                   LIMIT 30""",
                conn,
            )

            if df_films.empty:
                empty_state("🎬", "Aucun avis lié à un film", "Lancez : python -m src.db.import_films")
            else:
                for i in range(0, len(df_films), 3):
                    row_films = df_films.iloc[i:i + 3]
                    cols = st.columns(3)
                    for col, (_, film) in zip(cols, row_films.iterrows()):
                        with col, st.container(border=True):
                            pct = film["pct_positif"] or 0
                            bar_color = COLORS["success"] if pct >= 60 else (
                                COLORS["danger"] if pct < 40 else "#F59E0B"
                            )
                            note = film["note_tmdb"]
                            st.markdown(
                                f"""
                                <div style="min-height:3.2em;">
                                    <div style="font-weight:700; font-size:1rem;">{film['title']}</div>
                                    <div style="color:{COLORS["text_secondary"]}; font-size:0.8rem; margin-top:0.2rem;">
                                        ⭐ {note:.1f} TMDB · {int(film['nb_avis'])} avis
                                    </div>
                                </div>
                                <div style="background:{COLORS["border"]}; border-radius:999px; height:10px;
                                            margin-top:0.7rem; overflow:hidden;">
                                    <div style="background:{bar_color}; width:{pct}%; height:100%;"></div>
                                </div>
                                <div style="text-align:right; color:{COLORS["text_secondary"]}; font-size:0.72rem; margin-top:0.2rem;">
                                    {pct:.0f}% positif
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

            st.write("")
            with st.container(border=True):
                st.markdown("**Catalogue complet**")
                df_all = pd.read_sql_query(
                    "SELECT title, vote_average, genre_ids, release_date FROM films ORDER BY vote_average DESC",
                    conn,
                )
                st.dataframe(df_all, width='stretch', hide_index=True)

        conn.close()
    else:
        empty_state("🗄️", "Base de données introuvable")


# ══════════════════════════════════════════════════════════════
# Page 5 : Recherche
# ══════════════════════════════════════════════════════════════

elif page == "🔍 Recherche":
    st.markdown("## 🔍 Recherche d'avis")

    with st.container(border=True):
        query = st.text_input(
            "Mot-clé", placeholder="🔍  fantastic, boring, acting...", label_visibility="collapsed"
        )

    if query and len(query) >= 2:
        result = api_call("GET", f"/search?q={query}")
        if result:
            if result["count"] == 0:
                empty_state("🔍", "Aucun résultat", f"Rien ne correspond à « {result['query']} »")
            else:
                st.caption(f"{result['count']} résultat(s) pour « {result['query']} »")

                if result.get("reviews"):
                    df_export = pd.DataFrame(result["reviews"])
                    safe_query = re.sub(r"[^a-zA-Z0-9]+", "_", query).strip("_") or "recherche"
                    st.download_button(
                        "📥 Exporter les résultats en CSV",
                        data=df_export.to_csv(index=False).encode("utf-8"),
                        file_name=f"recherche_{safe_query}.csv",
                        mime="text/csv",
                    )

                st.write("")
                for r in result.get("reviews", []):
                    color, icon = sentiment_style(r.get("sentiment", "negative"))
                    with st.container(border=True):
                        st.markdown(
                            f"""
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <div>{badge_html(f"{icon} {(r.get('sentiment') or '?').upper()}", color)}
                                &nbsp;&nbsp;<span style="color:{COLORS["text_secondary"]}; font-size:0.8rem;">
                                #{r['id']} · {r['source']}</span></div>
                            </div>
                            <div style="margin-top:0.6rem; color:{COLORS["text"]};">
                                {r["review_text"][:400]}{"..." if len(r["review_text"]) > 400 else ""}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
    else:
        empty_state("🔍", "Lancez une recherche", "Saisissez au moins 2 caractères ci-dessus.")


# ══════════════════════════════════════════════════════════════
# Page 6 : Analyse avancée
# ══════════════════════════════════════════════════════════════

elif page == "📈 Avancé":
    st.markdown("## 📈 Analyse avancée")

    conn = get_db()
    if conn:
        with st.container(border=True):
            st.markdown("**Distribution des scores de qualité**")
            df_quality = pd.read_sql_query(
                "SELECT quality_score FROM reviews WHERE quality_score IS NOT NULL", conn
            )
            if not df_quality.empty:
                fig, ax = styled_fig((8, 3))
                ax.hist(df_quality["quality_score"], bins=20, color=COLORS["accent"], edgecolor=COLORS["bg"])
                ax.set_xlabel("Score de qualité")
                ax.set_ylabel("Nombre d'avis")
                st.pyplot(fig)
            else:
                st.caption("Aucun score de qualité en base.")

        st.write("")
        st.markdown("### Mots les plus fréquents par sentiment")
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
        with col1, st.container(border=True):
            st.markdown(f"**{badge_html('POSITIFS', COLORS['success'])}**", unsafe_allow_html=True)
            st.bar_chart(word_frequencies("positive").set_index("mot"), color=COLORS["success"])
        with col2, st.container(border=True):
            st.markdown(f"**{badge_html('NÉGATIFS', COLORS['danger'])}**", unsafe_allow_html=True)
            st.bar_chart(word_frequencies("negative").set_index("mot"), color=COLORS["danger"])

        st.write("")
        st.markdown("### Mots les plus discriminants (modèle custom)")
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
            with col1, st.container(border=True):
                st.markdown(f"**Top 10 mots → {model.classes_[1]}**")
                st.dataframe(
                    pd.DataFrame({"mot": feature_names[top_positive_idx], "coefficient": coefs[top_positive_idx]}),
                    width='stretch', hide_index=True,
                )
            with col2, st.container(border=True):
                st.markdown(f"**Top 10 mots → {model.classes_[0]}**")
                st.dataframe(
                    pd.DataFrame({"mot": feature_names[top_negative_idx], "coefficient": coefs[top_negative_idx]}),
                    width='stretch', hide_index=True,
                )
        else:
            empty_state("🧪", "Modèle custom non entraîné", "Lancez : python -m src.model.train_model")

        st.write("")
        with st.container(border=True):
            st.markdown("**Corrélation note du film vs sentiment moyen des avis**")
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

                fig, ax = styled_fig((8, 4))
                ax.scatter(df_corr["note"], df_corr["pct_positif"], color=COLORS["accent"], alpha=0.8)
                ax.set_xlabel("Note du film (TMDB — IMDB non disponible en base actuellement)")
                ax.set_ylabel("% d'avis positifs")
                st.pyplot(fig)
                st.caption(f"Basé sur {len(df_corr)} films ayant au moins 3 avis liés et une note connue.")
            else:
                st.caption("Pas assez de films avec avis liés et note connue pour calculer une corrélation.")

        conn.close()
    else:
        empty_state("🗄️", "Base de données introuvable")
