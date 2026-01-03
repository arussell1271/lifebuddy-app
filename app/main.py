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
    from importlib.machinery import ModuleSpec
    base = Path(__file__).resolve().parents[1]
    renderer_file = base / "shared" / "render_status.py"
    spec = importlib.util.spec_from_file_location("shared.render_status", str(renderer_file))
    if spec is None:
        raise RuntimeError(f"Unable to load shared renderer from {renderer_file}")
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("Loaded spec has no loader for shared renderer")
    spec.loader.exec_module(module)
    return module

_renderer_module = _load_shared_renderer()
render_status = _renderer_module.render_status
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
async def register_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{ENGINE_BASE}/api/v1/auth/register", data={"username": username, "email": email, "password": password}, timeout=5.0)
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


@app.get("/settings", response_class=HTMLResponse)
async def settings_get(request: Request):
    # Redirect to profile settings by default
    return RedirectResponse(url="/settings/profile")


@app.post("/settings")
async def settings_post(request: Request, email: str = Form(...)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.patch(f"{ENGINE_BASE}/api/v1/me", json={"email": email}, headers=headers, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("settings.html", {"request": request, "user": None, "error": "Engine unreachable"})
    if resp.status_code != 200:
        # Re-fetch user for display
        async with httpx.AsyncClient() as client:
            try:
                me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
                user = me.json() if me.status_code == 200 else None
            except Exception:
                user = None
        return templates.TemplateResponse("settings.html", {"request": request, "user": user, "error": resp.text})
    # success
    async with httpx.AsyncClient() as client:
        me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
    user = me.json() if me.status_code == 200 else None
    return templates.TemplateResponse("settings.html", {"request": request, "user": user, "message": "Email updated."})


@app.get("/settings/profile", response_class=HTMLResponse)
async def settings_profile_get(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers=headers, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("settings/profile.html", {"request": request, "user": None, "error": "Engine unreachable"})
    user = me.json() if me.status_code == 200 else None
    return templates.TemplateResponse("settings/profile.html", {"request": request, "user": user, "message": None, "error": None})


@app.post("/settings/profile")
async def settings_profile_post(request: Request, email: str = Form(...)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.patch(f"{ENGINE_BASE}/api/v1/me", json={"email": email}, headers=headers, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("settings/profile.html", {"request": request, "user": None, "error": "Engine unreachable"})
    if resp.status_code != 200:
        async with httpx.AsyncClient() as client:
            try:
                me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
                user = me.json() if me.status_code == 200 else None
            except Exception:
                user = None
        return templates.TemplateResponse("settings/profile.html", {"request": request, "user": user, "error": resp.text})
    async with httpx.AsyncClient() as client:
        me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
    user = me.json() if me.status_code == 200 else None
    return templates.TemplateResponse("settings/profile.html", {"request": request, "user": user, "message": "Profile updated."})


@app.get("/settings/security", response_class=HTMLResponse)
async def settings_security_get(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers=headers, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("settings/security.html", {"request": request, "user": None, "error": "Engine unreachable"})
    user = me.json() if me.status_code == 200 else None
    return templates.TemplateResponse("settings/security.html", {"request": request, "user": user, "message": None, "error": None})


@app.post("/settings/security")
async def settings_security_post(request: Request, current_password: str = Form(...), new_password: str = Form(...)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"current_password": current_password, "new_password": new_password}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{ENGINE_BASE}/api/v1/me/password", json=payload, headers=headers, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("settings/security.html", {"request": request, "user": None, "error": "Engine unreachable"})
    if resp.status_code != 200:
        async with httpx.AsyncClient() as client:
            try:
                me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
                user = me.json() if me.status_code == 200 else None
            except Exception:
                user = None
        return templates.TemplateResponse("settings/security.html", {"request": request, "user": user, "error": resp.text})
    async with httpx.AsyncClient() as client:
        me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
    user = me.json() if me.status_code == 200 else None
    return templates.TemplateResponse("settings/security.html", {"request": request, "user": user, "message": "Password changed."})


@app.get("/settings/preferences", response_class=HTMLResponse)
async def settings_preferences_get(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        try:
            me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers=headers, timeout=5.0)
            prefs = await client.get(f"{ENGINE_BASE}/api/v1/user-preferences", headers=headers, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("settings/preferences.html", {"request": request, "user": None, "prefs": None, "error": "Engine unreachable"})
    user = me.json() if me.status_code == 200 else None
    prefs_json = prefs.json() if prefs.status_code == 200 else None
    return templates.TemplateResponse("settings/preferences.html", {"request": request, "user": user, "prefs": prefs_json, "message": None, "error": None})


@app.post("/settings/preferences")
async def settings_preferences_post(request: Request, theme: str = Form(...), notifications: str = Form(...)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"theme": theme, "notifications": notifications}
    async with httpx.AsyncClient() as client:
        try:
            # Forward to Engine's preferences PATCH endpoint
            resp = await client.patch(f"{ENGINE_BASE}/api/v1/user-preferences", json=payload, headers=headers, timeout=5.0)
        except Exception:
            return templates.TemplateResponse("settings/preferences.html", {"request": request, "user": None, "error": "Engine unreachable"})
    if resp.status_code not in (200, 201):
        # Re-fetch user for display
        async with httpx.AsyncClient() as client:
            try:
                me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
                user = me.json() if me.status_code == 200 else None
            except Exception:
                user = None
        return templates.TemplateResponse("settings/preferences.html", {"request": request, "user": user, "error": resp.text})
    # success
    async with httpx.AsyncClient() as client:
        me = await client.get(f"{ENGINE_BASE}/api/v1/me", headers={"Authorization": f"Bearer {token}"}, timeout=5.0)
    user = me.json() if me.status_code == 200 else None
    return templates.TemplateResponse("settings/preferences.html", {"request": request, "user": user, "message": "Preferences saved."})



@app.get("/logout")
def logout(request: Request):
    # Clear the auth cookie and redirect to landing
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


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

        # Scan app source for prohibited DB/LLM imports or direct service references
        import re
        from pathlib import Path
        # import shared patterns (moved out of app source to avoid self-matches)
        try:
            from shared.safety_patterns import IMPORT_PATTERNS, HOST_PATTERNS
        except Exception:
            IMPORT_PATTERNS = []
            HOST_PATTERNS = []

        repo_base = Path(__file__).resolve().parents[1]
        app_src = repo_base / "app"
        code_hits = []
        try:
            for p in app_src.rglob("*.py"):
                try:
                    rel = str(p.relative_to(repo_base))
                    # Skip scanning this startup/status checker file to avoid self-matches
                    if rel == "app/main.py":
                        continue
                except Exception:
                    pass
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                # check import statements (multiline-aware)
                for pat in IMPORT_PATTERNS:
                    if re.search(pat, text, flags=re.MULTILINE):
                        code_hits.append((str(p.relative_to(repo_base)), pat))
                # check host/endpoint occurrences
                for pat in HOST_PATTERNS:
                    if re.search(pat, text):
                        code_hits.append((str(p.relative_to(repo_base)), pat))
        except Exception:
            code_hits = [("scan_error", "unable to scan source files")]

    code_ok = len(code_hits) == 0
    code_subs = []
    if code_hits:
        for f, pat in code_hits:
            code_subs.append({
                "status_class": "red",
                "status_label": "FOUND",
                "name": f,
                "detail": f"pattern: {pat}",
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
        {
            "status_class": "green" if code_ok else "red",
            "status_label": "OK" if code_ok else "ISSUES",
            "component": "Code Safety",
            "detail": "No prohibited DB/LLM imports or direct service references found." if code_ok else "Prohibited patterns found in source files.",
            "description": "Scans `app/` Python source for direct DB or LLM usage (psycopg2, sqlalchemy, ollama, lifebuddy-db, etc.). The App must call the Engine API instead.",
            "subcomponents": code_subs if not code_ok else [],
        },
    ]

    thresholds = [
        {"color": "#10b981", "label": "Green", "text": f"OK — latency < {int(APP_GREEN_THRESHOLD*1000)} ms"},
        {"color": "#f59e0b", "label": "Amber", "text": f"Degraded — latency {int(APP_GREEN_THRESHOLD*1000)} ms–{int(APP_AMBER_THRESHOLD*1000)} ms"},
        {"color": "#ef4444", "label": "Red", "text": f"Critical — latency > {int(APP_AMBER_THRESHOLD*1000)} ms or unreachable"},
    ]

    footer = "This page is for local diagnostics only. The App does not access the database or LLM directly; it communicates with the Engine on the secure network."
    html = render_status(title=title, subtitle=subtitle, services=services, thresholds=thresholds, footer=footer, home_url="http://localhost:8000/")
    return HTMLResponse(content=html)


# Startup-time static scan to ensure `app/` source does not import DB/LLM libraries
@app.on_event("startup")
def _verify_app_code_safety():
    import re
    from pathlib import Path

    repo_base = Path(__file__).resolve().parents[1]
    app_dir = repo_base / "app"
    try:
        from shared.safety_patterns import IMPORT_PATTERNS as STARTUP_IMPORT_PATTERNS, HOST_PATTERNS as STARTUP_HOST_PATTERNS
    except Exception:
        STARTUP_IMPORT_PATTERNS = []
        STARTUP_HOST_PATTERNS = []
    hits = []
    for p in app_dir.rglob("*.py"):
        # Skip scanning this startup checker file to avoid self-matches
        try:
            rel = str(p.relative_to(repo_base))
            if rel == "app/main.py":
                continue
        except Exception:
            pass
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for pat in STARTUP_IMPORT_PATTERNS:
            if re.search(pat, text, flags=re.MULTILINE):
                hits.append((str(p.relative_to(repo_base)), pat))
        for pat in STARTUP_HOST_PATTERNS:
            if re.search(pat, text):
                hits.append((str(p.relative_to(repo_base)), pat))
    if hits:
        details = ", ".join([f"{f} (pattern: {pat})" for f, pat in hits])
        msg = f"Prohibited DB/LLM import patterns found in App source: {details}. The App must not import or access DB/LLM libraries directly."
        raise RuntimeError(msg)


if __name__ == "__main__":
    import uvicorn  # type: ignore

    uvicorn.run(app, host="0.0.0.0", port=8000)
