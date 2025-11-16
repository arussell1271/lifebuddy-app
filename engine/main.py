from fastapi import FastAPI

# CRITICAL: This 'app' object is what the server command 'gunicorn engine.main:app' loads.
app = FastAPI(
    title="LifeBuddy Cognitive Engine Test",
    version="1.0.0",
)

@app.get("/")
def read_root():
    """Confirms the Cognitive Engine is running."""
    return {"status": "Cognitive Engine Test is UP and Running", "service": "dev_engine"}