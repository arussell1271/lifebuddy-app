import sys
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx  # type: ignore
import os
import time

app = FastAPI(title="LifeBuddy App")

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

ENGINE_BASE = os.environ.get("ENGINE_BASE", "http://lifebuddy-engine:8001")
APP_GREEN_THRESHOLD = 0.20
APP_AMBER_THRESHOLD = 1.50


def _badge(label: str, level: str) -> str:
    colors = {"green": "#10b981", "amber": "#f59e0b", "red": "#ef4444"}
    color = colors.get(level, "#6b7280")
    return f"<strong style='color:{color};margin-right:6px'>{label}</strong>"


def _severity_from_latency(lat: float | None) -> str:
    if lat is None:
        return "red"
    if lat < APP_GREEN_THRESHOLD:
        return "green"
    if lat <= APP_AMBER_THRESHOLD:
        return "amber"
    return "red"


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{ENGINE_BASE}/api/v1/auth/login", data={"username": username, "password": password}, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Engine unreachable"})
    if resp.status_code != 200:
        return templates.TemplateResponse("login.html", {"request": request, "error": resp.json().get("detail", "login failed")})
    token = resp.json().get("access_token")
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@app.post("/register")
async def register_post(request: Request, username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{ENGINE_BASE}/api/v1/auth/register", data={"username": username, "password": password}, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("register.html", {"request": request, "error": "Engine unreachable"})
    if resp.status_code not in (200, 201):
        return templates.TemplateResponse("register.html", {"request": request, "error": resp.json().get("detail", "register failed")})
    return RedirectResponse(url="/login", status_code=303)


@app.get("/reset-password", response_class=HTMLResponse)
def reset_get(request: Request):
    return templates.TemplateResponse("reset.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers=headers, timeout=5.0)
            db = await client.get(f"{ENGINE_BASE}/api/v1/db_test", timeout=5.0)
        except Exception:
            return templates.TemplateResponse("dashboard.html", {"request": request, "user": None, "db_status": "engine_unreachable"})
    user = me.json() if me.status_code == 200 else None
    db_status = db.json() if db.status_code == 200 else {"status": "error", "detail": db.text}
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "db_status": db_status})


@app.get("/health")
def health():
    return {"service": "lifebuddy-app", "status": "operational", "port": 8000}


@app.get("/internal/status", response_class=HTMLResponse)
async def internal_status_app(request: Request):
        # Check Engine reachability
        engine_ok = False
        engine_detail = "unreachable"
        engine_lat = None
        try:
                start = time.time()
                async with httpx.AsyncClient(timeout=3.0) as client:
                        r = await client.get(f"{ENGINE_BASE}/internal/status")
                        engine_lat = time.time() - start
                        engine_ok = r.status_code == 200
                        engine_detail = f"{r.status_code}"
        except Exception as e:
                engine_ok = False
                engine_detail = str(e)

        engine_level = _severity_from_latency(engine_lat) if engine_ok else "red"

        # Check templates and static directories
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        templates_ok = os.path.isdir(templates_dir)
        static_ok = os.path.isdir(static_dir)

        overall = "green"
        if not engine_ok or not templates_ok or not static_ok:
                overall = "red"

        html = f"""
<html><head><title>App Internal Status</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 18px }}
        .card {{ background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06) }}
        .service {{ margin:8px 0 }}
    </style>
</head><body>
    <div class="card">
        <h2>App Internal Status — {overall.upper()}</h2>
        <div class="service">{_badge('Engine', engine_level)}Engine: {engine_detail} — latency: {engine_lat if engine_lat is not None else 'n/a'}</div>
        <div class="service">{_badge('Templates', 'green' if templates_ok else 'red')}Templates dir: {'present' if templates_ok else 'missing'}</div>
        <div class="service">{_badge('Static', 'green' if static_ok else 'red')}Static dir: {'present' if static_ok else 'missing'}</div>
    </div>
</body></html>
"""

        return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn  # type: ignore

    uvicorn.run(app, host="0.0.0.0", port=8000)
