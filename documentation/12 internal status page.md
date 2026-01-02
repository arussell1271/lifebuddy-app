# Internal Status Page

Purpose
- A local-only engine endpoint that provides a traffic-light view (Green/Amber/Red) of core services and code integrity checks.

Location
- Engine endpoint: `GET /internal/status` (accessible from localhost only)

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
