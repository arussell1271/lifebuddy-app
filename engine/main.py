import sys
from datetime import datetime

from fastapi import FastAPI

app = FastAPI(title="LifeBuddy Engine")


@app.get("/", tags=["health"])
def read_root():
    """Health check and service info endpoint."""
    import fastapi
    import uvicorn
    
    return {
        "service": "lifebuddy-engine",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "versions": {
            "python": sys.version.split()[0],
            "fastapi": fastapi.__version__,
            "uvicorn": uvicorn.__version__,
        },
        "platform": sys.platform,
        "port": 8001,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
