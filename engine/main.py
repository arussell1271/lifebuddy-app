"""Minimal Engine for dev: auth demo, db test, and simple internal status."""

import os
import time
import json
import uuid
import socket
import hashlib

import httpx  # type: ignore
import psycopg2  # type: ignore
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Response
from fastapi.responses import JSONResponse, HTMLResponse
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError  # type: ignore
import os
import sys
# Ensure `shared/` package is importable when running inside the container image
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def _load_shared_renderer():
    import importlib.util
    from pathlib import Path
    base = Path(__file__).resolve().parents[1]
    renderer_file = base / "shared" / "render_status.py"
    spec = importlib.util.spec_from_file_location("shared.render_status", str(renderer_file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

_renderer_module = _load_shared_renderer()
render_status = _renderer_module.render_status
# optional landing renderer (may not exist in older shared modules)
render_landing = getattr(_renderer_module, "render_landing", None)

app = FastAPI(title="LifeBuddy Engine")

USERS_FILE = os.path.join(os.path.dirname(__file__), "data", "users.json")
os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

security = HTTPBearer()

# Prometheus metrics registry and gauges
registry = CollectorRegistry()
ollama_up = Gauge("ollama_up", "Ollama up (1=healthy, 0=unhealthy)", registry=registry)
ollama_status_code = Gauge("ollama_status_code", "HTTP status code from Ollama health", registry=registry)
ollama_response_time_ms = Gauge("ollama_response_time_ms", "Ollama HTTP health response time in milliseconds", registry=registry)


def _load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@app.post("/api/v1/auth/register")
async def register(username: str = Form(...), password: str = Form(...)):
    users = _load_users()
    if username in users:
        raise HTTPException(status_code=409, detail="user_exists")
    user_id = str(uuid.uuid4())
    users[username] = {"id": user_id, "password": _hash_password(password)}
    _save_users(users)
    return {"user_id": user_id}


@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    users = _load_users()
    if username not in users or users[username]["password"] != _hash_password(password):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    user_id = users[username]["id"]
    token = jwt.encode({"sub": user_id, "username": username}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user_id": user_id}


def _verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")


@app.get("/api/v1/me")
async def me(payload=Depends(_verify_token)):
    return {"user_id": payload.get("sub"), "username": payload.get("username")}


@app.get("/api/v1/db_test")
async def db_test():
    pg_host = os.environ.get("POSTGRES_HOST", "lifebuddy-db")
    pg_port = os.environ.get("POSTGRES_PORT", "5432")
    pg_db = os.environ.get("POSTGRES_DB", "lifebuddy_dev_db")
    pg_user = os.environ.get("POSTGRES_USER", "admin")
    pg_pass = os.environ.get("POSTGRES_PASSWORD", "admin")
    try:
        conn = psycopg2.connect(host=pg_host, port=pg_port, dbname=pg_db, user=pg_user, password=pg_pass, connect_timeout=3)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


GREEN_THRESHOLD = 0.20  # seconds
AMBER_THRESHOLD = 1.50  # seconds


def _socket_check(host: str, port: int, timeout: float = 2.0):
    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            latency = time.time() - start
            return True, f"ok (latency={latency:.2f}s)", latency
    except Exception as e:
        return False, str(e), None


def _severity_from_latency(lat):
    if lat is None:
        return "red"
    if lat < GREEN_THRESHOLD:
        return "green"
    if lat <= AMBER_THRESHOLD:
        return "amber"
    return "red"


def _badge(label: str, level: str) -> str:
    colors = {"green": "#10b981", "amber": "#f59e0b", "red": "#ef4444"}
    color = colors.get(level, "#6b7280")
    return f"<strong style='color:{color};margin-right:6px'>{label}</strong>"


@app.get("/internal/status")
async def internal_status(request: Request):
    client = request.client.host if request.client else None
    if client not in ("127.0.0.1", "::1") and not (isinstance(client, str) and client.startswith("172.")):
        return HTMLResponse(content="403 Forbidden", status_code=403)

    pg_host = os.environ.get("POSTGRES_HOST", "lifebuddy-db")
    pg_port = int(os.environ.get("POSTGRES_PORT", 5432))
    redis_host = os.environ.get("REDIS_HOST", "message-broker")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))

    pg_ok, pg_detail, pg_lat = _socket_check(pg_host, pg_port)
    redis_ok, redis_detail, redis_lat = _socket_check(redis_host, redis_port)

    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
    resp_time_ms = None
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            start = time.time()
            r = await client.get(f"{ollama_base}/api/health")
            resp_time_ms = (time.time() - start) * 1000.0
            status = r.status_code
            ollama_detail = f"{status}"
            # Update Prometheus metrics
            try:
                ollama_response_time_ms.set(resp_time_ms)
                ollama_status_code.set(status)
                ollama_up.set(1 if status == 200 else 0)
            except Exception:
                pass
            # Treat 200 as healthy (green). Treat 4xx as reachable but endpoint missing (amber).
            if status == 200:
                ollama_ok = True
                ollama_level = "green"
            elif 400 <= status < 500:
                ollama_ok = False
                ollama_level = "amber"
            else:
                ollama_ok = False
                ollama_level = "red"
    except Exception as e:
        ollama_ok = False
        ollama_detail = str(e)
        ollama_level = "red"
        try:
            ollama_response_time_ms.set(0)
            ollama_status_code.set(0)
            ollama_up.set(0)
        except Exception:
            pass

    # app HTTP probe (best-effort)
    app_probe = {"reachable": False}
    try:
        with httpx.Client(timeout=2.0) as c:
            r = c.get("http://lifebuddy-app:8000/")
            app_probe = {"reachable": True, "status_code": r.status_code}
    except Exception:
        app_probe = {"reachable": False}

    # determine per-service severities
    pg_level = "green" if pg_ok and (pg_lat is not None and pg_lat < GREEN_THRESHOLD) else _severity_from_latency(pg_lat)
    redis_level = "green" if redis_ok and (redis_lat is not None and redis_lat < GREEN_THRESHOLD) else _severity_from_latency(redis_lat)
    app_level = "green" if app_probe.get("reachable") else "red"

    # overall: red if any red, else amber if any amber, else green
    overall = "green"
    if any(l == "red" for l in (pg_level, redis_level, ollama_level, app_level)):
        overall = "red"
    elif any(l == "amber" for l in (pg_level, redis_level, ollama_level, app_level)):
        overall = "amber"

        # Use shared renderer
        title = f"Engine Internal Status — {overall.upper()}"
        subtitle = "Service-level health checks for the Engine and its dependencies."

        def _fmt(lat: float | None) -> str:
            return f"{lat*1000:.2f} ms" if isinstance(lat, (int, float)) else "n/a"

        label_map = {"green": "OK", "amber": "Degraded", "red": "Critical"}

        services = [
                {
                    "status_class": pg_level,
                    "status_label": label_map.get(pg_level, pg_level.upper()),
                    "component": "Postgres",
                    "detail": f"{('ok' if pg_ok else 'error')} — latency: {_fmt(pg_lat)}",
                    "description": "Primary Postgres database used to persist application data; accessed only by the Engine under RLS enforcement.",
                },
                {
                    "status_class": redis_level,
                    "status_label": label_map.get(redis_level, redis_level.upper()),
                    "component": "Redis",
                    "detail": f"{('ok' if redis_ok else 'error')} — latency: {_fmt(redis_lat)}",
                    "description": "Redis message-broker used for async job queues and short-lived caching (message-broker service).",
                },
                {
                    "status_class": ollama_level,
                    "status_label": label_map.get(ollama_level, ollama_level.upper()),
                    "component": "Ollama",
                    "detail": f"{('ok' if ollama_ok else 'error')} — latency: {_fmt(resp_time_ms)}",
                    "description": "Ollama LLM service hosting models used by the Engine for synthesis and analysis (default: ollama:11434).",
                },
                {
                    "status_class": app_level,
                    "status_label": label_map.get(app_level, app_level.upper()),
                    "component": "App Probe",
                    "detail": f"{('reachable' if app_probe.get('reachable') else 'unreachable')}",
                    "description": "HTTP probe of the public App service to verify the UI/API gateway is reachable from the Engine's network.",
                },
            ]
        thresholds = [
            {"color": "#10b981", "label": "Green", "text": f"OK — latency < {int(GREEN_THRESHOLD*1000)} ms"},
            {"color": "#f59e0b", "label": "Amber", "text": f"Degraded — latency {int(GREEN_THRESHOLD*1000)} ms–{int(AMBER_THRESHOLD*1000)} ms"},
            {"color": "#ef4444", "label": "Red", "text": f"Critical — latency > {int(AMBER_THRESHOLD*1000)} ms or unreachable"},
        ]
        footer = "This page is internal to the Engine. The Engine has exclusive access to DB and LLM resources on the secure network."
        html = render_status(title=title, subtitle=subtitle, services=services, thresholds=thresholds, footer=footer, home_url="http://localhost:8001/")
        return HTMLResponse(content=html)


@app.get("/", response_class=HTMLResponse)
async def root_landing():
    """Engine landing page: link to internal status and list App routes."""
    title = "Life Buddy Cognitive Engine"
    subtitle = "Internal service — Database and LLM access only"
    status_url = "/internal/status"
    # App routes to show (hosted on App service)
    app_api_calls = [
        {"path": "/", "url": "http://localhost:8000/", "desc": "App landing"},
        {"path": "/login", "url": "http://localhost:8000/login", "desc": "Login page"},
        {"path": "/register", "url": "http://localhost:8000/register", "desc": "Register page"},
        {"path": "/dashboard", "url": "http://localhost:8000/dashboard", "desc": "User dashboard"},
        {"path": "/health", "url": "http://localhost:8000/health", "desc": "App health check"},
        {"path": "/internal/status", "url": "http://localhost:8000/internal/status", "desc": "App internal status page"},
    ]
    # Extract OpenAPI paths and convert to a simple endpoint list
    try:
        spec = app.openapi()
        paths = spec.get("paths", {}) if isinstance(spec, dict) else {}
        endpoints = []
        for path, methods in sorted(paths.items()):
            for m, info in methods.items():
                endpoints.append({
                    "path": path,
                    "method": m.upper(),
                    "summary": info.get("summary") if isinstance(info, dict) else None,
                    "description": info.get("description") if isinstance(info, dict) else None,
                })
    except Exception:
        endpoints = []

    html = render_landing(title=title, subtitle=subtitle, status_url=status_url, app_api_calls=app_api_calls, endpoints=endpoints)
    return HTMLResponse(content=html)


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint for Engine health and Ollama status."""
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
