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

---

### III. Critical Connectivity Rules

All development must adhere to the following concrete, network-isolated connection details:

1. **App-to-DB & App-to-LLM Access:** The App Service **MUST NOT** make direct connections to the database (`dev_db`/`prod_db`) or the LLM (`ollama`) because it is isolated on the `frontend-network`.
2. **App-to-Engine Communication:** The App Service must initiate **asynchronous requests** to the Engine Service by targeting the internal service name **`cognitive-engine` or `prod_engine`** on port **`8001`**.
3. **Engine-to-DB/LLM Connections:** The Engine Service, being on the `core-network`, uses the internal service names **`dev_db` / `prod_db`** (port `5432`) and **`ollama`** to perform its privileged operations.

---

### IV. Mandatory Production Execution Commands

| Service | Execution Command (Gunicorn) |
| :--- | :--- |
| **App Service** | `gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000` |
| **Engine Service** | `gunicorn engine.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001` |
