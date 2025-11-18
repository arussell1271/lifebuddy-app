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

#### A. User Login: Token Acquisition

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/auth/token` |
| **Description** | Authenticates the user and generates a JWT. |
| **Request Schema (Body)** | `username`: string (or email); `password`: string |
| **Success Response (200 OK)** | `access_token`: string (JWT); `token_type`: "bearer" |
| **Security Action (CRITICAL)** | App middleware **MUST** extract the `user_id` from the JWT payload and use it to execute: `SET app.current_user_id = '<user_uuid>';` for all subsequent database interactions. |

#### B. User Registration: Account Creation

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/auth/register` (Adheres to `kebab-case` standard) |
| **Description** | Creates a new user record (UUID, Email, Username, Hashed Password) in the `users` table and immediately returns an authentication token. |
| **Request Schema (Body)** | `email`: string; `username`: string; `password`: string |
| **Success Response (201 Created)**| `access_token`: string (JWT); `token_type`: "bearer" |
| **Failure Response (409 Conflict)**| If the provided email or username already exists in the `users` table. |
| **Security Action (CRITICAL)** | Upon token generation, the App middleware **MUST** extract the `user_id` from the JWT payload and use it to execute: `SET app.current_user_id = '<user_uuid>';` for all subsequent database interactions. |

#### C. Request Password Reset (App-to-Engine Asynchronous Delegation)

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/auth/request-password-reset` |
| **Constraint Adherence** | App immediately queues the request for the **Engine Service** via the message queue (Redis/RabbitMQ). |
| **Success Response (202 Accepted)**| `detail`: "Password reset request accepted and queued." |

### 2.2 Client-Side Implementation Details

| Component | Responsibility | Technical Notes |
| :--- | :--- | :--- |
| **Auth Store (Pinia)**| Global state for token, user details, and authentication status. | Store the JWT in **Session Storage** or an **HTTP-only Cookie** (preferred for security). **Do NOT use Local Storage.** |
| **HTTP Interceptor**| Security layer for all API communication. | Automatically inject the saved JWT into the `Authorization: Bearer <token>` header for every protected route call. |

## III. Feature: User Preferences and Cognitive Configuration

### 3.1 Database Schema Additions

A new table, `user_preferences`, is required to store user-specific cognitive configuration, secured by RLS.

| Table | RLS Policy | Columns and Constraints |
| :--- | :--- | :--- |
| `user_preferences` | **Mandatory** using `user_id = get_current_user_id()`. | `user_id` (UUID, PK, FK to `users`); `advisor_name_spiritual` (VARCHAR); `spiritual_mode` (VARCHAR, CHECK IN 'TAROT', 'GOD', 'NEUTRAL'); `spiritual_tone` (VARCHAR, CHECK IN 'GUIDANCE', 'MENTOR', 'EXPERT'); `health_data_ingestion` (VARCHAR, CHECK IN 'APPLE_HEALTH', 'DIRECT_DB'). |
| `cognitive_definitions` | **NONE** (Global Data) | `definition_key` (VARCHAR, PK); `advisor_role` (VARCHAR, e.g., 'CULTIVATE'); `system_prompt_template` (TEXT); `version` (INT). *Note: This table is read-only for the Engine; it is managed by an Administration service, not the App or Engine.* |

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

### 3.3 Client-Side Implementation: Preferences Screen

| Component | Responsibility | Technical Notes |
| :--- | :--- | :--- |
| **Preferences Store (Pinia)**| Manages the state of the preferences object. | Fetch data on mount of the settings route. Use optimistic updates upon patch requests. |
| **UI Components** | Input fields for names, radio groups/dropdowns for modes and tones. | Implement using **Tailwind CSS** for responsive design (mobile-first primary). Ensure validation matches database constraints (e.g., for Spiritual Mode choices). |
| **HTTP Requests** | `GET` on load, `PATCH` on save/change. | Must use the authenticated HTTP Interceptor to ensure JWT is passed. |

### IV. Feature: Professional Collaboration & Secure Sharing (NEW)

The App Service mediates all consent and access management (via the `data_access_grants` table) to ensure RLS is correctly enforced by the database.

#### 4.1 API Contracts (App Service - `app/api/v1/data-grants`)

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/data-grants/grant` |
| **Method** | POST |
| **Authentication** | Required (JWT for Primary User) |
| **Purpose** | Primary User grants granular access to a Professional. |
| **Request Body** | `professional_email`: string (The target professional's account), `access_scope`: JSONB (defines the data types/time window permitted). |

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/data-grants/revoke/{professional_user_id}` |
| **Method** | POST |
| **Authentication** | Required (JWT for Primary User) |
| **Purpose** | Primary User immediately revokes access. Revocation updates the `revoked_at` timestamp in the database, instantly denying RLS-controlled access. |
| **Request Body** | N/A |

#### 4.2 API Contracts (Engine Service Proxy - `engine/api/v1/professional-synthesis`)

| Property | Value |
| :--- | :--- |
| **Endpoint** | `POST /api/v1/professional-synthesis` |
| **Method** | POST |
| **Authentication** | Required (JWT for **Professional User**). |
| **Purpose** | Professional requests a holistic synthesis report for their linked client (Primary User). |
| **Request Body** | `client_user_id`: UUID (The UUID of the client), `query_context`: string (The professional's question, e.g., "Analyze their sleep patterns for the last 90 days"). |
| **Engine Action** | The Engine performs the full Cognitive Synthesis. Data retrieval is strictly filtered by the RLS policy, which checks the professional's `access_scope` in `data_access_grants` to ensure only consented data is used in the synthesis. |
| **Success Response** | Returns the synthesized, consent-filtered holistic report (e.g., JSON or TEXT). |
