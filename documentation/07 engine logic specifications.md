# 🧠 Cognitive Engine Logic Specification (The Brain)

**File Path:** 07 engine logic specification.md
**Audience:** Full-Stack Engineers, AI/ML Engineers, Product Leadership (for core IP).

---

## I. Purpose: Mapping Hypothesis to Implementation

This document translates the philosophical goals (H1, H2, H3 from `01 project definition.md`) into concrete, deterministic logic for the Cognitive Engine service.

---

## II. Cultivate Synthesis Logic (The Dream/Journal Analysis)

The Engine's primary function is to perform a **Synthesis** by analyzing all user data since the last synthesis to identify misalignments.

### A. Dream/Journal Analysis

The Engine MUST use the internal LLM (`ollama`) and vector similarity search (against `documents` table) to perform the following:

1. **Input:** All new `document_type='DREAM'` and `document_type='JOURNAL'` entries.
2. **Steps:**
    * **LLM Task:** Extract the **dominant emotion** and **core subconscious theme** (e.g., 'Lack of self-worth', 'Fear of commitment', 'Spiritual drift').
    * **Vector Query:** Compare the extracted theme vector against the **User's Historical Synthesis Store** (via `synthesis_log` table) to establish a **Disalignment Frequency Count** (DFC).
    * **Logic:**
        * If the DFC for a theme is **> 3** in the last 7 days, classify the finding as **"Limiting Subconscious Misalignment."**
        * If the DFC for a theme is **> 5** in the last 14 days, classify the finding as **"Spiritual Disalignment"** (a severe, sustained pattern).

### B. H2 Validation Logic: Non-Adherence Prediction

This logic fulfills Hypothesis H2: predicting non-adherence 3-5 days in advance.

1. **Input:** Current Disalignment Frequency Count (DFC) and the user's `user_cognitive_state`.
2. **Logic:**
    * **IF** (New Synthesis contains **Limiting Subconscious Misalignment**)
    * **AND** (The user's 7-day adherence rate to **HOLISTIC** items is **< 70%**)
    * **THEN** The Engine **MUST** log a state prediction to `user_cognitive_state` with `prediction_type='NON_ADHERENCE'` and `prediction_confidence=HIGH`.
3. **App Service Action:** The App Service will poll the `user_cognitive_state` table. If this prediction is present, the App **MUST** inject a supportive intervention message into the chat UI.

---

## III. Execute Phase: Actionable Item Generation

The Engine must convert the **Cultivate Synthesis** into a concrete **Holistic Actionable Item**.

### A. Holistic Item Generation (H1 Focus)

1. **Prerequisite:** A "Limiting Subconscious Misalignment" must have been identified in the Synthesis (Section II.A).
2. **LLM Task:** The Engine provides the LLM (`ollama`) with the **Synthesis** and the **User's Identity Store** (`users.identity_statement`).
3. **Prompt Instruction (Simplified):** "Generate one concise, specific Actionable Item whose completion directly contradicts the Limiting Subconscious Misalignment, and is framed as an act that reaffirms the User's Identity Statement. The item type MUST be 'HOLISTIC'."
4. **Output:** The generated Item is saved to the `actionable_items` table with `item_type='HOLISTIC'` and `status='PENDING'`.

### B. Mandated Item Generation (Health Focus)

1. **Prerequisite:** New `health_metrics` or `daily-check` data (e.g., a low sleep score or high RHR).
2. **LLM Task:** The Engine provides the LLM (`ollama`) with the **new health data** and the **current item set**.
3. **Prompt Instruction (Simplified):** "Generate one concise, behavioral Actionable Item to address the worst health metric (e.g., 'Go to bed 30 minutes earlier'). The item type MUST be 'MANDATED'."
4. **Output:** The generated Item is saved to the `actionable_items` table with `item_type='MANDATED'` and `status='PENDING'`.

## IV. Engine Core Service Mandates 🛡️

### A. RLS Context Initialization (CRITICAL SECURITY STEP)

The Engine Service MUST ensure that for every synchronous API call received via the `/api/v1/data-proxy/{user_id}/{engine_route}` endpoint, the following steps are performed **sequentially and transactionally** before any database business logic is executed:

1. **Validate User ID:** Verify the integrity and format of the `user_id` received from the App Service.
2. **Establish RLS Connection:** Establish a new, dedicated database connection using **Role 2 (`cognitive_engine_rls`)**.
3. **Execute Session Setup:** Execute the SQL command to enable RLS filtering for the current session: `SET app.current_user_id = '<<user_id from API>>';`
4. **Execute Business Logic:** Proceed to execute the core Engine logic required by the `engine_route` (e.g., retrieving documents, logging adherence).
5. **Connection Management:** Close the connection immediately upon completion of the request.

This process ensures all data access is strictly limited by the database's RLS policy to the user specified in the session context, maintaining the **PoLP** standard.

## V. Asynchronous Job Polling Contract (CRITICAL) ⏱️

For all asynchronous jobs (e.g., Synthesis, Report Generation) initiated by the App Service through the `message-broker`, the client/App must poll this endpoint for status updates and results.

| Property | Value |
| :--- | :--- |
| **Endpoint Pattern** | `GET /api/v1/jobs/{job_id}` |
| **Method** | GET |
| **Authentication** | Required (Internal JWT/Shared Secret for App-to-Engine communication). |
| **Engine Service Action** | 1. Query Redis (via `message-broker`) using the `job_id`. 2. Return the current job status and the resulting data/location if complete. |
| **Success Response (Pending)** | `200 OK` / `{"status": "PROCESSING", "progress": 55, "message": "Analyzing dream documents..."}` |
| **Success Response (Complete)** | `200 OK` / `{"status": "COMPLETE", "result_uri": "/api/v1/synthesis-report/{job_id}", "message": "Report is ready."}` |
| **Failure Response** | `500 Internal Error` / `{"status": "FAILED", "error": "LLM returned un-parseable output."}` |

## V. Asynchronous Job Polling Contract (CRITICAL) ⏱️

For all asynchronous jobs (e.g., Synthesis, Report Generation) initiated by the App Service through the `message-broker`, the client/App must poll this endpoint for status updates and results.

| Property | Value |
| :--- | :--- |
| **Endpoint Pattern** | `GET /api/v1/jobs/{job_id}` |
| **Method** | GET |
| **Authentication** | Required (Internal JWT/Shared Secret for App-to-Engine communication). |
| **Engine Service Action** | 1. Query Redis (via `message-broker`) using the `job_id`. 2. Return the current job status and the resulting data/location if complete. |
| **Success Response (Pending)** | `200 OK` / `{"status": "PROCESSING", "progress": 55, "message": "Analyzing dream documents..."}` |
| **Success Response (Complete)** | `200 OK` / `{"status": "COMPLETE", "result_uri": "/api/v1/synthesis-report/{job_id}", "message": "Report is ready."}` |

---

### V.1. Client-Side Polling Mitigation Strategy (MANDATORY) ⚠️

To prevent network strain and denial-of-service risks due to excessive polling, the client (Vue 3/Pinia) **MUST** implement an **Exponential Backoff** strategy for polling the job status endpoint.

| Parameter | Standard | Rationale |
| :--- | :--- | :--- |
| **Initial Delay** | `1000ms` (1 second) | Provides a quick initial check. |
| **Backoff Multiplier** | `1.5` | Exponential increase in wait time. |
| **Maximum Delay** | `15000ms` (15 seconds) | Prevents polling from becoming too slow for the user experience. |
| **Max Retries** | `60` | Caps the total polling time for an extremely long job (e.g., 15 minutes max). |

**Polling Wait Calculation:** `Delay(n) = min(Initial Delay * (Backoff Multiplier ^ n), Maximum Delay)`
