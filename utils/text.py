"""
utils/text.py - Enhanced text processing with better sentiment
"""

import re
from typing import List


def clean_html(raw: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    no_tags = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", no_tags).strip()


def truncate(text: str, max_chars: int) -> str:
    """Hard-truncate to max_chars, appending '…' if cut."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_space = cut.rfind(" ")
    if last_space > max_chars // 2:
        cut = cut[:last_space]
    return cut + " …"


def deduplicate_articles(articles: List[dict]) -> List[dict]:
    """Remove near-duplicate articles by title similarity."""
    seen: set = set()
    unique: List[dict] = []
    for art in articles:
        key = re.sub(r"\W+", "", art.get("title", "").lower())[:60]
        if key and key not in seen:
            seen.add(key)
            unique.append(art)
    return unique


def extract_keywords(text: str, top_n: int = 8) -> List[str]:
    """Lightweight keyword extraction without ML dependencies."""
    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "are", "was", "were", "has", "have",
        "had", "it", "its", "this", "that", "be", "as", "we", "our", "they",
        "their", "he", "she", "i", "you", "not", "will", "can", "do", "does",
        "about", "also", "into", "more", "new", "over", "up", "said", "says",
        "than", "then", "when", "which", "who", "would", "could", "should",
        "been", "being", "after", "before", "report", "according", "year",
        "world", "global", "major", "show", "shows", "find", "found", "how",
        "what", "where", "why", "just", "now", "get", "make", "year", "years",
    }
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    freq: dict = {}
    for w in words:
        if w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:top_n]]


def sentiment_score(text: str) -> dict:
    """
    ENHANCED rule-based sentiment with more nuanced scoring.
    Returns {"label": "Positive|Neutral|Negative", "score": float 0-1}.
    """
    # Expanded lexicons with more environmental terms
    POSITIVE = {
        "improve", "solution", "progress", "achieve", "success", "hope", "restore",
        "protect", "clean", "green", "renewable", "sustainable", "recovery", "advance",
        "benefit", "growth", "innovation", "reduce", "agreement", "milestone",
        "breakthrough", "conservation", "positive", "victory", "win", "boost",
        "increase", "rise", "expand", "adopt", "implement", "launch", "approve",
        "pledge", "commit", "invest", "fund", "initiative", "action", "cooperation",
        "collaboration", "treaty", "accord", "reduction", "decline", "fall",
        # Context: "emissions decline" is positive, "temperatures decline" is negative
        # We'll handle this with context patterns below
    }

    NEGATIVE = {
        "crisis", "disaster", "loss", "destroy", "damage", "threat", "risk", "decline",
        "pollution", "toxic", "extinction", "collapse", "death", "warning", "danger",
        "severe", "extreme", "catastrophe", "flooding", "drought", "wildfire",
        "contamination", "deforestation", "harmful", "urgent", "alarming", "worse",
        "worsen", "critical", "emergency", "failure", "reject", "oppose", "delay",
        "deny", "controversial", "conflict", "dispute", "deadlock", "stall", "crisis",
        "vulnerable", "endangered", "threaten", "accelerate", "surge", "spike",
        "record-high", "unprecedented", "irreversible", "devastating",
    }

    # Context-aware patterns (overrides word-level scoring)
    POSITIVE_PATTERNS = [
        r"emissions?\s+(fall|decline|drop|decrease|reduce)",
        r"(renewable|clean)\s+energy\s+(rise|increase|grow|expand|record)",
        r"temperature\s+rise\s+(slow|stabilize|limit)",
        r"(protect|save|restore|conserve)\s+",
        r"carbon\s+(capture|neutral|negative|offset)",
        r"(ban|phase.out)\s+(fossil|plastic|coal)",
    ]

    NEGATIVE_PATTERNS = [
        r"(temperature|warming|heat)\s+(rise|increase|accelerate|surge)",
        r"(ice|glacier)\s+(melt|shrink|disappear|loss)",
        r"(species|wildlife)\s+(extinct|endangered|decline|loss)",
        r"(emission|pollution)\s+(rise|increase|surge|worsen)",
        r"(forest|tree)\s+(loss|destroy|clear|cut)",
        r"(drought|flood|fire|storm)\s+(intensif|worsen|severe|record)",
    ]

    text_lower = text.lower()

    # Check context patterns first (higher priority)
    pos_pattern_matches = sum(
        1 for p in POSITIVE_PATTERNS if re.search(p, text_lower))
    neg_pattern_matches = sum(
        1 for p in NEGATIVE_PATTERNS if re.search(p, text_lower))

    # Word-level scoring
    words = re.findall(r"\b[a-z]+\b", text_lower)
    pos_words = sum(1 for w in words if w in POSITIVE)
    neg_words = sum(1 for w in words if w in NEGATIVE)

    # Combine pattern-based and word-based scores
    pos_total = pos_words + (pos_pattern_matches * 3)  # Patterns weighted 3x
    neg_total = neg_words + (neg_pattern_matches * 3)
    total = pos_total + neg_total or 1

    score = pos_total / total

    # More nuanced thresholds
    if score > 0.60:
        label = "Positive"
    elif score < 0.35:
        label = "Negative"
    else:
        label = "Neutral"

    return {"label": label, "score": round(score, 2)}
