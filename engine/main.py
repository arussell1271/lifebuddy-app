from fastapi import FastAPI

app = FastAPI(title="LifeBuddy Engine")


@app.get("/", tags=["health"])
def read_root():
    return {"service": "lifebuddy-engine", "status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
