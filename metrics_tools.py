import json
import logging
from datetime import date

import pandas as pd
from langchain_core.tools import tool

from app.db.queries import get_metrics_dataframe, get_all_metric_names, get_metrics_by_name
from app.config import RELEASE_DATE

logger = logging.getLogger(__name__)

RELEASE_DATE_PARSED = date.fromisoformat(RELEASE_DATE)


@tool
def aggregate_metrics(metric_name: str) -> str:
    """Compare pre-release vs post-release metric averages, deltas, and percent changes.
    Use 'all' to compare every metric, or pass a specific name like 'crash_rate' or 'dau'."""
    logger.info(f"[TOOL] aggregate_metrics called with metric_name='{metric_name}'")

    df = get_metrics_dataframe()
    if df.empty:
        return "No metrics data available."

    df["period"] = df["date"].apply(
        lambda d: "post_release" if d.date() >= RELEASE_DATE_PARSED else "pre_release"
    )

    if metric_name.lower() != "all":
        df = df[df["metric_name"] == metric_name]
        if df.empty:
            available = get_all_metric_names()
            return f"Metric '{metric_name}' not found. Available: {available}"

    results = []
    for name, group in df.groupby("metric_name"):
        pre = group[group["period"] == "pre_release"]["value"]
        post = group[group["period"] == "post_release"]["value"]

        pre_avg = round(pre.mean(), 4) if len(pre) > 0 else 0
        post_avg = round(post.mean(), 4) if len(post) > 0 else 0
        delta = round(post_avg - pre_avg, 4)
        pct_change = round((delta / pre_avg) * 100, 2) if pre_avg != 0 else 0

        unit = group["unit"].iloc[0] if len(group) > 0 else ""

        results.append({
            "metric": name,
            "pre_release_avg": pre_avg,
            "post_release_avg": post_avg,
            "delta": delta,
            "percent_change": pct_change,
            "unit": unit,
            "direction": "improved" if _is_improvement(name, delta) else "degraded",
        })

    return json.dumps(results, indent=2)


@tool
def detect_anomalies(metric_name: str) -> str:
    """Detect anomalies (spikes or drops) in daily metrics using z-score analysis.
    Use 'all' for all metrics or specify a metric name like 'crash_rate'."""
    logger.info(f"[TOOL] detect_anomalies called with metric_name='{metric_name}'")

    df = get_metrics_dataframe()
    if df.empty:
        return "No metrics data available."

    if metric_name.lower() != "all":
        df = df[df["metric_name"] == metric_name]
        if df.empty:
            return f"Metric '{metric_name}' not found."

    anomalies = []
    z_threshold = 1.8  # Flag values beyond 1.8 standard deviations

    for name, group in df.groupby("metric_name"):
        values = group["value"]
        mean = values.mean()
        std = values.std()

        if std == 0:
            continue

        for _, row in group.iterrows():
            z_score = (row["value"] - mean) / std
            if abs(z_score) > z_threshold:
                anomalies.append({
                    "metric": name,
                    "date": row["date"].strftime("%Y-%m-%d"),
                    "value": round(row["value"], 4),
                    "mean": round(mean, 4),
                    "z_score": round(z_score, 2),
                    "type": "spike" if z_score > 0 else "drop",
                    "unit": row["unit"],
                })

    if not anomalies:
        return "No anomalies detected within the z-score threshold."

    return json.dumps(anomalies, indent=2)


def _is_improvement(metric_name: str, delta: float) -> bool:
    """Determine if a delta represents an improvement based on metric semantics.
    For metrics where higher is worse (crash_rate, latency, etc.), a positive delta is bad."""
    higher_is_worse = {
        "crash_rate", "api_latency_p95_ms", "support_ticket_volume", "churn_rate"
    }
    if metric_name in higher_is_worse:
        return delta < 0
    return delta > 0
