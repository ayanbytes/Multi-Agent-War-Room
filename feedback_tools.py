import json
import logging
from collections import Counter

from langchain_core.tools import tool

from app.db.queries import get_all_feedback, get_feedback_by_sentiment, get_feedback_summary_counts

logger = logging.getLogger(__name__)


@tool
def feedback_summary(sentiment_filter: str) -> str:
    """Summarize user feedback sentiment distribution and top recurring themes.
    Filter by 'all', 'positive', 'negative', or 'neutral'."""
    logger.info(f"[TOOL] feedback_summary called with sentiment_filter='{sentiment_filter}'")

    if sentiment_filter.lower() == "all":
        feedback = get_all_feedback()
    else:
        feedback = get_feedback_by_sentiment(sentiment_filter.lower())

    if not feedback:
        return f"No feedback found for filter '{sentiment_filter}'."

    # Count sentiments and categories
    sentiment_counts = Counter(fb["sentiment"] for fb in feedback)
    category_counts = Counter(fb["category"] for fb in feedback)

    # Extract top themes from category counts
    top_categories = category_counts.most_common(5)

    # Collect sample quotes per sentiment
    samples = {}
    for sentiment in ["positive", "negative", "neutral"]:
        matching = [fb["feedback_text"] for fb in feedback if fb["sentiment"] == sentiment]
        samples[sentiment] = matching[:3]  # Up to 3 samples each

    result = {
        "total_feedback_count": len(feedback),
        "sentiment_distribution": dict(sentiment_counts),
        "top_categories": [{"category": cat, "count": count} for cat, count in top_categories],
        "sample_quotes": samples,
        "source_distribution": dict(Counter(fb["source"] for fb in feedback)),
    }

    return json.dumps(result, indent=2)
