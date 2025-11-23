# 📘 Functional Guide: The Holistic Cognitive Data Engine

**File Path:** 05 functionality guide.md
**Audience:** Product Managers, UI/UX Designers, Quality Assurance (QA).

---

## 💡 Instructions for Use

1. **Scope:** Defines the intended user behaviour, business logic, and high-level interaction models for the client application.
2. **Constraint (CRITICAL):** Must **NEVER** mention specific technical details like **API endpoints, database tables (e.g., `users`, `health_metrics`),** or backend service logic (App/Engine).
3. **Goal:** Serves as the single source of truth for user flows and acceptance criteria for all features.

---

## Feature: User Authentication & Onboarding

### 1.1 Login Screen

**User Goal:** Access their personalized data securely.

| Element | Functional Requirement / Business Rule | UX & Interaction Details |
| :--- | :--- | :--- |
| **Login Form** | Requires a valid Username (or Email) and a Password from the **User Identity Store**. | Form submission is disabled until both fields are non-empty. |
| **Password Visibility** | Must allow the user to view the password for verification. | A visible 'eye' icon must appear next to the password field, toggling the input mask. |
| **Failed Login** | If credentials validation fails. | Display a generic, temporary error message: "Invalid username or password. Please try again." |
| **Account Recovery Links**| Provides pathways for account recovery and creation. | Must clearly present three separate, functional links: **"Forgot Password?"**, **"Forgot Username?"**, and **"Create Account"** |

### 1.2 User Registration

**User Goal:** Create a secure, unique account to begin their personalized health journey.

| Element | Functional Requirement / Business Rule | UX & Interaction Details |
| :--- | :--- | :--- |
| **Registration Form** | Requires a unique **Email**, a unique **Username**, and a **Password** (with confirmation). The system validates uniqueness against the **User Identity Store**. | User input validation must occur on the client side (e.g., password strength). |
| **Post-Registration** | Upon successful creation, the user must be immediately authenticated and seamlessly redirected to the application dashboard. | No intermediary screens; minimal friction onboarding. |

### 1.3 Account Recovery Flows

**Business Rule:** The system must prevent user enumeration in all recovery requests.

#### A. Forgot Password Flow

* **Step 1: Request**: User submits their email address.
* **System Response**: The system must instantly display a confirmation message, *regardless of whether the email exists*: "If a matching account is found, a password reset link will be sent to your email shortly."

#### B. Forgot Username Flow

* **Step 1: Request**: User submits their email address.
* **System Response**: The system must instantly display a confirmation message, *regardless of whether the email exists*: "If a matching account is found, your Username will be sent to your email shortly."

---

## Feature: Personalized Cognitive Configuration

### 2.1 Advisor Naming and Personas (CULTIVATE, EXECUTE, CONTRIBUTE)

**User Goal:** Customize the language and perceived identity of the Cognitive Engine's sub-modules to enhance personal resonance and adherence.

| Element | Functional Requirement / Business Rule | UX & Interaction Details |
| :--- | :--- | :--- |
| **Custom Name Input** | The user must be able to change the name associated with the **Cultivate Advisor**, the **Execute Advisor**, and the **Contribute Advisor**. | Default names are *The Cultivator*, *The Executor*, and *The Contributor*. Names must be displayed in the relevant sections of the app. |
| **Spiritual Mode** | The Cultivate Advisor (Brain) must adopt a logic persona based on the user's selection: **Neutral**, **Tarot**, or **God/Spiritual**. | A single-choice selector (e.g., radio buttons or dropdown) is required for the user to select one mode. This dictates the interpretation context for **Dream Analysis** and **Journaling**. |
| **Communication Tone** | The Cultivate Advisor's text generation (outputs) must adhere to the user's selected tone: **Guidance**, **Mentor**, or **Expert**. | **Guidance/Mentor:** Flexible, empathetic, and open to discussion. **Expert:** Definitive, authoritative, and direct in delivery. |

---

### 2.2 Health Data Ingestion Configuration (CONTRIBUTE)

**User Goal:** Define the primary source for clinical and health metric data to feed the **Contribute** component.

| Element | Functional Requirement / Business Rule | UX & Interaction Details |
| :--- | :--- | :--- |
| **Health Data Source** | The user must select where the system sources its health metrics (`RHR`, `SLEEP_SCORE`, etc.). | The selection must be between **External App Synchronization** (e.g., Apple Health) or **Direct Entry** into the application's log. |
| **Synchronization Status** | If "External App Synchronization" is chosen, the UI must provide a read-only status (e.g., "Last Synced: 2 hours ago"). | This status should reflect the last successful data pull timestamp. |

---

### 2.3 Dynamic Cognitive Artifacts (The Brain's Configuration Principle)

**Business Goal:** The system must allow administrators to define and modify the core instructions and personalities for all cognitive advisors without deploying new code.

| Element | Functional Requirement / Business Rule | Contextual Rule |
| :--- | :--- | :--- |
| **Advisor Role Templates** | Each core advisor must have a base, non-user-specific definition that outlines its core purpose and persona. | This defines the 'default' identity for the advisor. |
| **Preference Modifiers** | The system must define specific *modifier* templates that activate based on user selections in the **User Preferences** screen (e.g., Spiritual Mode, Tone). | These modifiers are dynamically applied by the Cognitive Engine during **Cognitive Synthesis**. |
| **Dynamic Assembly Mandate** | The App Service (The Body) must **NEVER** contain or access the proprietary content of the Advisor Role Templates or Preference Modifiers. The App only manages the user's selection (e.g., "TAROT"), and the Engine retrieves the corresponding proprietary instructions based on that selection. | This strictly enforces the **App/Engine separation**, protecting the proprietary instructional content. |

### 2.4 Cognitive Personalization (The User's Engine Control)

**Business Goal:** Allow Primary Users to customize the synthesis logic, controlling which advisors interact and how data is weighted, to create a powerful, bespoke cognitive co-pilot.

| Element | Functional Requirement / Business Rule | Contextual Rule |
| :--- | :--- | :--- |
| **Advisor Interaction Control** | The user must be able to explicitly select which secondary data sources (Cultivate, Execute, Contribute) are considered by the primary advisor during a Holistic Query. | The user can mandate that the Health Advisor use Dream Analysis but *exclude* Spiritual (Tarot/Journaling) data from its synthesis. |
| **Data Weighting Control** | The user must be able to specify granular retrieval criteria (quantity, recency, relevance) for each enabled data source. | The user can specify: "Retrieve the **Top 4** most semantically relevant Dream entries," or "Only include the **Most Recent** Tarot Reading," or "Use **Zero** data points from the Health Insights source." |
| **Configuration Persistence** | All custom advisor interaction and weighting settings must be saved to the user's profile and automatically applied to all subsequent Holistic Queries until changed. | This ensures a consistent, personalized cognitive experience across all client sessions. |

### 2.5 Professional Portal Access & Report Generation

**Business Goal:** Provide Secondary Users (Professionals) a dedicated, secure interface to analyze client data within the scope of the Primary User's active consent.

| Element | Functional Requirement / Business Rule | UX & Interaction Details |
| :--- | :--- | :--- |
| **Professional Authentication** | Upon successful login, the Professional must be directed immediately to a **Dedicated Portal** view. | This view replaces the standard Cultivate/Execute/Contribute user dashboard for this role. |
| **Client List Visibility** | The portal must display a searchable, paginated list of clients who have granted **active, un-revoked consent** to the logged-in Professional. | No inactive or un-consented clients are visible to maintain security. |
| **Report Request** | The Professional must be able to select a client and submit a **Synthesis Query** (e.g., "Analyze adherence trends for the last quarter"). | This triggers the asynchronous Engine process. |
| **Asynchronous Response** | After submitting the query, the Professional will receive an immediate confirmation that the report request has been initiated, and they must be directed to a **Report History** or **Notification** section to retrieve the final report when completed. | The interface must never wait synchronously for the complex analysis to complete. |

### 2.6 Professional Collaboration & Secure Sharing

**Business Goal:** Empower the Primary User to selectively share their full historical (Conscious, Unconscious, and Actionable) data with vetted Secondary Users (doctors, dieticians, researchers) to facilitate advanced collaborative care.

| Element | Functional Requirement / Business Rule | Contextual Rule |
| :--- | :--- | :--- |
| **Granular Consent Interface** | The Primary User must have a clear interface to grant or revoke access, defining the **exact scope** of data the Professional can view (e.g., only Health Metrics, all data, or only data after a specific date). | Access must be based on a time-bound or data-type-bound consent that can be **immediately revoked** by the user via a single action. |
| **Professional Pre-Analysis Report** | The Secondary User (Professional) must access a dedicated Portal where they can request a **Cognitive Synthesis Report** for their linked client (Primary User). | This report leverages the system's core analytical capabilities to show **subconscious blocks, adherence patterns, and correlation themes** derived from the client's historical data, delivered *prior* to a physical appointment. |
| **Data Sovereignty Mandate** | The system must guarantee that any data requested by the Professional is filtered according to the user's current, active consent rules. | If the user revokes consent, the Professional's access is instantly terminated. |

### 2.6 System Effectiveness Monitoring

**Business Goal:** The system must continuously track and validate the core hypotheses (H1, H2, H3) to provide empirical evidence of the system's value and guide future development.

| Element | Functional Requirement / Business Rule | Contextual Rule |
| :--- | :--- | :--- |
| **Hypothesis Tracking (H2)** | The system must run scheduled, background processes to calculate the **prediction accuracy** of Cultivate data (Dream/Spiritual themes) in forecasting Execute failures (Actionable Item non-adherence) within a defined future window (e.g., 3-5 days). | This process provides quantitative evidence of the system's ability to identify unconscious behavioral blocks. |
| **Holistic Outcome Metering (H3)** | The system must calculate and log the overall user adherence rate to **Holistic Actionable Items**, correlating it with positive changes in clinical/health markers (Contribute data). | This metric provides the longitudinal evidence required to demonstrate the system's effectiveness for sustained change. |
| **Internal Research Data** | The aggregate system effectiveness metrics must be stored in a dedicated, **anonymized** research data store separate from individual user content. | This data store is used for internal analysis, not for user-facing features, ensuring separation of research and user data. |

### 3.1 Cognitive Advisor Chat Flow (Updated with Daily State Management) 🧠

**User Goal:** Engage with the system's personalized advisors for guidance and insight.

| Element | Functional Requirement / Business Rule | UX & Interaction Details |
| :--- | :--- | :--- |
| **Daily Cognitive Check (CRITICAL)** | On the **first interaction of the day** with an advisor, the system must perform a check against the `user_cognitive_state` table to ensure all mandatory **Pre-Analysis Questions** are answered for the current day. This is a **hard block** to the main chat function. | The main chat input field is disabled and replaced by a prompt to complete the daily check, presenting the unanswered questions sequentially using the `expected_format`. |
| **Dynamic Question Set** | Questions are loaded based on the current context and the Advisor Type from the `pre_synthesis_questions` table. | Examples: "What time did you go to bed last night?" (EXECUTE), or "What was the dominant feeling in your dream?" (CULTIVATE). |
| **Question Persistence** | Questions are tracked **per user, per day**. Once answered (status is `ANSWERED_EXPLICIT` or `ANSWERED_IMPLICIT`), the check is complete for that calendar day. | If a user answers a question via the check form, the status is set to `ANSWERED_EXPLICIT`. |
| **Implicit Completion (Engine Responsibility)** | The **Cognitive Engine** must analyze the new user input against the `PENDING` questions in `user_cognitive_state`. If an answer is sufficiently identified in the text (even if the user is asking for clarification), the Engine must update the state status to `ANSWERED_IMPLICIT`. | This allows the user's flow to proceed naturally if they provide the necessary data in conversation. |
| **Response Synthesis** | The full synthesis is only initiated when the daily check status is confirmed as **COMPLETE**. The final synthesis payload must include all collected daily answers for context. | The App Service uses the `/daily-check-status` API to determine if it can proceed to initiate the job. |
