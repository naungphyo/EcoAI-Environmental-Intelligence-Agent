"""
tools/newsapi_tool.py
──────────────────────
NewsAPI retrieval (no LangChain tool decorator)
"""

import requests
from typing import List

from config.settings import (
    NEWS_API_KEY, MAX_ARTICLES_PER_SOURCE,
    ARTICLE_MAX_CHARS, REQUEST_TIMEOUT,
)
from utils.cache import cache_get, cache_set
from utils.text import clean_html, truncate


def _fetch_newsapi(query: str, page_size: int = MAX_ARTICLES_PER_SOURCE) -> List[dict]:
    if not NEWS_API_KEY:
        return []

    cache_key = f"newsapi::{query}::{page_size}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        print(f"[NewsAPI] Request failed: {exc}")
        return []

    articles = []
    for item in data.get("articles", []):
        body = clean_html(item.get("content") or item.get("description") or "")
        articles.append({
            "title":       item.get("title", "Untitled"),
            "url":         item.get("url", ""),
            "source":      item.get("source", {}).get("name", "NewsAPI"),
            "published_at": item.get("publishedAt", ""),
            "body":        truncate(body, ARTICLE_MAX_CHARS),
        })

    cache_set(cache_key, articles)
    return articles


def fetch_newsapi_structured(query: str) -> List[dict]:
    """Public helper for pipeline use (returns raw dicts)."""
    return _fetch_newsapi(query)
