@router.post("/login")
async def login(data: LoginSchema, engine: EngineClient = Depends(get_engine_client)):
    # 1. Proxy to Engine for validation
    user_data = await engine._proxy_request("POST", None, "auth/validate", payload=data.dict())
    
    # 2. Generate JWT with 'sub' as user_id
    token = create_access_token(data={"sub": user_data['user_id']})
    return {"access_token": token, "token_type": "bearer"}