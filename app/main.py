from fastapi import FastAPI

# CRITICAL: This 'app' object is what the server command 'uvicorn app.main:app' loads.
app = FastAPI(
    title="LifeBuddy Frontend API Test",
    version="1.0.0",
)

@app.get("/")
def read_root():
    """Confirms the Frontend API is running."""
    return {"status": "Frontend API Test is UP and Running", "service": "dev_app"}

# You can add a quick check for environment variables if you suspect those are failing
# @app.get("/env")
# def check_env():
#     import os
#     return {"db_host": os.environ.get("POSTGRES_HOST")}