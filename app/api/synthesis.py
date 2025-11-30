# app/api/v1/synthesis.py

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
import uuid
# We no longer need rq or database imports here; they are now Engine-side responsibilities.
# from rq import Queue 
# from app.core.message_broker import get_redis_connection

from app.api.auth.dependencies import get_current_active_user_id 
# Import the existing Engine Client dependency
from app.api.core.engine_client import get_engine_client, EngineClient 


router = APIRouter(tags=["Synthesis"], prefix="/synthesis")

class JobInitiationResponse(BaseModel):
    job_id: uuid.UUID = Field(..., description="The unique ID to poll for job status.")
    status_url: str = Field(..., description="The URL for polling the job status.")
    message: str = "Job successfully enqueued. Check status_url for result."

# Pydantic model for the Daily Check Answer payload
class DailyCheckAnswerPayload(BaseModel):
    question_id: int = Field(..., description="The ID of the question being answered.")
    answer_text: str = Field(..., max_length=1024, description="The user's response text.")

@router.post(
    "/daily-check/submit", 
    response_model=JobInitiationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submits a Daily Check answer via proxy and initiates asynchronous implicit-check logic."
)
async def submit_daily_check_answer(
    payload: DailyCheckAnswerPayload,
    user_id: str = Depends(get_current_active_user_id),
    engine_client: EngineClient = Depends(get_engine_client),
):
    """
    **CRITICAL ASYNC FLOW ENFORCEMENT (Proxied)**
    1. Validate user and extract ID (App responsibility).
    2. Synchronously proxy the entire request to the Engine (App responsibility).
    3. The Engine handles the DB write, RQ enqueue, and response (Engine responsibility).
    4. Return the Engine's Job ID to the Client (App responsibility).
    """
    
    # Payload is sent as a dictionary, using the existing _proxy_request method
    response_data = await engine_client.proxy_request(
        method="POST",
        user_id=user_id,
        engine_route="submit_daily_answer_proxy", # New route defined in the spec
        payload=payload.model_dump() # Send the Pydantic data
    )

    # The Engine is responsible for the JobInitiationResponse contract
    return JobInitiationResponse(**response_data)