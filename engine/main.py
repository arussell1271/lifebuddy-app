import sys
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import json
import os
import hashlib
import uuid
import socket
from fastapi import FastAPI, Request, HTTPException, Depends, Form
import time
import httpx
from pathlib import Path

app = FastAPI(title="LifeBuddy Engine")

USERS_FILE = os.path.join(os.path.dirname(__file__), "data", "users.json")
os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
import re
import html
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

security = HTTPBearer()
 

def _load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

import os
import sys
import time
import json
import uuid
import socket
import hashlib
import re
import html
from pathlib import Path
from datetime import datetime

import httpx
import psycopg2
from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

app = FastAPI(title="LifeBuddy Engine")

USERS_FILE = os.path.join(os.path.dirname(__file__), "data", "users.json")
os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")

security = HTTPBearer()


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


@app.get("/", tags=["health"])
def read_root():
    html_body = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title>LifeBuddy Cognitive Engine</title>
    <style>
        body{font-family:Arial,Helvetica,sans-serif;margin:24px;background:#f7fafc}
        .container{max-width:900px;background:#fff;padding:24px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06)}
        .endpoint{background:#f1f5f9;padding:12px;border-radius:6px;margin:8px 0}
        .method{display:inline-block;padding:4px 8px;border-radius:4px;font-weight:600;margin-right:8px}
        .get{background:#61affe;color:#fff}
        .post{background:#49cc90;color:#fff}
        pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px}
        .status{margin-top:12px}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 LifeBuddy Cognitive Engine</h1>
        <p>This internal service handles database and LLM operations. Access to the internal status page is restricted to localhost.</p>

        <h2>Database / Internal Endpoints</h2>
        <div class="endpoint"><span class="method post">POST</span>/api/v1/auth/register — register a new user (form)</div>
        <div class="endpoint"><span class="method post">POST</span>/api/v1/auth/login — login, returns JWT (form)</div>
        <div class="endpoint"><span class="method get">GET</span>/api/v1/me — introspect token (Authorization: Bearer ...)</div>
        <div class="endpoint"><span class="method get">GET</span>/api/v1/db_test — quick Postgres connectivity test</div>
        <div class="endpoint"><span class="method get">GET</span>/internal/status — (LOCALHOST ONLY) traffic-light status for DB, Redis, LLM, and app integrity</div>

        <h3>Usage examples</h3>
        <pre># Register (form)
POST /api/v1/auth/register
Content-Type: application/x-www-form-urlencoded
username=alice&password=Secret123!

# Login (form)
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
username=alice&password=Secret123!
        </pre>

        <div class="status">See <a href="/internal/status">/internal/status</a> for live service health and integrity checks.</div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_body)


@app.post("/api/v1/auth/register", tags=["auth"])
async def register(username: str = Form(...), password: str = Form(...)):
    users = _load_users()
    if username in users:
        raise HTTPException(status_code=409, detail="user_exists")
    user_id = str(uuid.uuid4())
    users[username] = {"id": user_id, "password": _hash_password(password)}
    _save_users(users)
    return {"user_id": user_id}


@app.post("/api/v1/auth/login", tags=["auth"])
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


@app.get("/api/v1/me", tags=["auth"])
async def me(payload=Depends(_verify_token)):
    username = payload.get("username")
    user_id = payload.get("sub")
    return {"user_id": user_id, "username": username, "message": f"Welcome, {username}!"}


@app.get("/api/v1/db_test", tags=["db"])
async def db_test():
    """Attempt to connect to Postgres using environment variables and report status."""
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
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable", "detail": str(e)})


def _socket_check(host: str, port: int, timeout: float = 2.0) -> (bool, str):
    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=timeout):
            latency = time.time() - start
            return True, f"ok (latency={latency:.2f}s)"
    except Exception as e:
        return False, str(e)


def _scan_app_for_db_usage() -> dict:
    # 1) If operator provided an explicit path via env var, prefer it
    env_path = os.environ.get("APP_SOURCE_PATH")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))

    # 2) Default: path relative to repo layout (when app/ is copied into image)
    candidates.append(Path(__file__).resolve().parents[1] / "app")

    # 3) Common host mount roots (Docker Desktop / WSL mount conventions)
    common_roots = ["/host_mnt", "/mnt/host", "/mnt/c", "/c", "/host"]
    for root_base in common_roots:
        candidates.append(Path(root_base))

    findings: list[dict] = []
    patterns = ["psycopg2", "psycopg", "sqlalchemy", "pgvector", "ollama", "openai"]

    for cand in candidates:
        try:
            if not cand.exists():
                continue
        except Exception:
            continue

        search_roots = []
        if cand.is_dir():
            potential = cand / "app"
            if potential.exists() and potential.is_dir():
                search_roots.append(potential)
            if (cand / "main.py").exists() or (cand / "templates").exists() or (cand / "static").exists():
                search_roots.append(cand)
            for p in cand.rglob("app"):
                if p.is_dir():
                    search_roots.append(p)

        for root in search_roots:
            for p in root.rglob("*.py"):
                try:
                    text = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                for pat in patterns:
                    if pat in text:
                        findings.append({"file": str(p.relative_to(Path(__file__).resolve().parents[1])), "pattern": pat})
            if findings:
                return {"scanned": True, "root": str(root), "findings": findings}

    app_probe = {"reachable": False}
    try:
        for url in ("http://lifebuddy-app:8000/", "http://localhost:8000/"):
            try:
                with httpx.Client(timeout=2.0) as client:
                    r = client.get(url)
                    app_probe = {"reachable": True, "url": url, "status_code": r.status_code, "body_snippet": r.text[:800]}
                    break
            except Exception:
                continue
    except Exception:
        app_probe = {"reachable": False}

    return {"scanned": False, "reason": "app source not found in inspected paths", "probe": app_probe}


def _parse_latency(detail: object) -> float | None:
    if not isinstance(detail, str):
        return None
    m = re.search(r"latency=([0-9]*\.?[0-9]+)s", detail)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


@app.get("/internal/status", response_class=HTMLResponse, tags=["internal"])
async def internal_status(request: Request):
    client_host = request.client.host if request.client else None
    allowed = {"127.0.0.1", "::1", "localhost"}
    if client_host not in allowed and not (isinstance(client_host, str) and client_host.startswith("172.")) and client_host != "0.0.0.0":
        return HTMLResponse(content="<h3>403 Forbidden</h3><p>Access to /internal/status is restricted to localhost.</p>", status_code=403)

    pg_host = os.environ.get("POSTGRES_HOST", "lifebuddy-db")
    pg_port = int(os.environ.get("POSTGRES_PORT", "5432"))
    pg_ok, pg_detail = _socket_check(pg_host, pg_port)

    redis_host = os.environ.get("REDIS_HOST", os.environ.get("MESSAGE_BROKER_HOST", "message-broker"))
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    redis_ok, redis_detail = _socket_check(redis_host, redis_port)

    ollama_base = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{ollama_base}/api/health", follow_redirects=True)
            ollama_ok = resp.status_code == 200
            ollama_detail = f"{resp.status_code} {resp.text[:200]}"
    except Exception as e:
        ollama_ok = False
        ollama_detail = str(e)

    scan = _scan_app_for_db_usage()
    app_ok = scan.get("scanned") and len(scan.get("findings", [])) == 0

    GREEN_THRESHOLD = 0.20
    AMBER_THRESHOLD = 1.50

    overall = "green"
    reasons: list[str] = []

    if not pg_ok:
        overall = "red"
        reasons.append(f"Postgres unreachable: {pg_detail}")
    if not redis_ok:
        overall = "red"
        reasons.append(f"Redis unreachable: {redis_detail}")
    if not ollama_ok:
        overall = "red"
        reasons.append(f"LLM unreachable: {ollama_detail}")

    if not app_ok:
        overall = "red"
        reasons.append("App code contains direct DB/LLM client references")

    pg_lat = _parse_latency(pg_detail)
    redis_lat = _parse_latency(redis_detail)
    for name, lat in (("Postgres", pg_lat), ("Redis", redis_lat)):
        if lat is None:
            continue
        if lat > AMBER_THRESHOLD:
            overall = "red"
            reasons.append(f"{name} latency high: {lat:.2f}s")
        elif lat > GREEN_THRESHOLD and overall != "red":
            overall = "amber"
            reasons.append(f"{name} latency degraded: {lat:.2f}s")

    color_map = {"green": "#10b981", "amber": "#f59e0b", "red": "#ef4444"}
    overall_color = color_map.get(overall, "#6b7280")

    def _service_color(ok: bool, detail: object) -> str:
        if not ok:
            return color_map["red"]
        lat = _parse_latency(detail)
        if lat is None:
            return color_map["green"]
        if lat > AMBER_THRESHOLD:
            return color_map["red"]
        if lat > GREEN_THRESHOLD:
            return color_map["amber"]
        return color_map["green"]

    pg_color = _service_color(pg_ok, pg_detail)
    redis_color = _service_color(redis_ok, redis_detail)
    ollama_color = _service_color(ollama_ok, ollama_detail) if isinstance(ollama_detail, str) else (color_map["green"] if ollama_ok else color_map["red"])
    app_color = color_map["green"] if app_ok else color_map["red"]

    app_probe_summary = ""
    app_probe_snippet_escaped = ""
    if scan.get("scanned"):
        app_probe_summary = f"App source scanned at: {scan.get('root')} (findings={len(scan.get('findings', []))})"
        if scan.get("findings"):
            app_probe_snippet_escaped = html.escape(json.dumps(scan.get("findings"), indent=2))
    else:
        probe = scan.get("probe") or {}
        if probe.get("reachable"):
            app_probe_summary = f"App HTTP probe reachable: {probe.get('url')} (status={probe.get('status_code')})"
            app_probe_snippet_escaped = html.escape(probe.get("body_snippet", ""))
        else:
            app_probe_summary = scan.get("reason", "app not available")

    notes_html = ""
    if reasons:
        notes_html = "<li>Notes:<ul>" + "".join(f"<li>{r}</li>" for r in reasons) + "</ul></li>"

    # Per-test evaluations
    pg_lat = _parse_latency(pg_detail)
    redis_lat = _parse_latency(redis_detail)

    pg_reachable = pg_ok
    pg_latency_status = "unknown"
    if isinstance(pg_lat, float):
        if pg_lat > AMBER_THRESHOLD:
            pg_latency_status = "high"
        elif pg_lat > GREEN_THRESHOLD:
            pg_latency_status = "degraded"
        else:
            pg_latency_status = "good"

    redis_reachable = redis_ok
    redis_latency_status = "unknown"
    if isinstance(redis_lat, float):
        if redis_lat > AMBER_THRESHOLD:
            redis_latency_status = "high"
        elif redis_lat > GREEN_THRESHOLD:
            redis_latency_status = "degraded"
        else:
            redis_latency_status = "good"

    ollama_reachable = ollama_ok

    app_probe_ok = bool(scan.get("probe") and scan.get("probe").get("reachable"))
    app_source_scanned = bool(scan.get("scanned"))
    app_source_ok = app_source_scanned and len(scan.get("findings", [])) == 0

    def badge(text: str, passed: bool) -> str:
        color = "#10b981" if passed else "#ef4444"
        return f"<span style='background:{color};color:#fff;padding:4px 8px;border-radius:4px;font-weight:700;margin-right:8px'>{text}</span>"

    body = f"""<html><head><title>Internal Status</title><style>
            body{{font-family:Arial;margin:18px}}
            .card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06)}}
            .section{{margin-bottom:18px}}
            .dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle}}
            pre{{background:#f1f5f9;color:#0f172a;padding:12px;border-radius:6px}}
            ul.tests{{list-style:none;padding-left:0}}
            ul.tests li{{margin:6px 0}}
        </style></head><body>
        <div class='card'>
            <h2>Internal Status — Overall: <span style='color:{overall_color}'>{overall.upper()}</span></h2>

            <div class='section'>
                <h3>Database (Postgres)</h3>
                <ul class='tests'>
                    <li>{badge('Reachable', pg_reachable)}Postgres host: {pg_host}:{pg_port} — {pg_detail}</li>
                    <li>{badge('Latency OK', pg_reachable and (pg_lat is None or pg_lat <= AMBER_THRESHOLD))}Latency: {pg_lat if pg_lat is not None else 'n/a'}</li>
                </ul>
            </div>

            <div class='section'>
                <h3>Message Broker (Redis)</h3>
                <ul class='tests'>
                    <li>{badge('Reachable', redis_reachable)}Redis host: {redis_host}:{redis_port} — {redis_detail}</li>
                    <li>{badge('Latency OK', redis_reachable and (redis_lat is None or redis_lat <= AMBER_THRESHOLD))}Latency: {redis_lat if redis_lat is not None else 'n/a'}</li>
                </ul>
            </div>

            <div class='section'>
                <h3>LLM (Ollama)</h3>
                <ul class='tests'>
                    <li>{badge('Healthy', ollama_reachable)}Status: {ollama_detail}</li>
                </ul>
            </div>

            <div class='section'>
                <h3>App</h3>
                <ul class='tests'>
                    <li>{badge('HTTP Probe', app_probe_ok)}{app_probe_summary}</li>
                    <li>{badge('Source Scan', app_source_scanned and app_source_ok)}Source scanned: {app_source_scanned} — findings: {len(scan.get('findings', [])) if scan.get('scanned') else 'n/a'}</li>
                </ul>
            </div>

            {notes_html}

            {f"<div style='margin-top:12px'><strong>App probe snippet</strong><pre style='white-space:pre-wrap'>{app_probe_snippet_escaped}</pre></div>" if app_probe_snippet_escaped else ''}

            <div style='margin-top:12px'>
                <strong>Meaning &amp; Thresholds</strong>
                <ul>
                    <li><span style='color:#10b981;font-weight:700'>Green</span> = OK — latency &lt; 200 ms</li>
                    <li><span style='color:#f59e0b;font-weight:700'>Amber</span> = Degraded — latency 200 ms–1500 ms (review)</li>
                    <li><span style='color:#ef4444;font-weight:700'>Red</span> = Critical — latency &gt; 1500 ms or unreachable / policy violation</li>
                </ul>
            </div>
        </div>
        </body></html>"""
    return HTMLResponse(content=body)
            .dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle}}
            .service{{margin:8px 0}}
            pre{{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px}}
        body = f"""<html><head><title>Internal Status</title><style>
                body{{font-family:Arial;margin:18px}}
                .card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.06)}}
                .section{{margin-bottom:18px}}
                .dot{{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle}}
                pre{{background:#f1f5f9;color:#0f172a;padding:12px;border-radius:6px}}
                ul.tests{{list-style:none;padding-left:0}}
                ul.tests li{{margin:6px 0}}
            </style></head><body>
            <div class='card'>
                <h2>Internal Status — Overall: <span style='color:{overall_color}'>{overall.upper()}</span></h2>

                <div class='section'>
                    <h3>Database (Postgres)</h3>
                    <ul class='tests'>
                        <li>{badge('Reachable', pg_reachable)}Postgres host: {pg_host}:{pg_port} — {pg_detail}</li>
                        <li>{badge('Latency OK', pg_reachable and (pg_lat is None or pg_lat <= AMBER_THRESHOLD))}Latency: {pg_lat if pg_lat is not None else 'n/a'}</li>
                    </ul>
                </div>

                <div class='section'>
                    <h3>Message Broker (Redis)</h3>
                    <ul class='tests'>
                        <li>{badge('Reachable', redis_reachable)}Redis host: {redis_host}:{redis_port} — {redis_detail}</li>
                        <li>{badge('Latency OK', redis_reachable and (redis_lat is None or redis_lat <= AMBER_THRESHOLD))}Latency: {redis_lat if redis_lat is not None else 'n/a'}</li>
                    </ul>
                </div>

                <div class='section'>
                    <h3>LLM (Ollama)</h3>
                    <ul class='tests'>
                        <li>{badge('Healthy', ollama_reachable)}Status: {ollama_detail}</li>
                    </ul>
                </div>

                <div class='section'>
                    <h3>App</h3>
                    <ul class='tests'>
                        <li>{badge('HTTP Probe', app_probe_ok)}{app_probe_summary}</li>
                        <li>{badge('Source Scan', app_source_scanned and app_source_ok)}Source scanned: {app_source_scanned} — findings: {len(scan.get('findings', [])) if scan.get('scanned') else 'n/a'}</li>
                    </ul>
                </div>

                {notes_html}

                {f"<div style='margin-top:12px'><strong>App probe snippet</strong><pre style='white-space:pre-wrap'>{app_probe_snippet_escaped}</pre></div>" if app_probe_snippet_escaped else ''}

                <div style='margin-top:12px'>
                    <strong>Meaning &amp; Thresholds</strong>
                    <ul>
                        <li><span style='color:#10b981;font-weight:700'>Green</span> = OK — latency &lt; 200 ms</li>
                        <li><span style='color:#f59e0b;font-weight:700'>Amber</span> = Degraded — latency 200 ms–1500 ms (review)</li>
                        <li><span style='color:#ef4444;font-weight:700'>Red</span> = Critical — latency &gt; 1500 ms or unreachable / policy violation</li>
                    </ul>
                </div>
            </div>
            </body></html>"""
    uvicorn.run(app, host="0.0.0.0", port=8001)
