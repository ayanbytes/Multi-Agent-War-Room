import logging
from datetime import date

import pandas as pd
from sqlalchemy import text

from app.db.init_db import get_session, engine
from app.db.models import DailyMetric, UserFeedback, ReleaseNote

logger = logging.getLogger(__name__)


def get_metrics_dataframe() -> pd.DataFrame:
    """Load all daily metrics into a Pandas DataFrame."""
    query = "SELECT date, metric_name, value, unit FROM daily_metrics ORDER BY date"
    df = pd.read_sql(query, engine, parse_dates=["date"])
    return df


def get_metrics_by_name(metric_name: str) -> list[dict]:
    """Get daily values for a specific metric."""
    with get_session() as session:
        rows = (
            session.query(DailyMetric)
            .filter(DailyMetric.metric_name == metric_name)
            .order_by(DailyMetric.date)
            .all()
        )
        return [r.to_dict() for r in rows]


def get_all_metric_names() -> list[str]:
    """Return distinct metric names in the database."""
    with get_session() as session:
        rows = session.query(DailyMetric.metric_name).distinct().all()
        return [r[0] for r in rows]


def get_all_feedback() -> list[dict]:
    """Load all user feedback entries."""
    with get_session() as session:
        rows = session.query(UserFeedback).order_by(UserFeedback.submitted_date).all()
        return [r.to_dict() for r in rows]


def get_feedback_by_sentiment(sentiment: str) -> list[dict]:
    """Load feedback filtered by sentiment (positive, negative, neutral)."""
    with get_session() as session:
        rows = (
            session.query(UserFeedback)
            .filter(UserFeedback.sentiment == sentiment)
            .order_by(UserFeedback.submitted_date)
            .all()
        )
        return [r.to_dict() for r in rows]


def get_release_notes(version: str | None = None) -> list[dict]:
    """Load release notes, optionally filtered by version."""
    with get_session() as session:
        query = session.query(ReleaseNote)
        if version and version.lower() != "latest":
            query = query.filter(ReleaseNote.version == version)
        rows = query.order_by(ReleaseNote.release_date.desc()).all()
        return [r.to_dict() for r in rows]


def get_feedback_summary_counts() -> dict:
    """Return counts of feedback by sentiment and category."""
    with get_session() as session:
        all_feedback = session.query(UserFeedback).all()

        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        category_counts = {}

        for fb in all_feedback:
            sentiment_counts[fb.sentiment] = sentiment_counts.get(fb.sentiment, 0) + 1
            category_counts[fb.category] = category_counts.get(fb.category, 0) + 1

        return {
            "total": len(all_feedback),
            "by_sentiment": sentiment_counts,
            "by_category": category_counts,
        }
