# ⚙️ UI Technical Specification: The Holistic Cognitive Data Engine

**File Path:** 06 ui technical specifications.md
**Audience:** Full-Stack Engineers, Backend Developers, UI Developers.

---

## 💡 Instructions for Use

1. **Scope:** Defines the technical implementation, required **FastAPI API Contracts** on the App Service, client-side state management, and the overall front-end architecture.
2. **Adherence (CRITICAL):** Must strictly conform to the **App/Engine Service Separation** and the **Asynchronous Processing Flow** constraint (App never waits for the Engine).
3. **Security:** All API contracts must align with the **RLS** mandate by ensuring the client can acquire and use a JWT.

---

## I. Core Client Stack Definition

| Layer | Recommended Technology | Rationale / Notes |
| :--- | :--- | :--- |
| **Client Framework** | **Vue 3** (Composition API) | Highly performant, reactive, and scalable for complex interfaces. |
| **State Management** | **Pinia** | Lightweight, type-safe, and modular state management for Vue 3. |
| **Styling** | **Tailwind CSS** | Utility-first approach ensures rapid, responsive development (mobile-first primary target). |

## II. Feature: User Authentication (Auth)

### 2.1 API Contracts (App Service - `app/api/v1/auth`)

⚠️ ARCHITECTURAL EXCEPTION: While the general architecture follows an Asynchronous/Polling pattern, Authentication endpoints are Synchronous. The App Service waits for the Engine to validate credentials and return the JWT before responding to the client to ensure a smooth login UX.

#### A. User Login: Token Acquisition (CRITICAL: Proxied to Engine)

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/auth/login` |
| **Method** | POST |
| **Authentication** | None (Public) |
| **Request Payload** | `{"username": "string", "password": "string"}` |
| **App Service Action** | **Synchronously forwards** the request (username/password) to the **Engine Service**'s internal Auth endpoint (`cognitive-engine:8001/auth/login`). |
| **Success Response** | `{"access_token": "JWT_STRING", "token_type": "bearer"}` |
| **Failure Response** | `401 Unauthorized` |

#### B. User Registration: New User Creation (CRITICAL: Proxied to Engine)

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/auth/register` |
| **Method** | POST |
| **Authentication** | None (Public) |
| **Request Payload** | `{"username": "string", "password": "string", "email": "string"}` |
| **App Service Action** | **Synchronously forwards** the request (username/password/email) to the **Engine Service**'s internal Auth endpoint (`cognitive-engine:8001/auth/register`). The Engine handles user hashing, DB write, and initial token generation. |
| **Success Response** | `201 Created` with a `Location` header or the full login response (as per Login: A). |
| **Failure Response** | `409 Conflict` (Username/Email already exists). |

---
**CRITICAL ARCHITECTURAL NOTE:** To uphold the **Principle of Least Privilege (PoLP)** and **Network Isolation**, the App Service **MUST NOT** import or use any database client library (e.g., `psycopg2`) or hold database credentials. All database operations, including Auth and Registration, are delegated to the **Cognitive Engine** (The Brain).

#### C. Request Password Reset (App-to-Engine Asynchronous Delegation)

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/auth/request-password-reset` |
| **Constraint Adherence** | App immediately queues the request for the **Engine Service** via the message queue (Redis/RabbitMQ). |
| **Success Response (202 Accepted)**| `detail`: "Password reset request accepted and queued." |

### 2.2 API Contracts (Account Recovery - App Service - `app/api/v1/auth`)

The following synchronous contracts are required to support the "Forgot Password" and "Forgot Username" flows as per the Functional Guide. These endpoints must perform rate-limiting.

| Functional Goal | HTTP Method | Endpoint (App Service) | Request Payload (Body) | Response Data (Status Code) |
| :--- | :--- | :--- | :--- | :--- |
| **Forgot Password** | `POST` | `/forgot-password` | `{ "email": "user@example.com" }` | `{ "message": "Recovery instructions sent." }` (202 Accepted) |
| **Password Reset** | `POST` | `/reset-password` | `{ "token": "...", "new_password": "..." }` | `{ "message": "Password successfully reset." }` (200 OK) |
| **Forgot Username** | `POST` | `/forgot-username` | `{ "email": "user@example.com" }` | `{ "message": "Username sent via email." }` (202 Accepted) |

### 2.3 API Contracts (App Service - `app/api/v1/synthesis`)

⚠️ ARCHITECTURAL RULE: These endpoints must strictly adhere to the Asynchronous Pattern (App MUST NOT wait for Engine).

| Functional Goal | HTTP Method | App Service Path (FastAPI) | Response Status | Constraint Adherence |
| :--- | :--- | :--- | :--- | :--- |
| **Initiate Synthesis** | `POST` | `/api/v1/synthesis/job` | `202 Accepted` | **Asynchronous:** Places job on Redis Queue (`rq`) and returns a `job_id`. |
| **Poll Status** | `GET` | `/api/v1/synthesis/job/{job_id}` | `200 OK` | **Polling:** Queries Redis Queue for `job_id` status (`PENDING`, `COMPLETE`, `FAILED`). |
| **Retrieve Synthesis** | `GET` | `/api/v1/synthesis/{synthesis_id}` | `200 OK` | **RLS-Protected:** Retrieves final result from `synthesis_log` table using `get_db_rls_session`. |

### 2.4 Client-Side Implementation Details

| Component | Responsibility | Technical Notes |
| :--- | :--- | :--- |
| **Auth Store (Pinia)**| Global state for token, user details, and authentication status. | Store the JWT in **Session Storage** or an **HTTP-only Cookie** (preferred for security). **Do NOT use Local Storage.** |
| **HTTP Interceptor**| Security layer for all API communication. | Automatically inject the saved JWT into the `Authorization: Bearer <token>` header for every protected route call. |

## III. Feature: User Preferences and Cognitive Configuration

### 3.1 Synchronous Data Retrieval Endpoints

These endpoints are simple, synchronous proxies from the App Service to the Engine Service. The App Service path is: `/api/v1/engine/{user_id}/{engine_route}`) for all synchronous user data operations.

This table defines the required `engine_route` values for the Engine Service.

| Functional Goal | HTTP Method | Client App Path/Action | Required `engine_route` Parameter | Engine Logic Performed |
| :--- | :--- | :--- | :--- | :--- |
| **User Identity** | `GET` | Retrieve User Profile/Stats | `get_user_profile` | Fetches data from `users` and `cognitive_efficacy_metrics`. |
| **User Preferences** | **GET** | Retrieve user preferences | `get_user_preferences` | Fetches data from `user_preferences`. |
| **User Preferences** | `PUT` | Update user preferences | `update_user_preferences` | Updates row in `user_preferences`. |
| **Action Items** | `GET` | Fetch all pending items | `get_all_action_items` | Fetches data from `actionable_items` where `is_complete = FALSE`. |
| **Action Items** | `POST` | Create a new action item | `create_action_item` | Inserts a new row into `actionable_items`. |
| **Action Items** | `PUT` | Mark item as complete | `complete_action_item` | Updates `actionable_items.is_complete = TRUE` and logs adherence. |
| **Daily Check** | `GET` | Get status of daily check | `get_daily_check_status` | Queries `pre_synthesis_answers` to determine if all mandatory questions are `COMPLETE`. |
| **Daily Check** | `POST` | Submit a daily answer | `submit_daily_answer_proxy` | **Engine (Synchronous):** Inserts row into `pre_synthesis_answers`. **Engine (Asynchronous):** Immediately enqueues implicit check job and returns `job_id`. |
| **Documents** | `GET` | Fetch recent dreams/journals | `get_recent_documents` | Retrieves up to the last 5 `DREAM` or `JOURNAL` documents. |

### 3.2 API Contracts (App Service - `app/api/v1/user-preferences`)

The App Service mediates all user interactions with the preference data.

#### A. Get User Preferences

| Property | Value |
| :--- | :--- |
| **Endpoint** | `PATCH /api/v1/user-preferences` |
| **Method** | PATCH |
| **Authentication** | Required (JWT for RLS context) |
| **Request Schema (Body)** | Subset of preferences to update. Now accepts the optional field: `synthesis_matrix: JSONB` |
| **Notes** | The App Service validates the JSON format and saves it directly to the database. The Engine Service is responsible for interpreting and executing the logic defined within the `synthesis_matrix`. |

#### B. Update User Preferences

| Property | Value |
| :--- | :--- |
| **Endpoint** | `PATCH /api/v1/user-preferences` |
| **Method** | PATCH |
| **Authentication** | Required (JWT for RLS context) |
| **Request Schema (Body)** | Subset of preferences to update (e.g., `spiritual_mode`: "TAROT") |
| **Success Response (200 OK)**| The full, updated preferences object. |

#### C. Pre-Synthesis Question Retrieval

| Property | Value | Rationale / RLS Policy |
| :--- | :--- | :--- |
| **Endpoint** | `GET /api/v1/cognitive/pre-analysis-questions/{advisor_type}` | Synchronous call to get mandatory questions. |
| **Method** | `GET` | |
| **Authentication** | Required (JWT). | |
| **Purpose** | Retrieves the set of static questions required by the Engine for a specific advisor type before synthesis can be initiated. | This data is **NOT RLS-enabled** (it is global system config). |
| **Response Body (Next Question)** | `{"status": "NEXT_QUESTION", "question": {"id": UUID, "text": "What was the dominant feeling...?", "format": "TEXT"\|"NUMBER"}}` | The client uses this list to render the UI form. |

#### D. Daily Cognitive Check Status (GATING ENDPOINT)

| Property | Value | Rationale / RLS Policy |
| :--- | :--- | :--- |
| **Endpoint** | `GET /api/v1/cognitive/daily-check-status/{advisor_type}` | Primary gate for the client. |
| **Method** | `GET` | |
| **Authentication** | Required (JWT). | |
| **Purpose** | Checks the `user_cognitive_state` table for the current user and current date. Determines if all mandatory questions for the day are complete. | RLS Policy: `user_isolation_cognitive_state` ensures the user only sees their own daily state. |
| **Response Body (Status COMPLETE)** | `{"status": "COMPLETE", "unanswered_questions": []}` | Client unlocks the main chat input field. |
| **Response Body (Status PENDING)** | `{"status": "PENDING", "unanswered_questions": [{"question_id": UUID, "text": str, "format": str}, ...]}` | Client uses the `unanswered_questions` array to render the required input forms. |

### 3.3 Client-Side Implementation: Preferences Screen

| Component | Responsibility | Technical Notes |
| :--- | :--- | :--- |
| **Preferences Store (Pinia)**| Manages the state of the preferences object. | Fetch data on mount of the settings route. Use optimistic updates upon patch requests. |
| **UI Components** | Input fields for names, radio groups/dropdowns for modes and tones. | Implement using **Tailwind CSS** for responsive design (mobile-first primary). Ensure validation matches database constraints (e.g., for Spiritual Mode choices). |
| **HTTP Requests** | `GET` on load, `PATCH` on save/change. | Must use the authenticated HTTP Interceptor to ensure JWT is passed. |

### 3.4 API Contracts (App Service - Daily Check Flow)

These contracts govern the execution of the Daily Check (CULTIVATE/EXECUTE Questions) which is a functional prerequisite for all other interactions.

#### A. Get Daily Check Status

| Property | Value |
| :--- | :--- |
| **Endpoint** | `GET /api/v1/daily-check/status` |
| **Method** | GET |
| **Authentication** | Required (JWT for **Primary User**). |
| **Purpose** | Retrieves the current overall state of the daily check (e.g., whether the flow is complete or in progress). |
| **Response Body (Example)** | `{"status": "IN_PROGRESS", "total_questions": 5, "questions_remaining": 2}` |

#### B. Get Next Daily Check Question/Data (NEW)

| Property | Value |
| :--- | :--- |
| **Endpoint** | `GET /api/v1/daily-check/question` |
| **Method** | GET |
| **Authentication** | Required (JWT for **Primary User**). |
| **Purpose** | Retrieves the **single, next required question** for sequential rendering, based on the `questions_remaining` count. |
| **Response Body (Next Question)** | `{"status": "NEXT_QUESTION", "question": {"id": UUID, "text": "What was the dominant feeling...?", "format": "TEXT"}}` |
| **Response Body (Complete)** | `{"status": "COMPLETE", "message": "Daily check complete for today."}` |

#### C. Submit Daily Check Answer

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/daily-check/answer` |
| **Method** | POST |
| **Authentication** | Required (JWT for **Primary User**). |
| **Purpose** | Submits a user's answer for the identified question. |
| **Request Body** | `{"question_id": UUID, "answer_text": "The dominant feeling in my dream was peace."}` |
| **Response Body (Example)** | `{"success": true, "message": "Answer saved. Next question data is available via GET /question."}` |

### 3.5 API Contracts (App Service - Actionable Items & Adherence)

These contracts manage the core "Execute" phase deliverables (Actionable Items) and the logging of user progress.

#### A. Retrieve Actionable Items

| Property | Value |
| :--- | :--- |
| **Endpoint** | `GET /api/v1/action-items` |
| **Method** | GET |
| **Authentication** | Required (JWT for **Primary User**). |
| **Purpose** | Retrieves all Actionable Items for the current date or specified date range. |
| **Query Params** | `?start_date=YYYY-MM-DD` (Optional) |
| **Response Body (Example)** | `[{"item_id": UUID, "title": "Be present while drinking your coffee.", "item_type": "HOLISTIC", "status": "PENDING"}]` |

#### B. Log Adherence

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/action-items/{item_id}/adherence` |
| **Method** | POST |
| **Authentication** | Required (JWT for **Primary User**). |
| **Purpose** | Logs the user's success or failure against a specific Actionable Item. |
| **Path Params** | `item_id`: The UUID of the item being logged. |
| **Request Body** | `{"success": true, "notes": "Successfully completed item before 10AM."}` |
| **Response Body (Example)** | `{"success": true, "message": "Adherence logged. Item status updated to COMPLETED."}` |

## IV. Feature: Delegated Access Management

This feature allows the Primary User (via the App Service) to grant and revoke access to Secondary Users (Professionals) by managing entries in the `data_access_grants` table.

### 4.1 API Contracts (App Service - `app/api/v1/grants`)

| Functional Goal | HTTP Method | API Path | Payload / Response | App Logic / RLS Context |
| :--- | :--- | :--- | :--- | :--- |
| **List Grants** | `GET` | `/api/v1/grants` | `200` with list of current `data_access_grants` objects. | Synchronous DB read. The RLS policy on the `data_access_grants` table ensures only the authenticated Primary User can view their own grants. |
| **Create Grant** | `POST` | `/api/v1/grants` | **Payload:** `professional_user_id: UUID`, `access_scope: JSONB`. | Synchronous DB write. Inserts a new row into `data_access_grants`. The `primary_user_id` is derived from the authenticated Primary User's JWT. |
| **Revoke Grant** | `DELETE` | `/api/v1/grants/{professional_user_id}` | `204` No Content on success. | Synchronous DB write. Finds the grant where `professional_user_id` matches the path and sets `revoked_at = CURRENT_TIMESTAMP`. |

### 4.2. Update Section: Proxied API Flow for Secondary Users

Insert this section into the document, likely after the main table of proxied routes.

### 4.2 Proxied API Flow for Secondary Users (CRITICAL RLS ENFORCEMENT)

The App Service MUST adhere to the following when proxying requests for **Secondary Users** (Professionals):

* **Authentication:** The Secondary User's JWT is validated.
* **Context Extraction:** The Secondary User's ID is extracted from the JWT's `sub` claim.
* **Proxy Header:** The App Service passes the **Secondary User's ID** in the `X-User-ID` RLS context header to the Engine.
* **Engine Trust:** The Engine receives the request, and its security layer (`get_rls_session`) sets the RLS context variable `app.current_user_id` to the Secondary User's ID.
* **DB Authorization:** The **Dual-Mode RLS Policy** in the database evaluates the access: if an active, scoped grant exists, the query succeeds; otherwise, it returns zero rows, maintaining security isolation.

## V. Feature: Professional Collaboration & Secure Sharing

The App Service mediates all consent and access management (via the `data_access_grants` table) to ensure RLS is correctly enforced by the database.

### 5.0 Client-Side Role-Based Rendering (Vue/Pinia)

The client application must implement a state check on successful authentication to route the user based on their assigned role.

| Property | Value | Rationale |
| :--- | :--- | :--- |
| **Client State Variable** | `Pinia.user_store.user_role: string` (`PRIMARY_USER` or `SECONDARY_USER`) | Determines UI context for authorization and rendering. |
| **Secondary User Route** | Navigate to `/professional/portal`. | Dedicated Portal Access. |

### 5.1 API Contracts (App Service - `app/api/v1/data-grants`) - Primary User Actions

... (Keep existing `POST /data-grants/grant` and `POST /data-grants/revoke/{professional_user_id}` as is) ...

#### 5.1.A Client List Retrieval

| Property | Value |
| :--- | :--- |
| **Endpoint** | `GET /api/v1/professionals/clients` |
| **Method** | GET |
| **Authentication** | Required (JWT for **Secondary User**). |
| **Purpose** | Retrieves a list of active client UUIDs consented to this Professional, filtered by an active `data_access_grants` record. |
| **Response Body (Example)** | `[{"client_user_id": UUID, "client_username": "client.user", "last_report_date": "2024-10-01"}]` |

### 5.2 API Contracts (Engine Service Proxy - CRITICAL ASYNCHRONOUS CORRECTION)

This endpoint **MUST** adhere to the **Asynchronous Processing Flow** constraint. The App Service must **NOT** wait for the Engine's synthesis.

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/professional-synthesis` |
| **Method** | POST |
| **Authentication** | Required (JWT for **Professional User**). |
| **Purpose** | Professional requests a holistic synthesis report for their linked client. |
| **App Service Action** | Sends request to Engine via internal message queue (e.g., Redis/RabbitMQ) and immediately returns a non-blocking confirmation. |
| **Request Payload (CRITICAL ADDITION)** | **MUST** include the `daily_check_answers` object for the client user being queried. |
| **Success Response (CRITICAL: 202 Accepted)**| `{"status": "Report processing initiated", "job_id": UUID}` |

### 5.3 API Contracts (Engine Service RLS Proxy - CRITICAL SYNCHRONOUS FLOW)

The App Service MUST use this endpoint for all operations that require fetching or modifying user-specific data. This is the **only acceptable synchronous data access** call to the Engine, as it is a low-latency proxy to enable RLS.

| Property | Value |
| :--- | :--- |
| **Endpoint Pattern** | `POST /api/v1/data-proxy/{user_id}/{engine_route}` |
| **Method** | POST |
| **Authentication** | Required (Internal JWT or shared secret for App-to-Engine communication). |
| **App Service Action** | 1. Decode the authenticated `user_id` from the user's JWT. 2. Pass this `user_id` as the path parameter. 3. Pass the original user request body/query parameters as the payload to the Engine. |
| **Purpose** | Proxies the request to the Engine, allowing the Engine to safely set the RLS context (`SET app.current_user_id = '{user_id}';`) before executing the requested business logic (`engine_route`). |
| **Example App Call** | App calls Engine: `POST cognitive-engine:8001/api/v1/data-proxy/123e4567-e89b.../health-metrics` |

## 5.4 API Route Mapping: Synchronous Data Proxy Endpoints (RLS MANDATORY)

The App Service MUST use the RLS Proxy pattern (`POST /api/v1/data-proxy/{user_id}/{engine_route}`) for all synchronous user data operations.

This table defines the required `engine_route` values for the Engine Service.

| Functional Goal | HTTP Method | Client App Path/Action | Required `engine_route` Parameter | Engine Logic Performed |
| :--- | :--- | :--- | :--- | :--- |
| **User Identity** | `GET` | Retrieve User Profile/Stats | `get_user_profile` | Fetches data from `users` and `cognitive_efficacy_metrics`. |
| **Action Items** | `GET` | Fetch all pending items | `get_all_action_items` | Fetches data from `actionable_items` where `is_complete = FALSE`. |
| **Action Items** | `POST` | Create a new action item | `create_action_item` | Inserts a new row into `actionable_items`. |
| **Action Items** | `PUT` | Mark item as complete | `complete_action_item` | Updates `actionable_items.is_complete = TRUE` and logs adherence. |
| **Daily Check** | `GET` | Get status of daily check | `get_daily_check_status` | Queries `pre_synthesis_answers` to determine if all mandatory questions are `COMPLETE`. |
| **Daily Check** | `POST` | Submit a daily answer | `submit_daily_answer` | Inserts an answer into `pre_synthesis_answers` and performs implicit check logic. |
| **Documents** | `GET` | Fetch recent dreams/journals | `get_recent_documents` | Retrieves up to the last 5 `DREAM` and `JOURNAL` documents. |
| **Documents** | `POST` | Upload a new document | `create_document` | Inserts a new document row and triggers the vector embedding job. |
