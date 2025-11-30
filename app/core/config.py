# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# CRITICAL: This class loads environment variables from the Docker container
# or a local .env file. Variables MUST match the keys defined in 02 infrastructure setup.md.
class Settings(BaseSettings):
    """
    Core Configuration Settings for the App Service (The Body).
    Loads variables required for RLS, Messaging, and Proxied API calls.
    """
    model_config = SettingsConfigDict(
        env_file=".env.dev", 
        env_file_encoding='utf-8',
        extra='ignore' # Ignore variables not explicitly defined here
    )

    # --- Database RLS Configuration (Mandatory Security) ---
    # The URL used by the App Service for all RLS-enforced operations.
    # Must connect as the 'cognitive_engine_rls' user.
    DATABASE_URL_RLS: str 

    # --- Service Communication (Decoupling & Asynchronous Flow) ---
    # 1. Redis/Message Broker
    # Used for Asynchronous Job Initiation (POST /synthesis/job)
    REDIS_HOST: str = "message-broker" # Default to the Docker service name
    REDIS_PORT: int = 6379 
    
    # 2. Engine Service Client (Proxied API Pattern)
    # Used for synchronous, light-weight calls to the Engine (e.g., Daily Check Status)
    ENGINE_SERVICE_URL: str # Default to the Docker service name. Now mandatory, no default for security best practice

    # --- Security & Auth ---
    # Used for JWT decoding and validation in the App Service
    JWT_SECRET_KEY: str # JWT signing key (CRITICAL SECRET)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Standard lifespan

    # --- System Information ---
    SERVICE_NAME: str = "LifeBuddy App Service"
    API_V1_STR: str = "/api/v1"

# Instantiate the settings object globally for use throughout the App Service
settings = Settings()