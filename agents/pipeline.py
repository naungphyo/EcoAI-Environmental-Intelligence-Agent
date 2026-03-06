"""
agents/pipeline.py - Enhanced pipeline with query expansion
"""

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from config.settings import MAX_TOTAL_ARTICLES
from tools.newsapi_tool import fetch_newsapi_structured
from tools.gnews_tool import fetch_gnews_structured
from tools.gdelt_tool import fetch_gdelt_structured
from utils.text import deduplicate_articles, sentiment_score
from agents.trend_detector import detect_trends
from agents.insight_extractor import extract_insights


def run_pipeline(question: str) -> dict:
    """Main pipeline with smart query expansion"""
    try:
        t0 = time.perf_counter()

        # Import query expander
        try:
            from agents.query_expander import expand_query, deduplicate_across_sentiment
            use_expansion = True
        except ImportError:
            print("[Pipeline] Query expander not found, using simple retrieval")
            use_expansion = False

        # Step 1: Retrieve
        print(f"[Pipeline] Retrieving articles for: {question}")
        all_articles = []

        if use_expansion:
            # Use query expansion
            expanded = expand_query(question)
            print(
                f"[Pipeline] Detected topics: {', '.join(expanded['topics'][:3])}")

            # Fetch with primary queries
            for query in expanded["primary"][:2]:  # Limit to 2 primary
                print(f"[Pipeline] Primary query: {query}")
                for fetcher in [fetch_newsapi_structured, fetch_gnews_structured, fetch_gdelt_structured]:
                    try:
                        results = fetcher(query)
                        for art in results:
                            art.setdefault("retriever", fetcher.__name__)
                            art.setdefault("query_type", "primary")
                        all_articles.extend(results)
                    except Exception as exc:
                        print(f"[Pipeline] {fetcher.__name__} failed: {exc}")

            # Add balanced queries (fewer articles for diversity)
            balanced_queries = (
                expanded["positive"][:1] +
                expanded["negative"][:1] +
                expanded["neutral"][:1]
            )
            for query in balanced_queries:
                print(f"[Pipeline] Balanced query: {query}")
                try:
                    results = fetch_gnews_structured(query)
                    for art in results[:2]:  # Only top 2
                        art.setdefault("retriever", "gnews_balanced")
                        art.setdefault("query_type", "balanced")
                    all_articles.extend(results)
                except Exception as exc:
                    print(f"[Pipeline] Balanced query failed: {exc}")
        else:
            # Simple retrieval without expansion
            fetchers = [fetch_newsapi_structured,
                        fetch_gnews_structured, fetch_gdelt_structured]
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(fn, question)
                                       : fn.__name__ for fn in fetchers}
                for future in as_completed(futures):
                    try:
                        results = future.result()
                        for art in results:
                            art.setdefault("retriever", futures[future])
                        all_articles.extend(results)
                    except Exception as exc:
                        print(f"[Pipeline] {futures[future]} failed: {exc}")

        print(f"[Pipeline] Retrieved {len(all_articles)} total articles")

        # Step 2: Deduplicate and balance
        if use_expansion:
            articles = deduplicate_across_sentiment(all_articles)
            print(
                f"[Pipeline] After sentiment balancing: {len(articles)} articles")
        else:
            articles = deduplicate_articles(all_articles)
            print(f"[Pipeline] After deduplication: {len(articles)} articles")

        # Step 3: Filter and score relevance
        question_lower = question.lower()
        question_keywords = set(re.findall(r"\b[a-z]{4,}\b", question_lower))

        for art in articles:
            combined = f"{art.get('title', '')} {art.get('body', '')}".lower()
            article_keywords = set(re.findall(r"\b[a-z]{4,}\b", combined))
            overlap = len(question_keywords & article_keywords)
            art["relevance_score"] = overlap / (len(question_keywords) or 1)

            # Add sentiment if not already present
            if "sentiment" not in art:
                art["sentiment"] = sentiment_score(combined)

        # Filter low relevance
        articles = [a for a in articles if a.get("relevance_score", 0) >= 0.15]

        # Sort by relevance and recency
        articles.sort(
            key=lambda a: (-a.get("relevance_score", 0),
                           a.get("published_at", "")),
            reverse=True
        )
        articles = articles[:MAX_TOTAL_ARTICLES]

        print(f"[Pipeline] After filtering: {len(articles)} relevant articles")

        # Step 4: Analyze
        print("[Pipeline] Analyzing trends and insights...")
        with ThreadPoolExecutor(max_workers=2) as pool:
            f_trends = pool.submit(detect_trends, articles)
            f_insights = pool.submit(extract_insights, articles)
            trend_report = f_trends.result()
            insight_report = f_insights.result()

        # Step 5: Summarize
        print("[Pipeline] Generating summary...")
        summary = _generate_summary(question, articles)

        # Step 6: Format sources
        sources = [
            {
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "url": a.get("url", ""),
                "published": a.get("published_at", "")[:10],
                "sentiment": a.get("sentiment", {}).get("label", ""),
            }
            for a in articles
        ]

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        return {
            "question": question,
            "articles": articles,
            "trend_report": trend_report,
            "insight_report": insight_report,
            "summary": summary,
            "final_answer": summary,
            "sources": sources,
            "elapsed_ms": elapsed_ms,
            "error": None,
        }

    except Exception as exc:
        print(f"[Pipeline] FATAL ERROR: {exc}")
        import traceback
        traceback.print_exc()

        # Return error state instead of None
        return {
            "question": question,
            "articles": [],
            "trend_report": None,
            "insight_report": None,
            "summary": f"⚠️ Error: {exc}",
            "final_answer": f"⚠️ Pipeline error: {exc}",
            "sources": [],
            "elapsed_ms": 0,
            "error": str(exc),
        }


def _generate_summary(question: str, articles: List[dict]) -> str:
    """Generate summary using LLM or fallback"""
    if not articles:
        return "⚠️ No relevant articles found. Try rephrasing your question."

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    backend = os.environ.get("LLM_BACKEND", "groq")

    print(
        f"[Summary] Backend={backend}, Groq={'SET' if groq_key else 'MISSING'}, Gemini={'SET' if gemini_key else 'MISSING'}")

    use_llm = (backend == "gemini" and gemini_key) or (
        backend == "groq" and groq_key)

    if not use_llm:
        print("[Summary] No valid LLM config, using fallback")
        return _build_fallback_summary(question, articles)

    # Build context
    context_parts = []
    for i, art in enumerate(articles[:8], 1):
        snippet = (art.get("body") or art.get("title", ""))[:700]
        relevance = art.get("relevance_score", 0)
        context_parts.append(
            f"[{i}] {art['source']} ({art.get('published_at', '')[:10]}) [Relevance: {relevance:.0%}]\n"
            f"Title: {art['title']}\n{snippet}\n"
        )

    prompt = f"""You are EcoAI, a precise environmental news analyst.

USER QUESTION: {question}

RETRIEVED ARTICLES (sorted by relevance):
{"".join(context_parts)}

CRITICAL INSTRUCTIONS:
1. Answer ONLY what the user asked - stay laser-focused on their question
2. Use ONLY facts from the articles above - cite sources as [1], [2], etc.
3. If the question asks for specific data (numbers, dates, policies), prioritize those
4. If articles don't fully answer the question, state what's missing
5. Synthesize multiple sources when they discuss the same topic
6. Be factual and precise - no speculation
7. Keep answer under 350 words

ANSWER:"""

    try:
        from agents.llm_client import get_llm
        print("[Summary] Calling LLM...")
        llm = get_llm(temperature=0.15, max_new_tokens=900)
        summary = llm.invoke(prompt)
        if hasattr(summary, "content"):
            summary = summary.content
        result = str(summary).strip()
        print(f"[Summary] LLM returned {len(result)} chars")
        return result
    except Exception as exc:
        print(f"[Summary] LLM failed: {exc}")
        return _build_fallback_summary(question, articles)


def _build_fallback_summary(question: str, articles: List[dict]) -> str:
    """Rule-based summary when no LLM"""
    emoji_map = {"Positive": "🟢", "Negative": "🔴", "Neutral": "🟡"}
    lines = [f"### 📰 Latest Environmental News: {question}\n"]

    for i, art in enumerate(articles[:8], 1):
        sent = art.get("sentiment", {}).get("label", "Neutral")
        emoji = emoji_map.get(sent, "📄")
        date = art.get("published_at", "")[:10]
        src = art.get("source", "")
        title = art.get("title", "Untitled")
        body = (art.get("body") or "")[:180]

        lines.append(f"{emoji} **[{i}] {title}**")
        lines.append(f"*Source: {src} · Published: {date}*")
        lines.append(f"{body}…\n")

    return "\n".join(lines)
