# app/api/v1/synthesis.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import uuid
from rq import Queue
# Assuming Redis connection setup in app.core.message_broker
from app.core.message_broker import get_redis_connection
from app.api.auth.dependencies import get_current_active_user_id 

router = APIRouter(tags=["Synthesis"], prefix="/synthesis")

class JobInitiationResponse(BaseModel):
    job_id: uuid.UUID
    status: str = "PENDING"
    detail: str = "Synthesis job accepted for asynchronous processing."

@router.post("/job", response_model=JobInitiationResponse, status_code=status.HTTP_202_ACCEPTED)
async def initiate_cognitive_synthesis_job(
    user_id: str = Depends(get_current_active_user_id), 
    redis_conn = Depends(get_redis_connection)
):
    """
    Submits the Cognitive Synthesis request to the message queue for the Engine to pick up.
    This call returns immediately (202 Accepted) to comply with the Asynchronous Flow rule.
    """
    # CRITICAL: Get the Redis Queue instance
    q = Queue('default', connection=redis_conn) 
    
    # CRITICAL: Enqueue the Engine's main job function. 
    # The Engine service must have the 'engine.jobs.synthesis_worker.perform_synthesis' function accessible.
    job = q.enqueue(
        'engine.jobs.synthesis_worker.perform_synthesis', 
        str(user_id), # Ensure UUID is passed as a string
        job_timeout='20m', # Allow ample time for LLM/vector heavy tasks
        # Optional: Set a result TTL to control Redis memory usage
    )
    
    return JobInitiationResponse(job_id=job.id)

# --- NOTE: Additional endpoints for GET /job/{job_id} status and GET /{synthesis_id} retrieval must be implemented.
# The retrieval endpoint MUST use the RLS session dependency.