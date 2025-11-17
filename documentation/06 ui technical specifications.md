# ⚙️ UI Technical Specification: The Holistic Cognitive Data Engine

**File Path:** 06 ui technical specifications.md
**Audience:** Full-Stack Engineers, Backend Developers, UI Developers.

---

## 💡 Instructions for Use

1. **Scope:** Defines the technical implementation, required **FastAPI API Contracts** on the App Service, client-side state management, and the overall front-end architecture.
2. **Adherence:** Must strictly conform to the **App/Engine Service Separation** and the **Asynchronous Processing Flow** constraint.
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

#### B. Request Password Reset (App-to-Engine Asynchronous Delegation)

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
