"""Minimal Engine for dev: auth demo, db test, and simple internal status."""

import os
import time
import json
import uuid
import socket
import hashlib

import httpx
import psycopg2
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Response
from fastapi.responses import JSONResponse, HTMLResponse
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

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

        html = f"""
<html><head><title>Internal Status</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 18px }}
        .card {{ background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06) }}
        .service {{ margin:8px 0 }}
    </style>
</head><body>
    <div class="card">
        <h2>Internal Status — {overall.upper()}</h2>
        <div class="service">{_badge('Postgres', pg_level)}Postgres: {('ok' if pg_ok else 'error')} — {pg_detail}</div>
        <div class="service">{_badge('Redis', redis_level)}Redis: {('ok' if redis_ok else 'error')} — {redis_detail}</div>
        <div class="service">{_badge('Ollama', ollama_level)}Ollama: {('ok' if ollama_ok else 'error')} — {ollama_detail}</div>
        <div class="service">{_badge('App Probe', app_level)}App probe: {('reachable' if app_probe.get('reachable') else 'unreachable')}</div>

        <div style='margin-top:12px'>
            <strong>Meaning &amp; Thresholds</strong>
            <ul>
                <li><span style='color:#10b981;font-weight:700'>Green</span> = OK — latency &lt; {int(GREEN_THRESHOLD*1000)} ms</li>
                <li><span style='color:#f59e0b;font-weight:700'>Amber</span> = Degraded — latency {int(GREEN_THRESHOLD*1000)} ms–{int(AMBER_THRESHOLD*1000)} ms</li>
                <li><span style='color:#ef4444;font-weight:700'>Red</span> = Critical — latency &gt; {int(AMBER_THRESHOLD*1000)} ms or unreachable</li>
            </ul>
        </div>
    </div>
</body></html>
"""

    return HTMLResponse(content=html)


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint for Engine health and Ollama status."""
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
