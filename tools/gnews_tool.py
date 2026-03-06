"""
tools/gnews_tool.py
────────────────────
Google News RSS (no LangChain tool decorator)
"""

import email.utils
import xml.etree.ElementTree as ET
from typing import List
from urllib.parse import quote_plus

import requests

from config.settings import (
    GOOGLE_NEWS_RSS, MAX_ARTICLES_PER_SOURCE,
    ARTICLE_MAX_CHARS, REQUEST_TIMEOUT,
)
from utils.cache import cache_get, cache_set
from utils.text import clean_html, truncate


def _parse_rfc2822(date_str: str) -> str:
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return date_str


def _fetch_gnews(query: str, max_items: int = MAX_ARTICLES_PER_SOURCE) -> List[dict]:
    cache_key = f"gnews::{query}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    url = GOOGLE_NEWS_RSS.format(query=quote_plus(query))
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": "EcoAI/1.0"})
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[GNews] Request failed: {exc}")
        return []

    articles: List[dict] = []
    try:
        root = ET.fromstring(resp.text)
        channel = root.find("channel")
        if channel is None:
            return []

        for item in list(channel.findall("item"))[:max_items]:
            title = item.findtext("title", "Untitled")
            link = item.findtext("link", "")
            pub_raw = item.findtext("pubDate", "")
            desc = clean_html(item.findtext("description", ""))
            source_el = item.find("source")
            source = source_el.text if source_el is not None else "Google News"

            articles.append({
                "title":        title,
                "url":          link,
                "source":       source,
                "published_at": _parse_rfc2822(pub_raw),
                "body":         truncate(desc, ARTICLE_MAX_CHARS),
            })
    except ET.ParseError as exc:
        print(f"[GNews] XML parse error: {exc}")

    cache_set(cache_key, articles)
    return articles


def fetch_gnews_structured(query: str) -> List[dict]:
    """Public helper for pipeline use (returns raw dicts)."""
    return _fetch_gnews(query)
