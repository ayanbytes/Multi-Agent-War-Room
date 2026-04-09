import json
import logging
from datetime import datetime

from langchain_mistralai import ChatMistralAI

from app.config import MISTRAL_API_KEY, MISTRAL_MODEL, LLM_TEMPERATURE, OUTPUT_DIR, RELEASE_VERSION, RELEASE_DATE
from app.db.init_db import create_tables
from app.db.seed_data import seed_database
from app.db.queries import get_all_metric_names, get_feedback_summary_counts, get_release_notes
from app.agents.coordinator import run_coordinator
from app.models.output_models import FinalDecision

logger = logging.getLogger(__name__)


def build_dashboard_context() -> str:
    """Build a text summary of the current dashboard state for agents."""
    metric_names = get_all_metric_names()
    feedback_counts = get_feedback_summary_counts()
    release_notes = get_release_notes("latest")

    release_info = release_notes[0] if release_notes else {}

    context = f"""## Release Dashboard Context

**Release Version:** {RELEASE_VERSION}
**Release Date:** {RELEASE_DATE}
**Status:** {release_info.get('status', 'unknown')}

### Release Summary
{release_info.get('title', 'N/A')}

### Features Shipped
{release_info.get('features', 'N/A')}

### Known Issues
{release_info.get('known_issues', 'N/A')}

### Available Metrics (14-day window: 7 pre-release, 7 post-release)
{', '.join(metric_names)}

### User Feedback Overview
- Total feedback entries: {feedback_counts['total']}
- Positive: {feedback_counts['by_sentiment'].get('positive', 0)}
- Negative: {feedback_counts['by_sentiment'].get('negative', 0)}
- Neutral: {feedback_counts['by_sentiment'].get('neutral', 0)}
- Top categories: {', '.join(f"{k} ({v})" for k, v in sorted(feedback_counts['by_category'].items(), key=lambda x: -x[1])[:5])}

### Your Task
Analyze this release using the tools available to you. Gather data, identify trends, and provide your expert assessment of whether we should Proceed, Pause, or Roll Back this release.
"""
    return context


def create_llm() -> ChatMistralAI:
    """Initialize the Mistral LLM instance."""
    return ChatMistralAI(
        model=MISTRAL_MODEL,
        mistral_api_key=MISTRAL_API_KEY,
        temperature=LLM_TEMPERATURE,
    )


def save_output(decision: FinalDecision) -> str:
    """Save the final decision as a JSON file."""
    output_path = OUTPUT_DIR / "final_decision.json"
    output_data = decision.model_dump()

    # Add metadata
    output_data["_metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "release_version": RELEASE_VERSION,
        "model": MISTRAL_MODEL,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"[WORKFLOW] Final decision saved to: {output_path}")
    return str(output_path)


def run_workflow() -> None:
    """Execute the full multi-agent decision workflow end to end."""
    logger.info("=" * 70)
    logger.info("[WORKFLOW] Multi-Agent Release Decision System")
    logger.info("=" * 70)

    # Step 1: Initialize database
    logger.info("[WORKFLOW] Step 1: Initializing database...")
    create_tables()
    seed_database()

    # Step 2: Build dashboard context
    logger.info("[WORKFLOW] Step 2: Loading dashboard context...")
    context = build_dashboard_context()
    logger.info("[WORKFLOW] Dashboard context loaded successfully.")

    # Step 3: Create LLM instance
    logger.info(f"[WORKFLOW] Step 3: Initializing LLM ({MISTRAL_MODEL})...")
    llm = create_llm()

    # Step 4: Run multi-agent coordination
    logger.info("[WORKFLOW] Step 4: Starting multi-agent orchestration...")
    decision, state = run_coordinator(llm, context)

    # Step 5: Save output
    logger.info("[WORKFLOW] Step 5: Saving final decision...")
    output_path = save_output(decision)

    # Step 6: Print summary
    logger.info("=" * 70)
    logger.info("[WORKFLOW] WORKFLOW COMPLETE")
    logger.info("=" * 70)
    logger.info(f"  Decision:   {decision.decision}")
    logger.info(f"  Confidence: {decision.confidence_score}")
    logger.info(f"  Risks:      {len(decision.risk_register)} identified")
    logger.info(f"  Actions:    {len(decision.action_plan_24_48h)} planned")
    logger.info(f"  Output:     {output_path}")
    logger.info("=" * 70)

    # Also print the full decision to console
    print("\n" + "=" * 70)
    print("FINAL DECISION OUTPUT")
    print("=" * 70)
    print(json.dumps(decision.model_dump(), indent=2))
    print("=" * 70)
