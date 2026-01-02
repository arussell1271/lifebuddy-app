import sys
from datetime import datetime

from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Ensure `shared/` package is importable when running inside the container image
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def _load_shared_renderer():
    import importlib.util
    from pathlib import Path
    base = Path(__file__).resolve().parents[1]
    renderer_file = base / "shared" / "render_status.py"
    spec = importlib.util.spec_from_file_location("shared.render_status", str(renderer_file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.render_status

render_status = _load_shared_renderer()
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

    # Use shared renderer
    title = f"App Internal Status — {overall.upper()}"
    subtitle = "Quick check of App assets and Engine reachability."

    def _fmt(lat: float | None) -> str:
        return f"{lat*1000:.2f} ms" if isinstance(lat, (int, float)) else "n/a"

    label_map = {"green": "OK", "amber": "Degraded", "red": "Critical"}

    # Build subcomponent status lists for Templates and Static directories
    template_expected = ["landing.html", "login.html", "register.html", "dashboard.html", "status_template.html"]
    template_subs = []
    for tname in template_expected:
        p = os.path.join(templates_dir, tname)
        exists = os.path.isfile(p)
        template_subs.append({
            "status_class": "green" if exists else "red",
            "status_label": "OK" if exists else "MISSING",
            "name": tname,
            "detail": "present" if exists else "missing",
        })

    static_expected = ["styles.css", "app.js", "logo.png"]
    static_subs = []
    for sname in static_expected:
        p = os.path.join(static_dir, sname)
        exists = os.path.isfile(p)
        static_subs.append({
            "status_class": "green" if exists else "red",
            "status_label": "OK" if exists else "MISSING",
            "name": sname,
            "detail": "present" if exists else "missing",
        })

    services = [
        {
            "status_class": engine_level,
            "status_label": label_map.get(engine_level, engine_level.upper()),
            "component": "Engine",
            "detail": f"Status: {engine_detail} — latency: {_fmt(engine_lat)}",
            "description": "Internal Engine service — handles auth, synthesis, and DB requests on the secure network (App communicates only with the Engine).",
        },
        {
            "status_class": "green" if templates_ok else "red",
            "status_label": "OK" if templates_ok else "MISSING",
            "component": "Templates Directory",
            "detail": "present" if templates_ok else "missing",
            "description": "Jinja2 templates used to render App HTML pages (templates/*.html); shared rendering templates live in `shared/`.",
            "subcomponents": template_subs if templates_ok else [],
        },
        {
            "status_class": "green" if static_ok else "red",
            "status_label": "OK" if static_ok else "MISSING",
            "component": "Static Directory",
            "detail": "present" if static_ok else "missing",
            "description": "Static assets (CSS, JS, images) served at `/static` used for frontend styling and client-side scripts.",
            "subcomponents": static_subs if static_ok else [],
        },
    ]

    thresholds = [
        {"color": "#10b981", "label": "Green", "text": f"OK — latency < {int(APP_GREEN_THRESHOLD*1000)} ms"},
        {"color": "#f59e0b", "label": "Amber", "text": f"Degraded — latency {int(APP_GREEN_THRESHOLD*1000)} ms–{int(APP_AMBER_THRESHOLD*1000)} ms"},
        {"color": "#ef4444", "label": "Red", "text": f"Critical — latency > {int(APP_AMBER_THRESHOLD*1000)} ms or unreachable"},
    ]

    footer = "This page is for local diagnostics only. The App does not access the database or LLM directly; it communicates with the Engine on the secure network."
    html = render_status(title=title, subtitle=subtitle, services=services, thresholds=thresholds, footer=footer)
    return HTMLResponse(content=html)


# Startup-time static scan to ensure `app/` source does not import DB/LLM libraries
@app.on_event("startup")
def _verify_app_code_safety():
    import re
    from pathlib import Path

    repo_base = Path(__file__).resolve().parents[1]
    app_dir = repo_base / "app"
    patterns = [r"\bimport\s+psycopg2\b", r"\bfrom\s+psycopg2\b", r"\bimport\s+sqlalchemy\b", r"\bfrom\s+sqlalchemy\b", r"\bimport\s+pgvector\b", r"\bfrom\s+pgvector\b", r"\bollama\b", r"\bopenai\b"]
    hits = []
    for p in app_dir.rglob("*.py"):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for pat in patterns:
            if re.search(pat, text):
                hits.append((str(p.relative_to(repo_base)), pat))
    if hits:
        details = ", ".join([f"{f} (pattern: {pat})" for f, pat in hits])
        msg = f"Prohibited DB/LLM import patterns found in App source: {details}. The App must not import or access DB/LLM libraries directly."
        raise RuntimeError(msg)


if __name__ == "__main__":
    import uvicorn  # type: ignore

    uvicorn.run(app, host="0.0.0.0", port=8000)
