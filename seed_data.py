import logging
import random
from datetime import date, timedelta

from app.db.init_db import get_session
from app.db.models import DailyMetric, UserFeedback, ReleaseNote

logger = logging.getLogger(__name__)

# Seed for reproducible mock data
random.seed(42)

RELEASE_DATE = date(2026, 3, 25)
START_DATE = date(2026, 3, 18)

# Metric definitions: pre-release baseline, post-release shift, noise range
METRICS_CONFIG = {
    "signup_conversion_rate": {"pre": 3.2, "post": 4.1, "noise": 0.3, "unit": "%"},
    "dau": {"pre": 12000, "post": 13800, "noise": 800, "unit": "users"},
    "retention_d1": {"pre": 42.0, "post": 39.5, "noise": 1.5, "unit": "%"},
    "crash_rate": {"pre": 0.8, "post": 2.3, "noise": 0.3, "unit": "%"},
    "api_latency_p95_ms": {"pre": 185, "post": 320, "noise": 30, "unit": "ms"},
    "payment_success_rate": {"pre": 98.5, "post": 96.7, "noise": 0.4, "unit": "%"},
    "support_ticket_volume": {"pre": 48, "post": 89, "noise": 10, "unit": "tickets"},
    "feature_adoption_rate": {"pre": 15.0, "post": 29.0, "noise": 2.0, "unit": "%"},
    "churn_rate": {"pre": 1.2, "post": 1.6, "noise": 0.2, "unit": "%"},
}

FEEDBACK_ENTRIES = [
    # Positive feedback
    {"text": "Love the new onboarding flow! Much smoother and more intuitive than before.", "sentiment": "positive", "category": "onboarding", "source": "in_app"},
    {"text": "The dashboard redesign is fantastic. I can finally see all my analytics at a glance.", "sentiment": "positive", "category": "features", "source": "in_app"},
    {"text": "New search functionality is blazing fast. Huge improvement over the old search.", "sentiment": "positive", "category": "features", "source": "support_ticket"},
    {"text": "Feature adoption tracker is exactly what our team needed. Great addition.", "sentiment": "positive", "category": "features", "source": "in_app"},
    {"text": "Signup process went from 5 steps to 3. Our conversion will definitely improve.", "sentiment": "positive", "category": "onboarding", "source": "email"},
    {"text": "The UI refresh looks modern and professional. Clients have already noticed.", "sentiment": "positive", "category": "ux", "source": "in_app"},
    {"text": "Payment flow optimization reduced our checkout time significantly.", "sentiment": "positive", "category": "payments", "source": "support_ticket"},
    {"text": "Really impressed with the new widget customization options on the dashboard.", "sentiment": "positive", "category": "features", "source": "in_app"},
    {"text": "Onboarding tutorial is much clearer now. New users should ramp up faster.", "sentiment": "positive", "category": "onboarding", "source": "email"},
    {"text": "The improved navigation makes the whole platform feel more cohesive.", "sentiment": "positive", "category": "ux", "source": "in_app"},
    # Negative feedback
    {"text": "App crashed twice during checkout. Lost a customer because of it.", "sentiment": "negative", "category": "crashes", "source": "support_ticket"},
    {"text": "Payment page freezes for 10+ seconds on mobile. This is unacceptable.", "sentiment": "negative", "category": "performance", "source": "support_ticket"},
    {"text": "Getting random errors when trying to export reports since the update.", "sentiment": "negative", "category": "crashes", "source": "in_app"},
    {"text": "The app is noticeably slower. Pages that loaded instantly now take 3-4 seconds.", "sentiment": "negative", "category": "performance", "source": "in_app"},
    {"text": "Crash on the analytics page when filtering by custom date range.", "sentiment": "negative", "category": "crashes", "source": "support_ticket"},
    {"text": "Our team cannot complete payments reliably anymore. Getting timeout errors.", "sentiment": "negative", "category": "payments", "source": "support_ticket"},
    {"text": "Support response time has gotten worse. Waited 48 hours for a reply.", "sentiment": "negative", "category": "support", "source": "email"},
    {"text": "The update broke our API integration. We had to roll back our own deployment.", "sentiment": "negative", "category": "crashes", "source": "support_ticket"},
    {"text": "Dashboard widgets do not load on Firefox. Only works on Chrome apparently.", "sentiment": "negative", "category": "crashes", "source": "in_app"},
    {"text": "Experiencing data loss in saved reports after the v2.4 update.", "sentiment": "negative", "category": "crashes", "source": "support_ticket"},
    {"text": "Latency spikes during peak hours make the platform unusable for our team.", "sentiment": "negative", "category": "performance", "source": "email"},
    {"text": "Payment confirmation emails are delayed by hours since the update.", "sentiment": "negative", "category": "payments", "source": "support_ticket"},
    # Neutral / mixed feedback
    {"text": "The new design looks different. Taking some time to find where things are.", "sentiment": "neutral", "category": "ux", "source": "in_app"},
    {"text": "Some features improved, but the performance trade-off concerns me.", "sentiment": "neutral", "category": "performance", "source": "in_app"},
    {"text": "Not sure about the new color scheme, but the layout is better.", "sentiment": "neutral", "category": "ux", "source": "email"},
    {"text": "Migrated to v2.4 without issues so far. Have not tested all features yet.", "sentiment": "neutral", "category": "general", "source": "in_app"},
    {"text": "The onboarding is better but advanced settings are harder to find now.", "sentiment": "neutral", "category": "onboarding", "source": "support_ticket"},
    {"text": "Mixed feelings. Love the new features but worried about stability issues.", "sentiment": "neutral", "category": "general", "source": "email"},
    {"text": "Noticed faster signup but slower page loads. Net neutral for us so far.", "sentiment": "neutral", "category": "performance", "source": "in_app"},
    {"text": "Waiting to see if the crash issues get fixed before recommending to my team.", "sentiment": "neutral", "category": "general", "source": "in_app"},
]

RELEASE_NOTES_DATA = {
    "version": "v2.4.0",
    "release_date": RELEASE_DATE,
    "title": "Enhanced Onboarding & Dashboard Redesign",
    "features": (
        "1. Redesigned onboarding flow with streamlined 3-step signup\n"
        "2. New dashboard analytics widgets with customizable layouts\n"
        "3. Payment flow optimization with faster checkout processing\n"
        "4. Improved search functionality with instant results\n"
        "5. Feature adoption tracking dashboard for teams\n"
        "6. UI refresh with modern design language"
    ),
    "known_issues": (
        "1. Intermittent crash on devices with less than 4GB RAM during checkout\n"
        "2. Increased API latency (p95) under heavy concurrent load\n"
        "3. Payment timeout edge case on connections slower than 3G\n"
        "4. Dashboard widgets may not render correctly on Firefox 108 and below\n"
        "5. Report export may fail intermittently for date ranges exceeding 90 days\n"
        "6. Payment confirmation email delivery delay under high volume"
    ),
    "status": "released",
}


def _generate_metric_value(base: float, noise: float) -> float:
    """Generate a metric value with random noise around the base."""
    return base + random.uniform(-noise, noise)


def seed_metrics(session) -> None:
    """Seed 14 days of daily metrics (7 pre-release, 7 post-release)."""
    for day_offset in range(14):
        current_date = START_DATE + timedelta(days=day_offset)
        is_post_release = current_date >= RELEASE_DATE

        for metric_name, config in METRICS_CONFIG.items():
            base = config["post"] if is_post_release else config["pre"]
            value = _generate_metric_value(base, config["noise"])

            # Ensure non-negative values
            value = max(0, value)

            session.add(DailyMetric(
                date=current_date,
                metric_name=metric_name,
                value=round(value, 4),
                unit=config["unit"],
            ))

    logger.info("Seeded 14 days of daily metrics across 9 metric types.")


def seed_feedback(session) -> None:
    """Seed user feedback entries spread across post-release days."""
    post_release_dates = [
        RELEASE_DATE + timedelta(days=i) for i in range(7)
    ]

    for entry in FEEDBACK_ENTRIES:
        submitted = random.choice(post_release_dates)
        session.add(UserFeedback(
            submitted_date=submitted,
            feedback_text=entry["text"],
            sentiment=entry["sentiment"],
            category=entry["category"],
            source=entry["source"],
        ))

    logger.info(f"Seeded {len(FEEDBACK_ENTRIES)} user feedback entries.")


def seed_release_notes(session) -> None:
    """Seed the release notes for v2.4.0."""
    session.add(ReleaseNote(**RELEASE_NOTES_DATA))
    logger.info("Seeded release notes for v2.4.0.")


def seed_database() -> None:
    """Seed all tables if the database is empty."""
    with get_session() as session:
        existing_count = session.query(DailyMetric).count()
        if existing_count > 0:
            logger.info("Database already seeded. Skipping.")
            return

        seed_metrics(session)
        seed_feedback(session)
        seed_release_notes(session)
        logger.info("Database seeding complete.")
