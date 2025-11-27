# 02 Infrastructure Setup.md

## Infrastructure Setup for the Cultivate → Execute → Contribute Engine

**File Path:** 02 infrastructure setup.md
**Audience:** DevOps Engineers, Full-Stack Architects, Infrastructure Developers.

---

### Purpose

The **"How"** for the environment. This document defines the entire core technology stack, the concrete service architecture (including ports and service names), and the crucial network security boundaries via Docker, ensuring compliance with the Principle of Least Privilege (PoLP).

---

### I. Core Technology Stack (Concrete Implementation)

| Component | Technology / Docker Image | Internal Service Name | Python Entrypoint |
| :--- | :--- | :--- | :--- |
| **Database** | `pgvector/pgvector:pg16` | `dev_db` / `prod_db` | N/A |
| **LLM Engine** | `ollama/ollama:latest` | `ollama` | N/A |
| **App Service (Body)** | `Dockerfile` (Multi-stage) | `app` / `prod_app` | `app.main:app` |
| **Message Queue** | `redis:latest` | `message-broker` | N/A |
| **Engine Service (Brain)** | `Dockerfile` (Multi-stage) | `cognitive-engine` / `prod_engine` | `engine.main:app` |

---

### II. Service Architecture and Network Security (PoLP)

The system enforces the Principle of Least Privilege (PoLP) through strict network segregation, as defined in `docker-compose.yml`.

| Service | Internal Port | Exposed Port (Host) | Network Access | Database User |
| :--- | :--- | :--- | :--- | :--- |
| **Application (The Body)** | `8000` | `8000` | **`frontend-network` ONLY** | `lifebuddy_rw` |
| **Cognitive Engine (The Brain)**| `8001` | `8001` (Dev/Testing) | **`core-network` ONLY** | `cognitive_engine_full` |
| **Database** | `5432` | `5432` (Dev only) | **`core-network` ONLY** | N/A |
| **LLM (`ollama`)** | N/A | N/A | **`core-network` ONLY** | N/A |
| **Message Queue (Redis)** | `6379` | N/A | **`core-network` ONLY** | N/A |

---

### III. Critical Connectivity Rules

All development must adhere to the following concrete, network-isolated connection details:

1. **App-to-DB & App-to-LLM Access:** The App Service **MUST NOT** make direct connections to the database (`dev_db`/`prod_db`) or the LLM (`ollama`) because it is isolated on the `frontend-network`.
2. **App-to-Engine Communication:** The App Service must initiate **asynchronous requests** to the Engine Service by using the internal service name **`message-broker`** (Redis) to queue long-running jobs, and then optionally polling the Engine's API (`cognitive-engine:8001`) for job status. The App **MUST NOT** make synchronous requests to the Engine for heavy tasks.
3. **Engine-to-DB/LLM Connections:** The Engine Service, being on the `core-network`, uses the internal service names **`dev_db` / `prod_db`** (port `5432`) and **`ollama`** to perform its privileged operations.

---

### IV. Mandatory Production Execution Commands

| Service | Execution Command (Gunicorn) |
| :--- | :--- |
| **App Service** | `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` |
| **Engine Service** | `gunicorn engine.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001` |

## V. Mandatory Environment Variable Configuration (CRITICAL for Deployment) 🔒

This manifest defines the minimum required environment variables that **MUST** be present in the `.env.dev` and `.env.prod` files referenced by `docker-compose.yml`. The system will fail to start without these variables.

### A. General Application Secrets

| Variable | Description | Security Note / Example Source |
| :--- | :--- | :--- |
| **JWT_SECRET_KEY** | **CRITICAL:** The secret key used to sign all JSON Web Tokens (JWTs). | Must be a long, random string (e.g., generated via `openssl rand -hex 32`). |
| **JWT_ALGORITHM** | The signing algorithm for JWTs. | `HS256` |
| **APP_SECRET_KEY** | A shared secret/API key for internal App-to-Engine communication. | Used for internal service-to-service validation. |

#### A.1. Mandatory JWT Claims Specification (CRITICAL RLS ENFORCEMENT)

All generated JWTs **MUST** contain the following claims. The App Service relies solely on these claims to enforce the Proxied API Pattern for RLS.

| Claim Key | Data Type | Purpose |
| :--- | :--- | :--- |
| `sub` | String (UUID) | The **User ID** (e.g., `user_id` from the `users` table). **This is the identifier extracted and passed to the Engine.** |
| `aud` | String | Audience claim, must be set to `life-buddy-app` for all tokens. |
| `iat` | Integer (timestamp) | Issued At time. |
| `exp` | Integer (timestamp) | Expiration time. |

### B. Database Connection Variables

These variables define the credentials for the roles created in `03 db_schema.sql`.

| Variable | Target Role | Description |
| :--- | :--- | :--- |
| **POSTGRES_DB** | N/A | The name of the database instance. |
| **POSTGRES_USER_FULL_PASS** | `cognitive_engine_full` | Password for the **Bypass RLS** role. **CRITICAL SECRET.** |
| **POSTGRES_USER_RLS_PASS** | `cognitive_engine_rls` | Password for the **Enforce RLS** role. **CRITICAL SECRET.** |

### C. Service Connection Variables

These use the internal service names defined in **Section I** of this document.

| Variable | Service Target | Description |
| :--- | :--- | :--- |
| **REDIS_HOST** | `message-broker` | The internal DNS name for the Redis service. |
| **REDIS_PORT** | `6379` | The port for the Redis service. |
| **OLLAMA_HOST** | `ollama` | The internal DNS name for the Ollama LLM service. |
| **OLLAMA_MODEL** | `ollama` | The specific language model to load (e.g., `llama3:8b`). |
