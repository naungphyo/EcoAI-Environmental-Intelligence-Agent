"""
EcoAI Configuration Settings
All constants, API keys (from env), and tunable parameters live here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# LLM API Keys - multiple options for free inference

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Google Gemini (free)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")   # Groq (fast & free)

# ── Cache Settings ────────────────────────────────────────────────────────────
# TTL = Time To Live
# When you ask a question, the system saves the results for 20 minutes.
# If you ask the SAME question again within 20 minutes, it shows the saved
# results instantly (no new API calls). After 20 minutes, it fetches fresh data.
# This keeps responses FAST while data stays FRESH.
CACHE_TTL_SECONDS = 20 * 60          # 20 minutes (1200 seconds)
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")

# ── Retrieval Settings ────────────────────────────────────────────────────────
MAX_ARTICLES_PER_SOURCE = 6          # Fetch 6 from each source (more data)
# Keep top 15 after filtering (more context)
MAX_TOTAL_ARTICLES = 15
ARTICLE_MAX_CHARS = 1500            # Longer snippets = better summaries
REQUEST_TIMEOUT = 10                 # 10 seconds per request

# ── LLM / Model Settings ──────────────────────────────────────────────────────
# Which LLM backend to use
LLM_BACKEND = os.getenv("LLM_BACKEND", "huggingface")


# Google Gemini settings (free tier: 60 requests/min)
GEMINI_MODEL = "gemini-1.5-flash"

# Groq settings (extremely fast, free tier: 30 req/min)
GROQ_MODEL = "llama-3.1-70b-versatile"

# ── News Sources ──────────────────────────────────────────────────────────────
ENV_KEYWORDS = [
    "climate change", "global warming", "environment",
    "renewable energy", "carbon emissions", "sustainability",
    "biodiversity", "deforestation", "ocean pollution", "air quality",
]

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
