# engine/core/database.py

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# --- Configuration ---
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "dev_db")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "lifebuddy_db")
POSTGRES_USER_RLS_PASS = os.environ.get("POSTGRES_USER_RLS_PASS", "DEFAULT_RLS_PASS")
RLS_USER = "cognitive_engine_rls"

# RLS-enforcing connection string
DATABASE_URL = (
    f"postgresql+psycopg2://{RLS_USER}:{POSTGRES_USER_RLS_PASS}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_rls_session(user_id: str) -> Generator[Session, None, None]:
    """
    MANDATORY: Provides a database session with the RLS user context set.
    Used by ALL Engine Proxied API routes and RQ Workers.
    """
    db = SessionLocal()
    try:
        # CRITICAL: Execute the RLS context setting function
        db.execute(f"SELECT set_config('app.current_user_id', '{user_id}', false);")
        db.execute("SET search_path TO app, public;") 
        yield db
        db.commit() 
    except Exception:
        db.rollback() 
        raise
    finally:
        db.close()