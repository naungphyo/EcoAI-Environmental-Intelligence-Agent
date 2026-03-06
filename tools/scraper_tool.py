"""
tools/scraper_tool.py
──────────────────────
BeautifulSoup scraper (no LangChain tool decorator)
"""

import requests
from bs4 import BeautifulSoup

from config.settings import REQUEST_TIMEOUT, ARTICLE_MAX_CHARS
from utils.cache import cache_get, cache_set
from utils.text import clean_html, truncate


def scrape_article(url: str) -> str:
    if not url or not url.startswith("http"):
        return ""

    cache_key = f"scrape::{url}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (compatible; EcoAI/1.0)"},
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"[Scraper] Failed to fetch {url}: {exc}")
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "ads", "iframe"]):
        tag.decompose()

    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id="content")
        or soup.find(class_="content")
        or soup.body
    )

    text = clean_html(main.get_text(separator=" ") if main else "")
    result = truncate(text, ARTICLE_MAX_CHARS * 2)

    cache_set(cache_key, result)
    return result
