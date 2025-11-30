# engine/api/v1/internal.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import uuid
from sqlalchemy.orm import Session
from rq import Queue
import redis # Used to get the Redis connection directly in the Engine
import os

# RLS DB Session
from engine.core.database import get_rls_session
# Placeholder ORM model for pre_synthesis_answers
from engine.models.daily_check import PreSynthesisAnswer 

router = APIRouter(tags=["Internal"], prefix="/internal/v1")

class JobInitiationResponse(BaseModel):
    job_id: uuid.UUID = Field(..., description="The unique ID to poll for job status.")
    status_url: str = Field(..., description="The URL for polling the job status.")
    message: str = "Job successfully enqueued. Check status_url for result."

# Pydantic model for the Daily Check Answer payload (must match the App's contract)
class DailyCheckAnswerPayload(BaseModel):
    question_id: int = Field(...)
    answer_text: str = Field(..., max_length=1024)

# Utility to get RLS-scoped DB session for this specific endpoint
def get_db(user_id: str):
    with get_rls_session(user_id) as db:
        yield db

# Utility to get Redis connection for job queuing
def get_redis_conn():
    # Load from environment variables (REDIS_HOST)
    host = os.environ.get("REDIS_HOST", "message-broker") 
    return redis.Redis(host=host, port=6379, db=0)

@router.post(
    "/user/{user_id}/submit_daily_answer_proxy", 
    response_model=JobInitiationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="[INTERNAL] Proxied: Inserts answer, initiates async implicit-check."
)
def submit_daily_answer_proxy(
    user_id: str,
    payload: DailyCheckAnswerPayload,
    db: Session = Depends(get_db),
    redis_conn = Depends(get_redis_conn) 
):
    """
    Handles the Proxied Request: Synchronous write + Asynchronous job enqueue.
    1. Insert the answer into the database using RLS.
    2. Enqueue the heavy LLM processing job.
    3. Return the job ID.
    """
    
    try:
        # 1. RLS-enforced Synchronous Database Write (Engine responsibility)
        new_answer = PreSynthesisAnswer(
            user_id=user_id, 
            question_id=payload.question_id,
            answer_text=payload.answer_text,
            status="PENDING_IMPLICIT_CHECK" 
        )
        db.add(new_answer)
        db.flush() # Get the new record ID before committing
        
        # 2. Enqueue the Asynchronous Job
        q = Queue(connection=redis_conn)
        
        # Target the actual heavy lifting logic
        job = q.enqueue(
            'engine.tasks.daily_check_tasks.process_implicit_check', 
            args=(user_id, new_answer.id), 
            job_timeout='10m', 
        )
        
        # The transaction commits upon successful exit from the get_db/get_rls_session context
        
        # 3. Return the immediate response
        return JobInitiationResponse(
            job_id=job.id, 
            # Note: The status URL points back to the App's public API
            status_url="/api/v1/synthesis/job-status/" + str(job.id)
        )

    except Exception as e:
        # Propagate the error up the proxy chain
        print(f"Engine Error during submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Engine failed to process request and enqueue job."
        )