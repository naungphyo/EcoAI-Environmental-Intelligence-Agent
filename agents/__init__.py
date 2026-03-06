# Pure-Python modules (no external deps) – import eagerly
from .trend_detector import detect_trends,   format_trend_report,   TrendReport
from .insight_extractor import extract_insights, format_insight_report, InsightReport

# LangGraph/LangChain-dependent modules – import lazily to allow unit tests
# of pure-Python modules even when the ML libraries aren't installed.


def run_pipeline(question: str):
    from .pipeline import run_pipeline as _run
    return _run(question)


def get_llm(**kwargs):
    from .llm_client import get_llm as _get
    return _get(**kwargs)
