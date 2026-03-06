"""
agents/insight_extractor.py - ENHANCED with smarter extraction
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict

from utils.text import sentiment_score


# Enhanced patterns for statistics extraction
_STAT_PATTERNS = [
    # Numbers with units
    r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(percent|%|million|billion|trillion|thousand|tonnes?|tons?|kg|megawatts?|MW|GW|gigawatts?|degrees?|°C|°F)',
    # Monetary amounts
    r'\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(million|billion|trillion)?',
    # Percentages in context
    r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s+(?:increase|decrease|reduction|rise|fall|growth|decline)',
    # Year-based targets
    r'by\s+(\d{4})',
    # Specific quantities
    r'(\d+(?:,\d+)*)\s+(?:people|countries|nations|species|trees|hectares|acres|kilometers|miles)',
]

_ACTION_PATTERNS = [
    r'\b(?:must|need(?:s)? to|should|urged?|called? (?:on|for)|require[sd]?|demand[ed]*)\b',
    r'\b(?:recommend[s]?|policy|policies|action|initiative|commitment|pledge[sd]?)\b',
    r'\b(?:reduce[sd]?|cut|lower|limit|phase[- ]out|eliminate[sd]?|ban(?:ned)?)\b.*\b(?:emission|carbon|plastic|pollution|waste)\b',
    r'\b(?:target|goal|deadline|by \d{4}|net[- ]zero|paris agreement|cop\d+)\b',
    r'\b(?:invest(?:ment)?|fund(?:ing)?|allocat(?:e|ed|ion)|spend(?:ing)?)\b.*\b(?:billion|million)\b',
]

_COMPILED_STATS = [re.compile(p, re.IGNORECASE) for p in _STAT_PATTERNS]
_COMPILED_ACTIONS = [re.compile(p, re.IGNORECASE) for p in _ACTION_PATTERNS]


@dataclass
class InsightReport:
    actionable_sentences: List[str]
    source_comparison: List[Dict]
    cross_source_agreement: str
    quantified_facts: List[str]


def extract_insights(articles: List[dict]) -> InsightReport:
    """Enhanced insight extraction with smarter pattern matching."""
    if not articles:
        return InsightReport(
            actionable_sentences=[],
            source_comparison=[],
            cross_source_agreement="N/A",
            quantified_facts=[],
        )

    all_actionable: List[str] = []
    quantified: List[str] = []
    source_rows: List[Dict] = []

    for art in articles:
        combined = f"{art.get('title', '')}. {art.get('body', '')}"
        sentences = _split_sentences(combined)

        # Extract actionable items
        art_actionable = [s for s in sentences if _is_actionable(s)]
        all_actionable.extend(art_actionable)

        # Extract quantified facts (ENHANCED)
        quant_sentences = []
        for sentence in sentences:
            if _has_quantified_data(sentence):
                quant_sentences.append(sentence)
        quantified.extend(quant_sentences)

        # Per-source sentiment
        sentiment = sentiment_score(combined)
        source_rows.append({
            "source":    art.get("source", "Unknown"),
            "title":     art.get("title", "")[:80],
            "sentiment": sentiment["label"],
            "score":     sentiment["score"],
            "published": art.get("published_at", "")[:10],
            "url":       art.get("url", ""),
            "angle":     _infer_angle(combined),
        })

    # Dedup actionable sentences
    seen: set = set()
    unique_actionable: List[str] = []
    for s in all_actionable:
        key = s[:50].lower()
        if key not in seen:
            seen.add(key)
            unique_actionable.append(s)

    # Dedup quantified facts
    seen_quant: set = set()
    unique_quant: List[str] = []
    for s in quantified:
        key = s[:60].lower()
        if key not in seen_quant:
            seen_quant.add(key)
            unique_quant.append(s)

    # Cross-source agreement
    if source_rows:
        sentiments = [r["sentiment"] for r in source_rows]
        dominant = max(set(sentiments), key=sentiments.count)
        agreement_ratio = sentiments.count(dominant) / len(sentiments)
        agreement = (
            "High" if agreement_ratio > 0.7 else
            "Medium" if agreement_ratio > 0.5 else
            "Low"
        )
    else:
        agreement = "N/A"

    return InsightReport(
        actionable_sentences=unique_actionable[:10],
        source_comparison=source_rows,
        cross_source_agreement=agreement,
        quantified_facts=unique_quant[:8],
    )


def _has_quantified_data(sentence: str) -> bool:
    """Check if sentence contains numbers/statistics."""
    return any(p.search(sentence) for p in _COMPILED_STATS)


def _is_actionable(sentence: str) -> bool:
    """Check if sentence contains actionable language."""
    return any(p.search(sentence) for p in _COMPILED_ACTIONS)


def _split_sentences(text: str) -> List[str]:
    """Naive sentence splitter."""
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [p.strip() for p in parts if len(p.strip()) > 40]


def _infer_angle(text: str) -> str:
    """Classify article's editorial angle."""
    t = text.lower()
    if any(w in t for w in ["policy", "government", "law", "regulation", "bill", "treaty"]):
        return "Policy & Governance"
    if any(w in t for w in ["research", "study", "scientist", "data", "report", "finding"]):
        return "Science & Research"
    if any(w in t for w in ["company", "industry", "market", "invest", "economy", "business"]):
        return "Business & Economy"
    if any(w in t for w in ["activist", "protest", "movement", "community", "people", "youth"]):
        return "Activism & Society"
    if any(w in t for w in ["technology", "innovation", "solar", "wind", "battery", "electric"]):
        return "Clean Technology"
    return "General Environment"


def format_insight_report(report: InsightReport) -> str:
    """Render InsightReport as markdown."""
    lines = ["## ⚡ Actionable Insights"]

    if report.actionable_sentences:
        for s in report.actionable_sentences[:5]:
            lines.append(f"- {s.strip()}")
    else:
        lines.append("_No specific action items detected in this batch._")

    # ONLY show stats section if we have data
    if report.quantified_facts:
        lines += ["", "## 📊 Key Statistics & Figures"]
        for fact in report.quantified_facts[:6]:
            lines.append(f"- {fact.strip()}")

    lines += [
        "",
        f"## 🗞️ Source Consensus: **{report.cross_source_agreement}**",
    ]
    return "\n".join(lines)
