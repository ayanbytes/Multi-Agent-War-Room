import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DB_URL
from app.db.models import Base

logger = logging.getLogger(__name__)

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def create_tables() -> None:
    """Create all database tables if they don't exist."""
    Base.metadata.create_all(engine)
    logger.info("Database tables created/verified.")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
