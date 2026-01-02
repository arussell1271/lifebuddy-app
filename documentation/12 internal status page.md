# Internal Status Page

Purpose
- A local-only engine endpoint that provides a traffic-light view (Green/Amber/Red) of core services and code integrity checks.

Location
- Engine endpoint: `GET /internal/status` (accessible from localhost only)

- App endpoint: `GET /internal/status` on the App service provides a lighter-weight, App-focused health page (checks Engine reachability, templates/static presence, and shows the same traffic-light colors). This page is intended for UI/service owners and does not run the App source scan.

App Internal Status (App-facing)
- Location: `GET /internal/status` on the App service (App port 8000).
- Purpose: a lightweight, UI-focused traffic-light view for application owners. It verifies that the App can reach the Engine, that local template and static assets are present, and surface the same Green/Amber/Red guidance used by the Engine page.

Meaning of lights (App page)
- Green: App can successfully reach the Engine (`/internal/status` returned HTTP 200), templates and static directories are present, and measured latencies are under the Green threshold (default 200 ms).
- Amber: The App can reach the Engine but one or more latencies are between 200 ms and 1500 ms, or there are benign warnings (e.g., slow filesystem reads). No immediate incident required but review performance and logs.
- Red: The App cannot reach the Engine (timeout / non-200 response) or required local assets (templates/static) are missing. Treat as an incident for the App owner and remediate (check container logs, restart, or restore missing assets).

Operator guidance (App page)
- Use the App Internal Status for quick verification before escalating an Engine or infra incident; it helps determine whether failures are in the UI layer (missing templates/static) or in Engine reachability.
- If the App reports Red because it cannot reach the Engine, follow the Engine troubleshooting steps in this document (DB/Redis/Ollama checks) — the App page will show Engine status code and latency.

Note: The App internal status intentionally does not run the App source scan for DB/LLM imports. The Engine page remains the authoritative check for policy violations (App importing DB/LLM clients).

What it checks
- Postgres connectivity (socket check to `POSTGRES_HOST:POSTGRES_PORT`).
- Redis / message-broker connectivity (socket check to `MESSAGE_BROKER_HOST:6379`).
- Ollama LLM availability (HTTP GET to `OLLAMA_BASE_URL/api/health`).
- App code scan: searches the `app/` folder for direct DB client imports or direct LLM client usage patterns (e.g. `psycopg2`, `sqlalchemy`, `ollama`, `openai`).

Traffic-light definitions
- Green: All core services reachable and no suspicious imports in `app/`.
- Amber: All core services reachable but one or more warnings detected (e.g., higher-than-normal latency, or benign references that should be reviewed).
- Red: Any critical service unreachable, or the `app/` code contains direct DB/LLM client imports (policy violation), or explicit failures.

Latency thresholds and guidance
- **Green (OK)**: End-to-end socket/HTTP latency for a core service is consistently under 200 ms (0.20s). No manual action required beyond normal monitoring.
- **Amber (Degraded — review required)**: Latency is between 200 ms and 1500 ms (0.20s — 1.5s) or intermittent spikes are observed. Operator actions:
  - Check recent host/container CPU, memory, and I/O metrics for the affected service.
  - Inspect the last 5–10 log entries for errors, retries, or GC pauses.
  - If the service is a remote dependency (cloud DB, managed Redis), verify network path, security groups, and throughput limits.
  - Consider temporarily increasing monitoring cadence and enabling alerting if sustained for >5 minutes.
- **Red (Critical)**: Latency consistently above 1500 ms (1.5s) or the service is unreachable (connection refused / timeout / HTTP 5xx). Operator actions:
  - Treat as an incident: triage immediately, escalate to on-call if available.
  - Review container/service logs, restart the affected service if safe, and check resource exhaustion (CPU, memory, disk).
  - If the service is externally hosted, contact the provider and verify outage status.

Notes on thresholds
- These thresholds are conservative guidelines for the dev environment. Production SLAs may be stricter — tune thresholds per environment and metric baseline.
- The `internal/status` page uses simple socket and HTTP checks; for deeper diagnostics integrate with APM traces or synthetic transaction monitoring.

Engine Internal Status (Engine-facing)
- Location: `GET /internal/status` on the Engine service (Engine port 8001). This endpoint is restricted to localhost / Docker-internal addresses.
- Purpose: a comprehensive traffic-light view for operators and Engine owners. It verifies connectivity to core infrastructure (Postgres, Redis), the LLM service (Ollama), and performs a safety scan of the `app/` source for disallowed imports (e.g., `psycopg2`, `sqlalchemy`, `ollama`, `openai`).

What it checks (Engine)
- Postgres connectivity: socket check to `POSTGRES_HOST:POSTGRES_PORT` and a lightweight `SELECT 1` database probe.
- Redis / message-broker connectivity: socket check to `REDIS_HOST:REDIS_PORT`.
- Ollama LLM availability: HTTP GET to `OLLAMA_BASE_URL/api/health` (interprets non-200 as unhealthy).
- App source scan: searches the `app/` folder for direct DB or LLM client imports which would violate the service separation policy.

Traffic-light definitions (Engine)
- Green: All core services reachable, measured latencies under the Green threshold (default 200 ms), and the App source scan found no disallowed imports. No action required beyond normal monitoring.
- Amber: All core services reachable but one or more latencies are between 200 ms and 1500 ms, or benign warnings were detected (e.g., third-party dev-only code patterns). Review logs and performance; no immediate incident needed unless sustained.
- Red: Any critical service unreachable, latency consistently >1500 ms, or the App source scan found disallowed imports (policy violation). Treat as an incident.

Operator guidance (Engine)
- When the Engine page reports Amber:
  - Check the last 10 logs for the failing service and review resource metrics (CPU, memory, disk I/O).
  - If the issue is latency-only, monitor for 5–10 minutes for stabilization before escalating.
- When the Engine page reports Red:
  - If a core service is unreachable, follow incident triage: examine container logs, restart the affected service if needed, and check resource exhaustion and network connectivity.
  - If the App source scan reports direct DB/LLM imports, treat as a compliance incident: immediately remove the offending imports or revert the change, and re-run the scan. The App must never access DB or LLM clients directly — the Engine is the only permitted actor.

Remediation tips
- Ollama 404 / unhealthy: verify the Ollama container is running (`docker ps`), and pull/start the required model if missing (example: `docker exec -it ollama ollama pull mistral`). After model pull, re-check `/internal/status`.
- Postgres/Redis socket failures: verify container is running, check `docker logs <container>`, and ensure `POSTGRES_HOST`/`REDIS_HOST` env vars point to the correct service name.

Notes
- These Engine checks are intentionally stricter than the App's lightweight page — the Engine page includes the App source scan and is the authoritative policy enforcer for service separation.
- If you change thresholds or add new checks, update this document and `README_DOCUMENTATION.md` to preserve operator knowledge.

Monitoring & Metrics
- The Engine exposes a Prometheus-compatible metrics endpoint at `GET /metrics` which includes key Ollama health metrics:
  - `ollama_up`: 1 when Ollama returned HTTP 200, 0 otherwise.
  - `ollama_status_code`: last HTTP status code observed from the Ollama health probe.
  - `ollama_response_time_ms`: recent health probe response time in milliseconds.

- Recommended setup:
  1. Configure Prometheus to scrape `http://<engine-host>:8001/metrics`.
  2. Create alerts: `ollama_up == 0` (fire immediately), `ollama_response_time_ms > 1500` (warn/alert), `ollama_status_code >= 500` (server error).
  3. (Optional) Deploy a small Ollama exporter sidecar that can run `ollama list` or call additional Ollama internal APIs to publish `ollama_model_count` and `ollama_loaded_models` metrics — this is useful because the Engine cannot reliably introspect the Ollama container's model directory.

- Runbook snippets:
  - Check container: `docker ps --filter name=ollama`
  - Check logs: `docker logs --tail 200 ollama`
  - Verify models (inside ollama): `docker exec ollama ollama list`
  - Pull model (inside ollama): `docker exec -it ollama ollama pull mistral`

Keep this section updated if you add exporter sidecars or change metric names.

Policy notes
- The App service must never connect directly to the DB or LLM. The Engine is the only service allowed to access the DB and run LLM calls.
- If `/internal/status` reports Red because the app code contains DB/LLM client imports, treat this as a compliance incident and remediate immediately.

Usage & Rebuild guidance
1. To view the page locally on the Engine host:
   - From the host machine (where the Engine is running), open: `http://localhost:8001/internal/status`.
2. Rebuild instructions (dev):
```powershell
.\manager.bat
# choose: rebuild_app_engine (or use the equivalent docker_manager.ps1 call)
```
1. If you add this feature or modify it, update this doc and `README_DOCUMENTATION.md`.

Notes for operators
- The endpoint restricts access to localhost IPs. In containerized deployments, local requests may appear from Docker-internal addresses (172.x). The check allows such addresses by default but review if your environment differs.

Revision history
- 2026-01-02: Initial implementation and documentation.
