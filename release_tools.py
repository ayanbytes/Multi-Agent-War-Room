import json
import logging

from langchain_core.tools import tool

from app.db.queries import get_release_notes, get_metrics_dataframe, get_feedback_summary_counts
from app.config import RELEASE_DATE

logger = logging.getLogger(__name__)


@tool
def release_notes_lookup(version: str) -> str:
    """Look up release notes including features, known issues, and status.
    Pass a version like 'v2.4.0' or 'latest' for the most recent release."""
    logger.info(f"[TOOL] release_notes_lookup called with version='{version}'")

    notes = get_release_notes(version)
    if not notes:
        return f"No release notes found for version '{version}'."

    return json.dumps(notes, indent=2)


@tool
def calculate_risk_score(scope: str) -> str:
    """Calculate a rule-based risk score from metrics and feedback data.
    Scope: 'full' (metrics + feedback) or 'metrics_only'."""
    logger.info(f"[TOOL] calculate_risk_score called with scope='{scope}'")

    from datetime import date
    import pandas as pd

    release_date = date.fromisoformat(RELEASE_DATE)
    df = get_metrics_dataframe()

    if df.empty:
        return json.dumps({"error": "No metrics data available."})

    df["period"] = df["date"].apply(
        lambda d: "post" if d.date() >= release_date else "pre"
    )

    risk_items = []
    total_score = 0

    # Evaluate each metric against risk thresholds
    risk_rules = [
        {
            "metric": "crash_rate",
            "threshold_pct": 100,
            "severity": "High",
            "weight": 25,
            "description": "Crash rate increase",
        },
        {
            "metric": "payment_success_rate",
            "threshold_pct": -1.0,
            "severity": "High",
            "weight": 25,
            "description": "Payment success rate drop",
            "use_absolute_delta": True,
        },
        {
            "metric": "api_latency_p95_ms",
            "threshold_pct": 50,
            "severity": "Medium",
            "weight": 15,
            "description": "API latency increase",
        },
        {
            "metric": "support_ticket_volume",
            "threshold_pct": 50,
            "severity": "Medium",
            "weight": 15,
            "description": "Support ticket volume increase",
        },
        {
            "metric": "churn_rate",
            "threshold_pct": 20,
            "severity": "Medium",
            "weight": 10,
            "description": "Churn rate increase",
        },
        {
            "metric": "retention_d1",
            "threshold_pct": -5,
            "severity": "Low",
            "weight": 10,
            "description": "D1 retention drop",
            "use_absolute_delta": True,
        },
    ]

    for rule in risk_rules:
        metric_df = df[df["metric_name"] == rule["metric"]]
        if metric_df.empty:
            continue

        pre_avg = metric_df[metric_df["period"] == "pre"]["value"].mean()
        post_avg = metric_df[metric_df["period"] == "post"]["value"].mean()
        delta = post_avg - pre_avg
        pct_change = (delta / pre_avg * 100) if pre_avg != 0 else 0

        triggered = False
        if rule.get("use_absolute_delta"):
            triggered = delta <= rule["threshold_pct"]
        else:
            triggered = pct_change >= rule["threshold_pct"]

        if triggered:
            total_score += rule["weight"]
            risk_items.append({
                "risk": rule["description"],
                "severity": rule["severity"],
                "metric": rule["metric"],
                "pre_avg": round(pre_avg, 4),
                "post_avg": round(post_avg, 4),
                "change": f"{round(pct_change, 1)}%",
                "weight": rule["weight"],
            })

    # Include feedback signals if scope is 'full'
    if scope.lower() == "full":
        counts = get_feedback_summary_counts()
        negative_ratio = counts["by_sentiment"].get("negative", 0) / max(counts["total"], 1)
        if negative_ratio > 0.35:
            total_score += 10
            risk_items.append({
                "risk": "High negative feedback ratio",
                "severity": "Medium",
                "detail": f"{round(negative_ratio * 100, 1)}% negative feedback",
                "weight": 10,
            })

    # Classify overall risk level
    if total_score >= 60:
        risk_level = "Critical"
    elif total_score >= 40:
        risk_level = "High"
    elif total_score >= 20:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    result = {
        "overall_risk_score": total_score,
        "max_possible_score": 110,
        "risk_level": risk_level,
        "triggered_risks": risk_items,
        "recommendation": _risk_recommendation(risk_level),
    }

    return json.dumps(result, indent=2)


def _risk_recommendation(risk_level: str) -> str:
    """Return a recommendation based on the overall risk level."""
    recommendations = {
        "Critical": "Immediate rollback recommended. Multiple critical metrics degraded.",
        "High": "Pause rollout and investigate. Significant risks require mitigation before proceeding.",
        "Medium": "Proceed with caution. Monitor flagged metrics closely and prepare rollback plan.",
        "Low": "Proceed with standard monitoring. No significant risks detected.",
    }
    return recommendations.get(risk_level, "Unable to determine recommendation.")
