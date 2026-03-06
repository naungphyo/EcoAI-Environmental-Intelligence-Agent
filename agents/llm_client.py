"""
agents/llm_client.py
─────────────────────
Multi-LLM client supporting 2 free inference APIs:
  1. Google Gemini Flash (fast, free)
  2. Groq (fastest inference, free tier)
"""

from config.settings import (
    GEMINI_API_KEY, GEMINI_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    LLM_BACKEND,
)


def get_llm(temperature: float = 0.2, max_new_tokens: int = 800):
    """
    Factory function – returns the appropriate LLM.
    Lower temperature (0.2) = more factual, accurate summaries.
    """
    backend = LLM_BACKEND.lower()

    if backend == "gemini":
        return _get_gemini(temperature, max_new_tokens)
    else:  # default: groq
        return _get_groq(temperature, max_new_tokens)


def _get_gemini(temperature: float, max_new_tokens: int):
    """Google Gemini Flash - Fast, accurate, free (60 req/min)"""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError(
            "Install: pip install langchain-google-genai"
        )

    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY not set. Get free key: https://aistudio.google.com/app/apikey"
        )

    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=temperature,
        max_output_tokens=max_new_tokens,
    )


def _get_groq(temperature: float, max_new_tokens: int):
    """Groq - Llama 3.1 70B (fastest inference, free)"""
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        raise ImportError(
            "Install: pip install langchain-groq"
        )

    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Get free key: https://console.groq.com/keys"
        )

    return ChatGroq(
        model=GROQ_MODEL,
        groq_api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_new_tokens,
    )
