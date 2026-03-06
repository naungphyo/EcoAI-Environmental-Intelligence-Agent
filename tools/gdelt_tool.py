"""
tools/gdelt_tool.py
────────────────────
GDELT retrieval (no LangChain tool decorator)
"""

from typing import List
import requests

from config.settings import (
    GDELT_DOC_API, MAX_ARTICLES_PER_SOURCE,
    ARTICLE_MAX_CHARS, REQUEST_TIMEOUT,
)
from utils.cache import cache_get, cache_set
from utils.text import clean_html, truncate


def _fetch_gdelt(query: str, max_items: int = MAX_ARTICLES_PER_SOURCE) -> List[dict]:
    cache_key = f"gdelt::{query}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    params = {
        "query":      query,
        "mode":       "artlist",
        "maxrecords": max_items,
        "format":     "json",
        "timespan":   "1d",
        "sort":       "DateDesc",
    }

    try:
        resp = requests.get(GDELT_DOC_API, params=params,
                            timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"[GDELT] Request failed: {exc}")
        return []

    articles: List[dict] = []
    for item in (data.get("articles") or [])[:max_items]:
        articles.append({
            "title":        item.get("title", "Untitled"),
            "url":          item.get("url", ""),
            "source":       item.get("domain", "GDELT"),
            "published_at": item.get("seendatetime", "")[:10] + "T00:00:00Z",
            "body":         truncate(item.get("title", ""), ARTICLE_MAX_CHARS),
        })

    cache_set(cache_key, articles)
    return articles


def fetch_gdelt_structured(query: str) -> List[dict]:
    """Public helper for pipeline use (returns raw dicts)."""
    return _fetch_gdelt(query)
