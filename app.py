"""
app.py
───────
EcoAI – Environmental Intelligence Agent
Streamlit frontend with a clean, nature-inspired dark interface.

Run:  streamlit run app.py
"""

from utils.cache import cache_clear_expired
from agents.insight_extractor import format_insight_report
from agents.trend_detector import format_trend_report
from agents.pipeline import run_pipeline
import pandas as pd
import streamlit as st
import time
import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(__file__))


# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="EcoAI – Environmental Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS – nature-inspired dark theme ───────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500&display=swap');

  /* Base */
  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d1f17;
    color: #d4e8d0;
  }

  /* Hide Streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }

  /* ── Hero header ── */
  .hero {
    background: linear-gradient(135deg, #0a2e1a 0%, #14432a 60%, #0f3321 100%);
    border: 1px solid #2d6a45;
    border-radius: 16px;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: "";
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, #3a8c5c33 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    color: #7dcf96;
    margin: 0;
    line-height: 1.1;
  }
  .hero-sub {
    color: #8fb89a;
    font-size: 1.05rem;
    margin-top: 0.4rem;
    font-weight: 300;
  }

  /* ── Metric cards ── */
  .metric-row { display: flex; gap: 1rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
  .metric-card {
    background: #122b1e;
    border: 1px solid #265c3a;
    border-radius: 12px;
    padding: 0.9rem 1.3rem;
    flex: 1 1 140px;
    min-width: 120px;
  }
  .metric-label { font-size: 0.72rem; color: #6a9a78; text-transform: uppercase; letter-spacing: 0.06em; }
  .metric-value { font-size: 1.7rem; font-weight: 500; color: #7dcf96; line-height: 1.2; }

  /* ── Answer box ── */
  .answer-box {
    background: #0e2618;
    border-left: 4px solid var(--green2);
    border-radius: 0 12px 12px 0;
    padding: 1.5rem 1.8rem;
    line-height: 1.9;
    font-size: 1.05rem;        /* Was 0.92rem - BIGGER NOW */
    margin-bottom: 1.2rem;
    position: relative;
    letter-spacing: 0.01em;
  }

  /* ── Source badge ── */
  .source-badge {
    display: inline-block;
    background: #1a3d28;
    border: 1px solid #2f6344;
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.78rem;
    color: #8fd4a8;
    margin: 0.2rem;
  }

  /* ── Sentiment pill ── */
  .sentiment-pos { color: #4caf79; font-weight: 600; }
  .sentiment-neg { color: #e57373; font-weight: 600; }
  .sentiment-neu { color: #90a4ae; font-weight: 600; }

  /* ── Section headers ── */
  .section-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem;
    color: #7dcf96;
    border-bottom: 1px solid #2a5438;
    padding-bottom: 0.3rem;
    margin: 1.4rem 0 0.8rem;
  }

  /* ── Input area ── */
  .stTextArea textarea {
    background-color: #112419 !important;
    border: 1px solid #2d6a45 !important;
    color: #d4e8d0 !important;
    border-radius: 10px !important;
  }
  .stButton > button {
    background: linear-gradient(135deg, #2d8a52, #1e6b3e) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 2rem !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    transition: opacity 0.2s;
  }
  .stButton > button:hover { opacity: 0.88; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background-color: #0c1d14 !important;
    border-right: 1px solid #1e4a2c;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab"] {
    color: #7dcf96 !important;
    background: transparent;
  }
  .stTabs [aria-selected="true"] {
    border-bottom: 2px solid #4caf79 !important;
  }

  /* ── Keyword chip ── */
  .kw-chip {
    display: inline-block;
    background: #1a3d28;
    border: 1px solid #3a6e50;
    border-radius: 6px;
    padding: 0.15rem 0.55rem;
    font-size: 0.82rem;
    color: #a8dbb8;
    margin: 0.15rem;
    font-family: 'Courier New', monospace;
  }
  
  /* ── Spinner overlay ── */
  .loading-msg {
    font-size: 0.9rem;
    color: #6a9a78;
    font-style: italic;
  }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌿 EcoAI Settings")
    st.markdown("---")

    st.markdown("**AI Engine**")
    backend_options = {
        "Groq Llama 3.1 70B (Ultra-fast)": "groq",
        "Google Gemini Flash (Fast)": "gemini",
    }
    selected = st.selectbox(
        "Choose AI engine",
        list(backend_options.keys()),
        index=0,
        help="Both are 100% free! Groq is fastest.",
    )
    os.environ["LLM_BACKEND"] = backend_options[selected]

# ── Hero Section ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">🌿 EcoAI</div>
  <div class="hero-sub">Environmental Intelligence Agent · Live News · Multi-Source Analysis</div>
</div>
""", unsafe_allow_html=True)


# ── Question Input ────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill_question", "")
question = st.text_area(
    "Ask an environmental question:",
    value=prefill,
    placeholder="e.g. What are the latest developments in renewable energy policy?",
    height=90,
)

col_btn, col_info = st.columns([2, 5])
with col_btn:
    run_btn = st.button("🔍 Analyse", use_container_width=True)
with col_info:
    st.markdown(
        "<p class='loading-msg'>Fetches live news · Detects trends · Extracts insights · Summarises with AI</p>",
        unsafe_allow_html=True,
    )

# ── Results ───────────────────────────────────────────────────────────────────
if run_btn and question.strip():
    # NEW: Show query expansion strategy FIRST
    with st.expander("🎯 Query Strategy", expanded=False):
        from agents.query_expander import expand_query, explain_query_strategy
        expanded = expand_query(question.strip())
        st.markdown(explain_query_strategy(expanded))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Primary Queries:**")
            for q in expanded["primary"]:
                st.markdown(f"- `{q}`")
        with col2:
            st.markdown("**Positive Frame:**")
            for q in expanded["positive"]:
                st.markdown(f"- `{q}`")
        with col3:
            st.markdown("**Neutral Frame:**")
            for q in expanded["neutral"]:
                st.markdown(f"- `{q}`")

    # THEN show spinner and run pipeline
    with st.spinner("🌐 Fetching live environmental news..."):
        result = run_pipeline(question.strip())

    articles = result.get("articles", [])
    trend_report = result.get("trend_report")
    insight_report = result.get("insight_report")
    final_answer = result.get("final_answer", "")
    sources = result.get("sources", [])
    elapsed = result.get("elapsed_ms", 0)

    # ── Metrics Row ──────────────────────────────────────────────────────────
    recency_pct = f"{trend_report.recency_score:.0%}" if trend_report else "—"
    dominant = trend_report.dominant_trend if trend_report else "—"
    consensus = insight_report.cross_source_agreement if insight_report else "—"

    st.markdown(f"""
    <div class="metric-row">
      <div class="metric-card">
        <div class="metric-label">Articles Retrieved</div>
        <div class="metric-value">{len(articles)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Response Time</div>
        <div class="metric-value">{elapsed:.0f}<small style="font-size:0.9rem">ms</small></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Data Freshness</div>
        <div class="metric-value">{recency_pct}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Source Consensus</div>
        <div class="metric-value" style="font-size:1.1rem">{consensus}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Trending Topic</div>
        <div class="metric-value" style="font-size:0.95rem">{dominant}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main tabs ─────────────────────────────────────────────────────────────
    tab_answer, tab_trends, tab_insights, tab_sources, tab_compare = st.tabs([
        "🤖 AI Answer",
        "📈 Trends",
        "⚡ Insights",
        "📰 Sources",
        "🔍 Compare",
    ])

    # ── TAB 1: AI Answer ─────────────────────────────────────────────────────
    with tab_answer:
        st.markdown(
            '<div class="section-header">AI-Generated Summary</div>', unsafe_allow_html=True)
        if final_answer:
            st.markdown(
                f'<div class="answer-box">{final_answer}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("No answer generated. Check your LLM configuration.")

        if sources:
            st.markdown(
                '<div class="section-header">Sources Used</div>', unsafe_allow_html=True)
            for s in sources[:8]:
                sentiment_cls = {
                    "Positive": "sentiment-pos",
                    "Negative": "sentiment-neg",
                }.get(s["sentiment"], "sentiment-neu")

                st.markdown(
                    f'<span class="source-badge">🗞️ {s["source"]} · {s["published"]}</span>',
                    unsafe_allow_html=True,
                )
                col_t, col_s = st.columns([6, 1])
                with col_t:
                    if s["url"]:
                        st.markdown(f'[{s["title"][:90]}]({s["url"]})')
                    else:
                        st.markdown(s["title"][:90])
                with col_s:
                    st.markdown(
                        f'<span class="{sentiment_cls}">{s["sentiment"]}</span>',
                        unsafe_allow_html=True,
                    )

    # ── TAB 2: Trends ─────────────────────────────────────────────────────────
    with tab_trends:
        if trend_report:
            col_l, col_r = st.columns([1, 1])
            with col_l:
                st.markdown(
                    '<div class="section-header">🔑 Top Keywords</div>', unsafe_allow_html=True)
                kw_html = "".join(
                    f'<span class="kw-chip">{kw} <b>×{freq}</b></span>'
                    for kw, freq in trend_report.top_keywords[:8]
                )
                st.markdown(kw_html, unsafe_allow_html=True)

                if trend_report.cross_source_topics:
                    st.markdown(
                        '<div class="section-header">🤝 Cross-Source Topics</div>', unsafe_allow_html=True)
                    cs_html = "".join(
                        f'<span class="kw-chip" style="border-color:#5aaa80">{t}</span>'
                        for t in trend_report.cross_source_topics
                    )
                    st.markdown(cs_html, unsafe_allow_html=True)

            with col_r:
                if trend_report.source_breakdown:
                    st.markdown(
                        '<div class="section-header">📡 Articles per Source</div>', unsafe_allow_html=True)
                    df_src = pd.DataFrame(
                        list(trend_report.source_breakdown.items()),
                        columns=["Source", "Articles"],
                    ).sort_values("Articles", ascending=False)
                    st.bar_chart(df_src.set_index("Source"), color="#4caf79")

            # Date distribution sparkline
            if trend_report.date_distribution:
                dates = {
                    k: v for k, v in trend_report.date_distribution.items() if k != "unknown"}
                if dates:
                    st.markdown(
                        '<div class="section-header">📅 Publication Timeline</div>',
                        unsafe_allow_html=True
                    )
                    df_dates = pd.DataFrame(
                        list(dates.items()),
                        columns=["Date", "Articles"],
                    ).sort_values("Date")
                    st.line_chart(df_dates.set_index("Date"), color="#7dcf96")
        else:
            st.info("No trend data available.")

    # ── TAB 3: Insights ────────────────────────────────────────────────────────
    with tab_insights:
        if insight_report:
            col_a, col_b = st.columns([1, 1])

            with col_a:
                st.markdown(
                    '<div class="section-header">⚡ Actionable Items</div>', unsafe_allow_html=True)
                if insight_report.actionable_sentences:
                    for sentence in insight_report.actionable_sentences[:6]:
                        st.markdown(f"• {sentence.strip()}")
                else:
                    st.markdown(
                        "_No specific action items detected in this batch._")

            with col_b:
                st.markdown(
                    '<div class="section-header">📊 Key Statistics</div>', unsafe_allow_html=True)
                if insight_report.quantified_facts:
                    for fact in insight_report.quantified_facts[:5]:
                        st.markdown(f"• {fact.strip()}")
                else:
                    st.markdown("_No quantified data found._")

            # Sentiment distribution
            st.markdown(
                '<div class="section-header">🎭 Sentiment Overview</div>', unsafe_allow_html=True)
            sentiments = [r["sentiment"]
                          for r in insight_report.source_comparison]
            if sentiments:
                from collections import Counter
                sent_counts = Counter(sentiments)
                df_sent = pd.DataFrame(
                    [{"Sentiment": k, "Count": v}
                        for k, v in sent_counts.items()]
                )
                colors = {"Positive": "#4caf79",
                          "Negative": "#e57373", "Neutral": "#90a4ae"}
                st.bar_chart(
                    df_sent.set_index("Sentiment"),
                    color="#4caf79",
                )

    # ── TAB 4: Sources ─────────────────────────────────────────────────────────
    with tab_sources:
        st.markdown(
            '<div class="section-header">📰 All Retrieved Articles</div>', unsafe_allow_html=True)
        if articles:
            for art in articles:
                sent = art.get("sentiment", {})
                sent_label = sent.get("label", "Neutral")
                sent_cls = {"Positive": "sentiment-pos",
                            "Negative": "sentiment-neg"}.get(sent_label, "sentiment-neu")

                with st.expander(f"🗞️ {art.get('title', 'Untitled')[:85]}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.markdown(f"**Source:** {art.get('source', '—')}")
                    with c2:
                        st.markdown(
                            f"**Published:** {art.get('published_at', '—')[:10]}")
                    with c3:
                        st.markdown(
                            f'<span class="{sent_cls}">{sent_label}</span>',
                            unsafe_allow_html=True,
                        )
                    if art.get("body"):
                        st.markdown(art["body"][:600])
                    if art.get("url"):
                        st.markdown(f"[🔗 Read full article]({art['url']})")
        else:
            st.info("No articles retrieved. Try a different query or check API keys.")

    # ── TAB 5: Compare Sources ────────────────────────────────────────────────
    with tab_compare:
        st.markdown(
            '<div class="section-header">🔍 Source Comparison Matrix</div>', unsafe_allow_html=True)
        if insight_report and insight_report.source_comparison:
            df_comp = pd.DataFrame(insight_report.source_comparison)[
                ["source", "title", "sentiment", "score", "angle", "published"]
            ].rename(columns={
                "source": "Source",
                "title": "Headline",
                "sentiment": "Sentiment",
                "score": "Score",
                "angle": "Editorial Angle",
                "published": "Date",
            })

            # Colour-code sentiment column
            def colour_sentiment(val):
                colour = {"Positive": "#2d5a3d",
                          "Negative": "#5a2d2d"}.get(val, "#2d3a3a")
                return f"background-color: {colour}"

            st.dataframe(
                df_comp.style.applymap(colour_sentiment, subset=["Sentiment"]),
                use_container_width=True,
                height=380,
            )

            # Editorial angle breakdown
            st.markdown(
                '<div class="section-header">📐 Editorial Angles</div>', unsafe_allow_html=True)
            from collections import Counter
            angle_counts = Counter(r["angle"]
                                   for r in insight_report.source_comparison)
            df_angles = pd.DataFrame(
                [{"Angle": k, "Count": v}
                    for k, v in angle_counts.most_common()],
            )
            if not df_angles.empty:
                st.bar_chart(df_angles.set_index("Angle"), color="#7dcf96")
        else:
            st.info("Run a query to see source comparison.")

elif run_btn and not question.strip():
    st.warning("Please enter a question before clicking Analyse.")

# ── Empty state ───────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem; color: #4a7a5a;">
      <div style="font-size: 3rem">🌍</div>
      <div style="font-size: 1.1rem; margin-top: 0.5rem;">
        Enter an environmental question above to get started.
      </div>
      <div style="font-size: 0.85rem; margin-top: 0.3rem; color: #3a6050;">
        Live data · Trend detection · Actionable insights · Source comparison
      </div>
    </div>
    """, unsafe_allow_html=True)
