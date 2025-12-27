from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from engine.core.database import get_rls_session
from engine.models.user import User # Assuming ORM model exists

router = APIRouter(prefix="/internal/v1/auth")

@router.post("/validate")
async def validate_user(credentials: dict, db: Session = Depends(get_rls_session)):
    # In production, use passlib.hash.bcrypt.verify
    user = db.query(User).filter(User.username == credentials['username']).first()
    if not user or not (credentials['password'] == user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Return user_id to App Service for JWT signing
    return {"user_id": str(user.user_id), "username": user.username}