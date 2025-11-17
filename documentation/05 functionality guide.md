# 📘 Functional Guide: The Holistic Cognitive Data Engine

**File Path:** 05 functionality guide.md
**Audience:** Product Managers, UI/UX Designers, Quality Assurance (QA).

---

## 💡 Instructions for Use

1. **Scope:** Defines the intended user behavior, business logic, and high-level interaction models for the client application.
2. **Constraint:** Must **NEVER** mention specific technical details like API endpoints, database tables, or backend service logic (App/Engine).
3. **Goal:** Serves as the single source of truth for user flows and acceptance criteria for all features.

---

## Feature: User Authentication & Onboarding

### 1.1 Login Screen

**User Goal:** Access their personalized data securely.

| Element | Functional Requirement / Business Rule | UX & Interaction Details |
| :--- | :--- | :--- |
| **Login Form** | Requires a valid Username (or Email) and a Password from the **`users`** table. | Form submission is disabled until both fields are non-empty. |
| **Password Visibility** | Must allow the user to view the password for verification. | A visible 'eye' icon must appear next to the password field, toggling the input mask. |
| **Failed Login** | If credentials validation fails. | Display a generic, temporary error message: "Invalid username or password. Please try again." |
| **Account Recovery Links**| Provides pathways for account recovery. | Must clearly present two separate, functional links: **"Forgot Password?"** and **"Forgot Username?"** |

### 1.2 Forgot Password Flow (Recovery)

**Business Rule:** The system must use a secure, time-limited token delivered via email to allow a password change.

* **Step 1: Request**: User submits their email address.
* **System Response**: The system must instantly display a confirmation message, *regardless of whether the email exists*, to prevent user enumeration: "If a matching account is found, a password reset link will be sent to your email shortly."
