"""Minimal Engine for dev: auth demo, db test, and simple internal status."""

import os
import time
import json
import uuid
import socket
import hashlib

import httpx  # type: ignore
try:
    import psycopg2  # type: ignore
    from psycopg2.extras import RealDictCursor
except Exception:
    psycopg2 = None  # type: ignore
    RealDictCursor = None  # type: ignore
from fastapi import FastAPI, Request, HTTPException, Depends, Form, Response
from fastapi.responses import JSONResponse, HTMLResponse
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST  # type: ignore
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError  # type: ignore

# Optional: passlib may not be installed in the editor environment used for static
# analysis. Import defensively via importlib and fall back to None so the module
# can still be linted/loaded; runtime should install `passlib[bcrypt]` in the
# container image. Using importlib avoids some static-analysis import warnings.
try:
    import importlib
    _pl = importlib.import_module("passlib.hash")
    bcrypt = getattr(_pl, "bcrypt", None)
    bcrypt_sha256 = getattr(_pl, "bcrypt_sha256", None)
except Exception:
    bcrypt = None
    bcrypt_sha256 = None

import sys
# Ensure `shared/` package is importable when running inside the container image
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


def _verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")


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
    # Use bcrypt for new password hashes when available; otherwise fall back
    # to SHA-256 (not ideal, but allows the service to run in environments
    # where `passlib` isn't installed). Runtime images should include
    # `passlib[bcrypt]` so bcrypt is preferred.
    # Prefer bcrypt_sha256 which pre-hashes long inputs and avoids bcrypt's
    # 72-byte truncation limitation while keeping bcrypt strength.
    if bcrypt_sha256 is not None:
        try:
            return bcrypt_sha256.hash(password)
        except Exception:
            # Fallback: manually pre-hash with SHA-256 and then bcrypt the hex
            try:
                pre = hashlib.sha256(password.encode("utf-8")).hexdigest()
                if bcrypt is not None:
                    return bcrypt.hash(pre)
            except Exception:
                pass
    if bcrypt is not None:
        try:
            return bcrypt.hash(password)
        except Exception:
            # Fallback to hashing the SHA-256 hex if bcrypt complains about length
            pre = hashlib.sha256(password.encode("utf-8")).hexdigest()
            try:
                return bcrypt.hash(pre)
            except Exception:
                pass
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


from typing import Optional


def _is_legacy_sha256(hash_str: Optional[str]) -> bool:
    # legacy SHA-256 hex digest is 64 hex chars
    if not isinstance(hash_str, str):
        return False
    try:
        hs = hash_str.lower()
    except Exception:
        return False
    return len(hs) == 64 and all(c in "0123456789abcdef" for c in hs)


def _verify_password(password: str, stored_hash: Optional[str]) -> bool:
    # If stored hash is bcrypt, use passlib to verify
    try:
        # Try bcrypt_sha256 first (newer hashes may use this)
        if bcrypt_sha256 is not None and isinstance(stored_hash, str) and stored_hash.startswith("$2"):
            try:
                if bcrypt_sha256.verify(password, stored_hash):
                    return True
            except Exception:
                # Try verifying against a manual prehash if handler fails
                try:
                    pre = hashlib.sha256(password.encode("utf-8")).hexdigest()
                    if bcrypt is not None and bcrypt.verify(pre, stored_hash):
                        return True
                except Exception:
                    pass
        if bcrypt is not None and isinstance(stored_hash, str) and stored_hash.startswith("$2"):
            try:
                return bcrypt.verify(password, stored_hash)
            except Exception:
                # Try verifying with pre-hash
                try:
                    pre = hashlib.sha256(password.encode("utf-8")).hexdigest()
                    return bcrypt.verify(pre, stored_hash)
                except Exception:
                    pass
    except Exception:
        pass
    # Fallback: legacy SHA-256
    if _is_legacy_sha256(stored_hash):
        try:
            return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash
        except Exception:
            return False
    return False


# ----------------------
# Postgres-backed auth helpers
# ----------------------
def _pg_conn():
    # Read DB connection info exclusively from environment variables.
    # Do not fall back to hard-coded defaults to avoid leaking credentials.
    pg_host = os.environ.get("POSTGRES_HOST")
    # Allow a default port if not set in environment (common default 5432)
    pg_port = os.environ.get("POSTGRES_PORT") or "5432"
    pg_db = os.environ.get("POSTGRES_DB")
    pg_user = os.environ.get("POSTGRES_USER")
    pg_pass = os.environ.get("POSTGRES_PASSWORD")
    if not all([pg_host, pg_db, pg_user, pg_pass]):
        raise RuntimeError("Missing required Postgres environment variables: POSTGRES_HOST/POSTGRES_DB/POSTGRES_USER/POSTGRES_PASSWORD")
    return psycopg2.connect(host=pg_host, port=int(pg_port), dbname=pg_db, user=pg_user, password=pg_pass)


def db_get_user_by_username(username: str):
    try:
        conn = _pg_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT user_id, username, email, password_hash FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def db_get_user_by_id(user_id: str):
    try:
        conn = _pg_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT user_id, username, email FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def db_create_user(user_id: str, username: str, email: str, password_hash: str):
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (user_id, username, email, password_hash) VALUES (%s, %s, %s, %s)",
            (user_id, username, email, password_hash),
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False


def db_update_user_password(username: str, new_hash: str):
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s", (new_hash, username))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False


def db_update_user_email(username: str, new_email: str):
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET email = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s", (new_email, username))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception:
        return False


def migrate_users_json_to_db():
    # Backup file then migrate any entries into the DB if possible
    if not os.path.isfile(USERS_FILE):
        return
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except Exception:
        return

    # Backup
    try:
        bak = USERS_FILE + ".bak"
        with open(bak, "w", encoding="utf-8") as bf:
            json.dump(users, bf, indent=2)
    except Exception:
        pass

    for uname, info in users.items():
        uid = info.get("id") or str(uuid.uuid4())
        phash = info.get("password")
        if not phash:
            continue
        # email fallback
        email = info.get("email") or f"{uname}@local"
        # Skip if user already exists in DB
        existing = db_get_user_by_username(uname)
        if existing:
            continue
        db_create_user(uid, uname, email, phash)


def db_get_user_preferences(user_id: str):
    try:
        conn = _pg_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Ensure RLS session context is set for this connection
        cur.execute("SELECT set_config('app.current_user_id', %s, false)", (str(user_id),))
        cur.execute("SELECT user_id, advisor_name_spiritual, advisor_name_action, advisor_name_health, synthesis_matrix, spiritual_mode, spiritual_tone, health_data_ingestion, theme, notifications, updated_at FROM user_preferences WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def db_upsert_user_preferences(user_id: str, theme=None, notifications=None, synthesis_matrix=None):
    try:
        conn = _pg_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Set the RLS session context so policies apply correctly
        cur.execute("SELECT set_config('app.current_user_id', %s, false)", (str(user_id),))
        cur.execute(
            """
            INSERT INTO user_preferences (user_id, theme, notifications, synthesis_matrix, updated_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
              theme = COALESCE(EXCLUDED.theme, user_preferences.theme),
              notifications = COALESCE(EXCLUDED.notifications, user_preferences.notifications),
              synthesis_matrix = COALESCE(EXCLUDED.synthesis_matrix, user_preferences.synthesis_matrix),
              updated_at = CURRENT_TIMESTAMP
            RETURNING user_id, theme, notifications, synthesis_matrix, updated_at
            """,
            (user_id, theme, notifications, json.dumps(synthesis_matrix) if synthesis_matrix is not None else None),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None



@app.post("/api/v1/auth/register")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    # Prefer Postgres-backed users. If DB is unavailable, do NOT fall back
    # to the file-based store — return 503 so auth is disabled until DB is
    # recovered. This prevents logins using stale/backup JSON data.
    phash = _hash_password(password)
    # Try DB
    try:
        existing = db_get_user_by_username(username)
        if existing:
            raise HTTPException(status_code=409, detail="user_exists")
        user_id = str(uuid.uuid4())
        created = db_create_user(user_id, username, email, phash)
        if created:
            return {"user_id": user_id}
        # If DB functions returned but insertion failed, treat as server error
        raise HTTPException(status_code=500, detail="db_error")
    except HTTPException:
        raise
    except Exception as e:
        # Database unavailable — disable auth until DB is healthy
        raise HTTPException(status_code=503, detail="database_unavailable")


@app.post("/api/v1/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # Try DB first. If DB is unavailable, do NOT fall back to file-based auth;
    # instead return 503 so authentication is disabled until DB is recovered.
    try:
        existing = db_get_user_by_username(username)
        if existing:
            stored = existing.get("password_hash")
            if _verify_password(password, stored):
                # If legacy SHA-256, rehash with stronger handler and update DB
                if _is_legacy_sha256(stored):
                    new_hash = _hash_password(password)
                    try:
                        db_update_user_password(username, new_hash)
                    except Exception:
                        pass
                user_id = existing.get("user_id")
                token = jwt.encode({"sub": user_id, "username": username}, JWT_SECRET, algorithm=JWT_ALGORITHM)
                return {"access_token": token, "token_type": "bearer", "user_id": user_id}
            # DB lookup returned but password mismatch
            raise HTTPException(status_code=401, detail="invalid_credentials")
        # User not found in DB
        raise HTTPException(status_code=401, detail="invalid_credentials")
    except HTTPException:
        raise
    except Exception:
        # DB unavailable — disable auth
        raise HTTPException(status_code=503, detail="database_unavailable")


@app.patch('/api/v1/user-preferences')
async def patch_user_preferences(data: dict, payload=Depends(_verify_token)):
    """Upsert user preferences for the current user. Expects a JSON body with optional keys:
    - theme: 'system'|'light'|'dark'
    - notifications: boolean or 'enabled'/'disabled'
    - synthesis_matrix: JSON object
    """
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail='invalid_token')

    theme = data.get('theme') if isinstance(data, dict) else None
    notifications = data.get('notifications') if isinstance(data, dict) else None
    synthesis_matrix = data.get('synthesis_matrix') if isinstance(data, dict) else None

    # Normalize notifications: accept booleans or 'enabled'/'disabled'
    if isinstance(notifications, str):
        if notifications.lower() in ('enabled', 'true', '1'):
            notifications = True
        elif notifications.lower() in ('disabled', 'false', '0'):
            notifications = False
        else:
            raise HTTPException(status_code=422, detail='invalid_notifications')

    # Validate theme if provided
    if theme is not None and theme not in ('system', 'light', 'dark'):
        raise HTTPException(status_code=422, detail='invalid_theme')

    result = db_upsert_user_preferences(user_id, theme=theme, notifications=notifications, synthesis_matrix=synthesis_matrix)
    if result is None:
        raise HTTPException(status_code=500, detail='db_error')
    return result


@app.get('/api/v1/user-preferences')
async def get_user_preferences(payload=Depends(_verify_token)):
    user_id = payload.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail='invalid_token')
    prefs = db_get_user_preferences(user_id)
    if prefs is None:
        # Return sensible defaults
        return {
            'user_id': user_id,
            'theme': 'system',
            'notifications': True,
            'synthesis_matrix': None,
        }
    return prefs


@app.on_event("startup")
def _migrate_users_on_startup():
    try:
        migrate_users_json_to_db()
    except Exception:
        # Migration best-effort only
        pass



@app.get("/api/v1/me")
async def me(payload=Depends(_verify_token)):
    # Fetch full user record from Postgres so we can include email and confirm DB connectivity
    user_id = payload.get("sub")
    try:
        db_user = db_get_user_by_id(user_id)
        if db_user:
            return {"user_id": db_user.get("user_id"), "username": db_user.get("username"), "email": db_user.get("email")}
        # If user not found in DB, fall back to token claims
        return {"user_id": user_id, "username": payload.get("username")}
    except Exception:
        # If DB is unavailable, still return token claims so the App can render something
        return {"user_id": user_id, "username": payload.get("username")}


@app.patch("/api/v1/me")
async def update_me(data: dict, payload=Depends(_verify_token)):
    # Allow updating mutable user attributes such as email
    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="invalid_token")
    email = data.get("email") if isinstance(data, dict) else None
    if email:
        ok = db_update_user_email(username, email)
        if not ok:
            raise HTTPException(status_code=500, detail="db_error")
        return {"status": "ok", "email": email}
    raise HTTPException(status_code=400, detail="nothing_to_update")


@app.post("/api/v1/me/password")
async def change_password(data: dict, payload=Depends(_verify_token)):
    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="invalid_token")
    current = data.get("current_password") if isinstance(data, dict) else None
    new = data.get("new_password") if isinstance(data, dict) else None
    if not current or not new:
        raise HTTPException(status_code=400, detail="missing_fields")
    # Verify current password
    existing = db_get_user_by_username(username)
    if not existing:
        raise HTTPException(status_code=404, detail="user_not_found")
    stored = existing.get("password_hash")
    if not _verify_password(current, stored):
        raise HTTPException(status_code=401, detail="invalid_current_password")
    # Hash new password and update
    new_hash = _hash_password(new)
    ok = db_update_user_password(username, new_hash)
    if not ok:
        raise HTTPException(status_code=500, detail="db_error")
    return {"status": "ok"}


@app.get("/api/v1/db_test")
async def db_test():
    try:
        conn = _pg_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "error", "detail": str(e)})


GREEN_THRESHOLD = 0.20  # seconds
AMBER_THRESHOLD = 1.50  # seconds


from typing import Optional, Tuple


def _socket_check(host: str, port: Optional[int], timeout: float = 2.0) -> Tuple[bool, str, Optional[float]]:
    start = time.time()
    if port is None:
        return False, "missing_port", None
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
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

    pg_host = os.environ.get("POSTGRES_HOST")
    pg_port_env = os.environ.get("POSTGRES_PORT")
    if not pg_host or not pg_port_env:
        pg_ok = False
        pg_detail = "missing POSTGRES_HOST/POSTGRES_PORT env vars"
        pg_lat = None
    else:
        try:
            pg_port = int(pg_port_env)
        except Exception:
            pg_ok = False
            pg_detail = "invalid POSTGRES_PORT"
            pg_lat = None
            pg_port = None
    redis_host = os.environ.get("REDIS_HOST", "message-broker")
    redis_port = int(os.environ.get("REDIS_PORT", 6379))

    if 'pg_port' in locals() and pg_host:
        pg_ok, pg_detail, pg_lat = _socket_check(pg_host, pg_port)
    else:
        pg_ok = False
        # pg_detail and pg_lat already set above
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

    if callable(render_landing):
        html = render_landing(title=title, subtitle=subtitle, status_url=status_url, app_api_calls=app_api_calls, endpoints=endpoints)
        return HTMLResponse(content=html)
    # Fallback: render a minimal landing using render_status if available
    try:
        services = []
        thresholds = []
        footer = "Engine landing (minimal)"
        html = render_status(title=title, subtitle=subtitle, services=services, thresholds=thresholds, footer=footer, home_url="http://localhost:8001/")
        return HTMLResponse(content=html)
    except Exception:
        # Last-resort simple HTML
        simple = f"<html><body><h1>{title}</h1><p>{subtitle}</p></body></html>"
        return HTMLResponse(content=simple)


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint for Engine health and Ollama status."""
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
