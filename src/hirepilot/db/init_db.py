"""Database initialization script to create tables and seed default settings."""

from __future__ import annotations

import sys
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from hirepilot.db.models import Base, Setting
from hirepilot.db.session import engine, get_db_session
from hirepilot.logger import get_logger

logger = get_logger("db.init")

DEFAULT_SETTINGS = [
    ("dry_run", "true", "Safety switch: drafts only if true, sends if false"),
    ("autopilot", "false", "Autonomous background execution"),
    ("kill_switch", "false", "Master circuit breaker"),
    ("daily_send_cap", "5", "Maximum outreach emails per day"),
    ("min_send_delay_seconds", "180", "Minimum delay between emails"),
    ("max_send_delay_seconds", "600", "Maximum delay between emails"),
]


def init_db(target_engine: Engine | None = None) -> None:
    """Create all schema tables and populate default settings."""
    eng = target_engine or engine
    logger.info("Initializing HirePilot database tables...")
    Base.metadata.create_all(bind=eng)

    session_cls = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    with session_cls() as session:
        for key, val, desc in DEFAULT_SETTINGS:
            existing = session.query(Setting).filter_by(key=key).first()
            if not existing:
                session.add(Setting(key=key, value=val, description=desc))
        session.commit()

    logger.info("Database schema successfully created and verified.")


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
