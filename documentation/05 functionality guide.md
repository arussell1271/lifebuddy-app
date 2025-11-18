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
