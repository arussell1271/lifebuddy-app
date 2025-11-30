# app/services/engine_client.py

import httpx
from fastapi import HTTPException, status, Depends
from app.core.config import settings # Assumes settings.ENGINE_SERVICE_URL is defined

class EngineClient:
    """
    Client for making synchronous, security-proxied calls to the Cognitive Engine.
    Enforces the Proxied API Pattern: App -> (Secure) Engine/internal/{user_id}/{route}
    """
    def __init__(self):
        # The internal Docker service name (e.g., 'http://cognitive-engine')
        self.base_url = settings.ENGINE_SERVICE_URL 
        # Use httpx.AsyncClient for modern FastAPI integration
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=5.0) # Set a strict timeout

    async def _proxy_request(self, method: str, user_id: str, engine_route: str, payload: dict = None) -> dict:
        """
        Generic proxy method that adheres to the Engine's internal API contract.
        """
        path = f"/internal/{user_id}/{engine_route}"
        
        try:
            # The Engine is responsible for using the user_id to perform its internal, non-RLS logic.
            response = await self.client.request(method, path, json=payload)
            response.raise_for_status() # Raise an exception for 4xx/5xx responses
            return response.json()
        
        except httpx.HTTPStatusError as e:
            # Relays Engine errors back to the public client
            detail = e.response.json().get('detail', f"Engine reported error for route: {engine_route}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=detail
            )
        except httpx.RequestError as e:
            # Handles connection failures (Engine is unreachable)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Engine Service ('{self.base_url}') is unavailable or timed out."
            )

    async def get_daily_check_status(self, user_id: str) -> dict:
        """Proxies the GET /get_daily_check_status request to the Engine."""
        return await self._proxy_request("GET", user_id, "get_daily_check_status")

    async def create_action_item(self, user_id: str, item_data: dict) -> dict:
        """Proxies the POST /create_action_item request to the Engine."""
        # item_data will be the payload passed to the Engine
        return await self._proxy_request("POST", user_id, "create_action_item", payload=item_data)

# Dependency for FastAPI endpoints
def get_engine_client() -> EngineClient:
    """Provides an instance of the EngineClient."""
    return EngineClient()