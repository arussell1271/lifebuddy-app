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
