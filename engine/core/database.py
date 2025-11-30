# engine/core/database.py

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, Session

# --- Configuration (Standard) ---
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "dev_db")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "lifebuddy_db")

# --- 1. RLS-ENFORCING CONNECTION (For all user-facing, proxied APIs and RQ workers) ---
POSTGRES_USER_RLS_PASS = os.environ.get("POSTGRES_USER_RLS_PASS", "DEFAULT_RLS_PASS")
RLS_USER = "cognitive_engine_rls"

RLS_DATABASE_URL = (
    f"postgresql+psycopg2://{RLS_USER}:{POSTGRES_USER_RLS_PASS}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
)

engine_rls = create_engine(RLS_DATABASE_URL, pool_pre_ping=True)
SessionLocalRLS = sessionmaker(autocommit=False, autoflush=False, bind=engine_rls)

@contextmanager
def get_rls_session(user_id: str) -> Generator[Session, None, None]:
    """
    MANDATORY: Provides a database session with the RLS user context set.
    Used by ALL Engine Proxied API routes and RQ Workers.
    """
    db = SessionLocalRLS()
    try:
        # CRITICAL: Implement the RLS context setting function
        db.execute(
            text("SELECT set_config('app.current_user_id', :user_id, FALSE)"),
            {"user_id": user_id}
        )
        yield db
    finally:
        db.close()

# --- 2. RLS-BYPASSING/FULL ACCESS CONNECTION (MANDATORY for Maintenance Cron Jobs ONLY) ---
POSTGRES_USER_FULL_PASS = os.environ.get("POSTGRES_USER_FULL_PASS", "DEFAULT_FULL_PASS")
FULL_USER = "cognitive_engine_full"

FULL_DATABASE_URL = (
    f"postgresql+psycopg2://{FULL_USER}:{POSTGRES_USER_FULL_PASS}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
)

# This engine is ONLY used by the maintenance cron job.
engine_full = create_engine(FULL_DATABASE_URL, pool_pre_ping=True)
SessionLocalFull = sessionmaker(autocommit=False, autoflush=False, bind=engine_full)

@contextmanager
def get_full_access_session() -> Generator[Session, None, None]:
    """
    MANDATORY: Provides a session with the RLS-bypassing role.
    Used ONLY by the db_maintenance_cron service.
    """
    db = SessionLocalFull()
    try:
        # No RLS context setting required.
        yield db
    finally:
        db.close()