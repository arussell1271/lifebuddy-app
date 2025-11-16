# 02 Infrastructure Setup.md

## Infrastructure Setup for the Cultivate → Execute → Contribute Engine

### Purpose

The **"How"** for the environment. Defines the entire tech stack and the security boundaries for the Cognitive Engine.



### What to Include

**Stack:** Python version, specific Local LLM model, FastAPI/Gunicorn, etc.

**Docker:** The full service definition for development and production. The full docker-compose.yml file contains this information.

**Networking:** Security groups (networks), exposed ports, and service names.


### 1. Technology Stack Summary

**Primary Language:** Python 3.11+ **Rationale:**  Ideal for data science, MLOps, and the cognitive ecosystem.

**Web Framework:** FastAPI   **Rationale: ** High-performance async APIs, suitable for heavy Cognitive workloads.

**Production Server: ** Gunicorn + Uvicorn Workers **Rationale: ** Industry standard for Python application performance and stability.

**Database:** PostgreSQL 16+  **Rationale: ** Robust, transactional, and scalable.

**Vector Store:** pgVector (PostgreSQL extension) **Rationale : ** Keeps sensitive vector embeddings secure within the trusted database boundary.

**Containerization:** Docker & Docker Compose  **Rationale: ** Provides reproducible, isolated environments for dev and prod.

**Cognetive Model:** Ollama (Local LLM Engine)  **Rationale: ** Provides a local, air-gapped solution for the Cognitive Engine.



### 2. Service Architecture (The Body and The Brain)

The application is split into two distinct, network-isolated services to enforce the Principle of Least Privilege (PoLP):

Service                      |   Folder   |  Description    |  Database User      |  Network Access

Application (The Body)       |  /app      | The user-facing API. Handles authentication, CRUD operations, and logging. Never accesses vector data.     |  lifebuddy_rw (Read/Write to standard tables)  | frontend-network (Public)

Cognitive Engine (The Brain) | /engine    |  The proprietary engine. Handles vectorization, RAG, and cognitive synthesis (H1, H2, H3 logic). Requires high privilege.     | cognitive_engine_full (Full access to all tables, including document_vectors)   | core-network (Private)

### 3. Networking and Security Boundaries

To secure the sensitive vector data (document_vectors), we enforce strict network isolation:

1. frontend-network: This is the public-facing network.

**Services:** app (Body API) and pgadmin (in development only).

**Boundary:** Allows external access from the host machine/internet.

2. core-network: This is the restricted, secure network.

**Services:** db, cognitive-engine (The Brain), and ollama (LLM).

**Security:** Services on the frontend-network cannot communicate with services on the core-network. This physically prevents the user-facing API (The Body) from ever directly talking to the database or the LLM, forcing all synthesis requests to go through the highly controlled Cognitive Engine (The Brain).