"""
agents/query_expander.py
─────────────────────────
Intelligent query expansion for balanced, relevant article retrieval.

Key features:
1. Extracts environmental topics from user query
2. Expands query with related terms
3. Generates multiple search strategies
4. Balances positive/negative/neutral content
"""

import re
from typing import List, Dict, Set


# Environmental topic taxonomy
TOPIC_KEYWORDS = {
    "climate": ["climate change", "global warming", "climate crisis", "climate action"],
    "energy": ["renewable energy", "solar power", "wind energy", "clean energy", "fossil fuels"],
    "emissions": ["carbon emissions", "greenhouse gas", "CO2", "methane", "net zero"],
    "biodiversity": ["biodiversity", "species extinction", "wildlife", "habitat loss"],
    "ocean": ["ocean pollution", "marine life", "coral reefs", "overfishing", "sea level"],
    "forest": ["deforestation", "reforestation", "forest fires", "Amazon rainforest"],
    "pollution": ["air pollution", "water pollution", "plastic pollution", "toxic waste"],
    "policy": ["climate policy", "environmental regulation", "Paris Agreement", "COP"],
    "technology": ["green technology", "carbon capture", "electric vehicles", "sustainability"],
    "impact": ["environmental impact", "ecological damage", "climate impact"],
}

# Sentiment balancing terms
POSITIVE_MODIFIERS = [
    "progress", "solution", "innovation", "success", "achievement",
    "improvement", "breakthrough", "recovery", "restoration"
]

NEGATIVE_MODIFIERS = [
    "crisis", "threat", "damage", "loss", "decline",
    "warning", "risk", "failure", "destruction"
]

NEUTRAL_MODIFIERS = [
    "report", "study", "analysis", "data", "research",
    "update", "news", "development", "announcement"
]


def expand_query(user_query: str) -> Dict[str, List[str]]:
    """
    Expands user query into multiple balanced search queries.

    Returns:
        {
            "primary": [main queries],
            "positive": [positively-framed queries],
            "negative": [negatively-framed queries],
            "neutral": [neutral factual queries],
            "topics": [detected topics]
        }
    """
    query_lower = user_query.lower()

    # Detect topics
    detected_topics = _detect_topics(query_lower)

    # Build primary queries
    primary_queries = [user_query]  # Always include original

    # Add topic-specific queries
    for topic in detected_topics[:2]:  # Top 2 topics
        if topic in TOPIC_KEYWORDS:
            primary_queries.extend(TOPIC_KEYWORDS[topic][:2])

    # Build sentiment-balanced queries
    positive_queries = _build_balanced_queries(
        detected_topics, POSITIVE_MODIFIERS, query_lower)
    negative_queries = _build_balanced_queries(
        detected_topics, NEGATIVE_MODIFIERS, query_lower)
    neutral_queries = _build_balanced_queries(
        detected_topics, NEUTRAL_MODIFIERS, query_lower)

    return {
        "primary": list(set(primary_queries))[:3],  # Dedupe, max 3
        "positive": positive_queries[:2],
        "negative": negative_queries[:2],
        "neutral": neutral_queries[:2],
        "topics": detected_topics,
    }


def _detect_topics(query: str) -> List[str]:
    """Detects environmental topics mentioned in query."""
    detected = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query:
                detected.append(topic)
                break
    return detected if detected else ["climate", "environment"]  # defaults


def _build_balanced_queries(topics: List[str], modifiers: List[str], original_query: str) -> List[str]:
    """Builds queries with sentiment modifiers."""
    queries = []

    # If original query already contains a modifier, skip
    has_modifier = any(mod in original_query for mod in POSITIVE_MODIFIERS +
                       NEGATIVE_MODIFIERS + NEUTRAL_MODIFIERS)
    if has_modifier:
        return []

    for topic in topics[:2]:  # Top 2 topics
        if topic in TOPIC_KEYWORDS:
            main_term = TOPIC_KEYWORDS[topic][0]
            for modifier in modifiers[:2]:  # Top 2 modifiers
                queries.append(f"{main_term} {modifier}")

    return queries


def deduplicate_across_sentiment(all_articles: List[dict]) -> List[dict]:
    """
    Ensures balanced representation of positive/negative/neutral articles.
    Removes near-duplicates while preserving sentiment diversity.
    """
    from utils.text import sentiment_score

    # Group by title similarity
    seen_titles: Set[str] = set()
    sentiment_buckets = {"Positive": [], "Negative": [], "Neutral": []}

    for art in all_articles:
        # Normalize title for dedup
        title_key = re.sub(r'\W+', '', art.get("title", "").lower())[:50]

        if title_key in seen_titles:
            continue

        seen_titles.add(title_key)

        # Get sentiment
        combined = f"{art.get('title', '')} {art.get('body', '')}"
        sent = sentiment_score(combined)
        art["sentiment"] = sent

        sentiment_buckets[sent["label"]].append(art)

    # Balance: take equal amounts from each bucket
    balanced = []
    max_per_bucket = 5  # Max 5 from each sentiment

    for bucket in sentiment_buckets.values():
        # Sort by recency within each bucket
        bucket.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        balanced.extend(bucket[:max_per_bucket])

    # Sort final list by recency
    balanced.sort(key=lambda x: x.get("published_at", ""), reverse=True)

    return balanced


def explain_query_strategy(expanded: Dict[str, List[str]]) -> str:
    """Generates human-readable explanation of query strategy."""
    lines = [
        f"🎯 **Query Strategy:**",
        f"- Detected topics: {', '.join(expanded['topics'][:3])}",
        f"- Primary searches: {len(expanded['primary'])} queries",
        f"- Balanced retrieval: {len(expanded['positive'])} positive + {len(expanded['negative'])} negative + {len(expanded['neutral'])} neutral",
    ]
    return "\n".join(lines)
