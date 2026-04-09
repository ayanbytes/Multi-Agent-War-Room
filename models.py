from sqlalchemy import Column, Integer, Float, String, Date, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DailyMetric(Base):
    """Stores daily metric measurements for pre- and post-release tracking."""
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50))

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "metric_name": self.metric_name,
            "value": round(self.value, 4),
            "unit": self.unit,
        }


class UserFeedback(Base):
    """Stores user feedback entries collected after the release."""
    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submitted_date = Column(Date, nullable=False)
    feedback_text = Column(Text, nullable=False)
    sentiment = Column(String(20))
    category = Column(String(50))
    source = Column(String(50))

    def to_dict(self) -> dict:
        return {
            "submitted_date": self.submitted_date.isoformat(),
            "feedback_text": self.feedback_text,
            "sentiment": self.sentiment,
            "category": self.category,
            "source": self.source,
        }


class ReleaseNote(Base):
    """Stores release notes including features and known issues."""
    __tablename__ = "release_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(20), nullable=False)
    release_date = Column(Date, nullable=False)
    title = Column(String(200))
    features = Column(Text)
    known_issues = Column(Text)
    status = Column(String(20))

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "release_date": self.release_date.isoformat(),
            "title": self.title,
            "features": self.features,
            "known_issues": self.known_issues,
            "status": self.status,
        }
