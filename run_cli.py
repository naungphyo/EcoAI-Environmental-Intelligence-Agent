"""
run_cli.py
───────────
Quick CLI test runner.  Useful for debugging without opening the browser.

Usage:
  python run_cli.py "What are the latest climate change news?"
  python run_cli.py  (prompts interactively)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agents.pipeline import run_pipeline
from agents.trend_detector import format_trend_report
from agents.insight_extractor import format_insight_report


def main():
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = input("🌿 EcoAI > Enter your environmental question: ").strip()

    if not question:
        print("No question provided. Exiting.")
        return

    print(f"\n🔍 Querying: {question}\n{'─'*60}")

    result = run_pipeline(question)

    print(f"\n⏱  Completed in {result['elapsed_ms']:.0f} ms")
    print(f"📰 Articles retrieved: {len(result['articles'])}")
    print(f"\n{'─'*60}")
    print("🤖 AI ANSWER")
    print(f"{'─'*60}")
    print(result.get("final_answer", "No answer generated"))

    if result.get("trend_report"):
        print(f"\n{'─'*60}")
        print(format_trend_report(result["trend_report"]))

    if result.get("insight_report"):
        print(f"\n{'─'*60}")
        print(format_insight_report(result["insight_report"]))

    print(f"\n{'─'*60}")
    print("📰 SOURCES")
    print(f"{'─'*60}")
    for s in result.get("sources", [])[:6]:
        print(f"• [{s['sentiment']:8s}] {s['source']:20s} {s['published']}  {s['title'][:60]}")


if __name__ == "__main__":
    main()