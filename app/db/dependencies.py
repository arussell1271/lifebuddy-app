# app/db/dependencies.py

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
from fastapi import Depends, HTTPException, status
from typing import Generator
from app.core.config import settings # CRITICAL: Assumes configuration is in app.core.config
from app.api.auth.dependencies import get_current_active_user_id # Assumes the JWT dependency exists

# --- RLS Session Setup ---
# CRITICAL: This URL MUST use the POSTGRES_USER_RLS_PASS credentials.
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL_RLS 
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_rls_session(user_id: str = Depends(get_current_active_user_id)) -> Generator[Session, None, None]:
    """
    FastAPI Dependency to enforce Row-Level Security (RLS).
    1. Opens a DB session using the RLS-enforced role ('cognitive_engine_rls').
    2. Sets the application context variable 'app.current_user_id' using the authenticated user_id.
    3. The database's RLS policies automatically filter all subsequent queries.
    """
    db: Session = SessionLocal()
    try:
        # 1. CRITICAL: Set the application context for RLS enforcement
        # The 'false' parameter ensures the setting is local to the transaction.
        db.execute(
            text(f"SELECT set_config('app.current_user_id', '{user_id}', false);")
        )
        yield db
    except Exception as e:
        # Proper error handling ensures the database session is closed on failure
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database RLS setup failed: {e}"
        )
    finally:
        db.close()

# Example usage in an App Service endpoint:
# from app.db.dependencies import get_db_rls_session
# @router.get("/user/profile")
# def get_profile(db: Session = Depends(get_db_rls_session)):
#     return db.query(User).first() # This query is now RLS-protected