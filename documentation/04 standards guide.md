# 04 Standards Guide.md

## Development Standards and Architecture (Version 2.0)

### Purpose

The **"Rules."** Ensures consistency in style, naming, architecture, and, most critically, **security** across the two decoupled services.

### What to Include

1. Naming Conventions.
2. The V2 Folder Structure (Body and Brain services).
3. The V2 Architectural Decisions (Service Separation, PoLP, Network Isolation).
4. Data Integrity, RLS, and Security Mandates.

***

### 1. Naming Conventions

| Element | Convention | Example |
| :--- | :--- | :--- |
| Python Variables/Functions | `snake_case` | `calculate_adherence_rate` |
| Python Classes/Models | `PascalCase` | `User`, `ActionableItemModel` |
| Database Tables/Columns | `snake_case` | `adherence_log`, `hashed_password` |
| API Endpoints (URL Paths) | `kebab-case` | `/api/v1/action-items` |
| Constants/Enums | `UPPER_SNAKE_CASE` | `ITEM_TYPE_HOLISTIC` |

***

### 2. Code Structure (V2 High-Level Architecture)

The codebase is split into two distinct, network-isolated services: the public-facing **Application (The Body)** and the proprietary **Cognitive Engine (The Brain)**.

/ ├── app/ # Application Service (The Body) - Public-facing APIs │
  ├── api/ # Public FastAPI router definitions (endpoints) │
  ├── models/ # Pydantic models (DTOs) │
  ├── services/ # Business logic for CRUD (e.g., UserService, AdherenceService) │
  └── main.py # Entry point for the Body service
  ├── engine/ # Cognitive Engine Service (The Brain) - Proprietary Logic │
  ├── api/ # Internal FastAPI router definitions (The Brain's API) │
  ├── core/ # Core proprietary AI/LLM logic (H1, H2, H3) │
  ├── workers/ # Background/scheduled tasks (e.g., vectorization) │
  └── main.py # Entry point for the Brain service
  ├── db/ # Database files │
  ├── 03 db_schema.sql # Database DDL, RLS policies │
  └── init.sql # Postgres startup scripts (user creation, extensions)
  ├── .env.dev # Environment vars for development
  ├── .env.cognitive # SECURE environment vars for THE BRAIN
  └── docker-compose.yml # Defines the V2 services and networks

***

### 3. Architectural Decisions (V2 Separation & PoLP)

All logic must adhere to the **Principle of Least Privilege (PoLP)** enforced by the V2 architecture.

#### A. Service Responsibilities

| Service | Responsibility | Database User Privilege | Network Access |
| :--- | :--- | :--- | :--- |
| **Application (The Body)** | User Authentication, CRUD operations on `actionable_items` and `adherence_log`, serving the UI. | `lifebuddy_rw` (Read/Write to standard tables). **CANNOT read `document_vectors`**. | `frontend-network` (Public/External). |

| **Cognitive Engine (The Brain)** | All proprietary logic: Vectorization, RAG, Cognitive Synthesis (H1, H2, H3), Item Generation. | `cognitive_engine_full` (Full access to all tables, including `document_vectors`). | `core-network` (Private/Internal). |

#### B. Inter-Service Communication

* The **Body** communicates with the **Brain** only via a dedicated, authenticated **Internal API**.
* All communication to the Brain must include the required `INTERNAL_API_KEY` for service-to-service authentication.

***

### 4. Data Integrity and Privacy

#### A. Row-Level Security (RLS) Mandate

**RLS is the primary security boundary** for all user data and **MUST** be enabled on all tables containing user-specific information (`actionable_items`, `adherence_log`, `documents`, `health_metrics`, `document_vectors`).

* The application must set the **`app.current_user_id`** session variable immediately after successful user authentication.
* All database queries executed by the `lifebuddy_rw` user will be **automatically filtered** by the PostgreSQL RLS policy, making it impossible for a developer error in the API logic to expose another user's data.

#### B. Logic Location

* **Core Business Logic:** All non-security-critical logic remains in the Python **Service Layer** of The Body or The Brain.
* **Security Logic:** All user isolation logic (RLS policies) **MUST** reside in the PostgreSQL layer.

#### C. Encryption Strategy

* **In Transit:** All API communication (internal and external) must be secured (HTTPS/TLS).
* **At Rest:** The entire PostgreSQL instance must be secured with a robust encryption strategy (e.g., TDE or file-system level encryption).
* **Vector Store:** The `document_vectors` table is secured by the combination of network isolation, a high-privilege user (`cognitive_engine_full`), and mandatory **RLS**.
```eof