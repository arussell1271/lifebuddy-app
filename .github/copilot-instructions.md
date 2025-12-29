# AI Coding Agent Instructions: Life Buddy

## Architecture Overview

**Life Buddy** is a dual-service system: a public-facing **Application (The Body)** and a proprietary **Cognitive Engine (The Brain)**, implementing the **Cultivate → Execute → Contribute** framework for behavioral health.

### Deployment Stage & Mobile Access

**Current (MVP)**:
- Responsive web application (Vue 3) accessible via browser and mobile browsers
- Web platform serves desktop, tablet, and mobile devices through responsive design (Tailwind CSS)
- Direct health data entry only (via web form)

**Future Phases**:
- Native iOS app (SwiftUI) calling same `app:8000` API
- Native Android app (Kotlin) calling same `app:8000` API
- Apple Health / Android Health Connect integration for automated data ingestion

**Monetization**: Free with ads (future billing/tier structure TBD)

### Service Separation (Strict Principle of Least Privilege)

- **App Service** (`app/`, port 8000): Public FastAPI service. Handles authentication, CRUD, UI APIs. **Cannot** directly access the database or LLM.
- **Engine Service** (`engine/`, port 8001): Internal FastAPI service. Handles AI/LLM logic, proprietary synthesis, database operations. **Only** communicates via internal API.
- **Networks**: `frontend-network` (App/Client) and `core-network` (Engine/DB/LLM/Redis). Network isolation is enforced by Docker.

### Critical Communication Pattern

- **Synchronous**: App ↔ Engine for auth, config retrieval, and real-time queries (via `cognitive-engine:8001`).
- **Asynchronous**: App queues jobs via **Redis** (`message-broker:6379`), Engine polls and processes, returns `job_id` for client polling.
- **Never**: App → Database directly. App → LLM directly.

---

## Essential Files & Data Flows

### Schema & Security
- [Database Schema`documentation/03 db_schema.sql` - Defines RLS policies, user roles, and tables. **Key**: `cognitive_engine_full` (admin) and `cognitive_engine_rls` (enforces RLS).
- [Infrastructure Setup`documentation/02 infratructure setup.md` - Network isolation, port mappings, mandatory env vars (JWT_SECRET_KEY, JWT_ALGORITHM, APP_SECRET_KEY).

### Execution & Patterns
- [Standards Guide`documentation/04 standards guide.md` - Naming conventions, service responsibilities, RLS dual-mode enforcement, JSON serialization for `*_json` fields, 4-day data retention.
- [UI Technical Specs`documentation/06 ui technical specifications.md` - API contracts, async job pattern, RLS enforcement in endpoints.

### Configuration
- `.env.dev` / `.env.prod`: Environment variables (never commit secrets).
- `docker-compose.yml` / `lifebuddy-app.yml`: Service orchestration. Use `--profile dev` or `--profile prod`.

---

## Development Workflows

### Build & Run
```powershell
# Development startup
docker compose -f lifebuddy-app.yml --profile dev up --build

# Production startup
docker compose -f lifebuddy-app.yml --profile prod up --build

# Stop services (preserves volumes)
docker compose stop

# Clean shutdown (removes containers)
docker compose down --remove-orphans
```

### Scripts
- [docker_manager.ps1`scripts/docker_manager.ps1`: PowerShell wrapper for compose commands (rebuild, stop, pull_mistral).
- [docker_transfer.ps1`scripts/docker_transfer.ps1`: Volume and data transfer utilities.

### Testing & Debugging
- Check logs: `docker logs <service-name>`
- Database access: `psql -h localhost -U lifebuddy_rw -d postgres` (dev mode).
- Engine API direct testing: `http://localhost:8001/docs` (Swagger UI).
- App API: `http://localhost:8000/docs`.

---

## Documentation & Verification Workflows (MANDATORY)

### Developer Responsibility: Keep Docs in Sync ✅

**CRITICAL MANDATE**: All code changes MUST be accompanied by documentation updates. The codebase is only considered "finalized" when BOTH code AND documentation are validated and error-free.

### During Development (After Each Feature)

1. **Update Relevant Documentation Files**
   - If modifying API endpoints → Update `documentation/06 ui technical specifications.md`
   - If changing database schema → Update `documentation/03 db_schema.sql`
   - If modifying synthesis logic → Update `documentation/07 engine logic specifications.md`
   - If adding new error codes → Update `documentation/04 standards guide.md`

2. **Update Copilot Instructions (If Architecture Changes)**
   - Major changes to service responsibilities? → Update this file (.github/copilot-instructions.md)
   - New patterns or conventions? → Add to Code Patterns section

3. **Update Summary Files** (in `summaries/` directory)
   - Update `summaries/README_DOCUMENTATION.md` to reflect new docs or changes
   - Update `summaries/IMPLEMENTATION_READY.md` with current status
   - Use these as your checklist—check off each item as it's implemented

### Before Finalizing Code (Pre-Commit Checklist)

**VERIFICATION STEP 1: Error Check**
```powershell
# In VS Code, open the Problems panel (Ctrl+Shift+M)
# Verify: 0 errors shown (all green checks)
# If errors appear, fix them before committing
```

**VERIFICATION STEP 2: Documentation Validation**
- [ ] All links in documentation are valid (check via VS Code Go-to-Definition)
- [ ] No broken cross-references between docs
- [ ] All code examples are up-to-date
- [ ] All error codes mentioned in code are documented in standards guide

**VERIFICATION STEP 3: Summaries Review** (Your Quality Gate!)
1. Open `summaries/IMPLEMENTATION_READY.md`
   - Is the feature you built listed? ✅
   - Is the status accurate? ✅
   
2. Open `summaries/README_DOCUMENTATION.md`
   - Are all related documentation files listed? ✅
   - Are the links working? ✅

3. Run error check one final time
   - Execute: `Ctrl+Shift+M` (open Problems panel)
   - Verify: "No errors found" message ✅

**VERIFICATION STEP 4: Git Pre-Commit Hook** (Automated)
```powershell
# Before committing, the system SHOULD check:
# 1. No markdown errors in /documentation and /summaries
# 2. All referenced files exist
# 3. No %20 or other encoding issues in links
# (Future: implement pre-commit hook for this)
```

### Quarterly Documentation Audit

Review all documentation quarterly to ensure it reflects the current system:
- Check `documentation/DOCUMENTATION_MANIFEST.md` for outdated entries
- Verify all API endpoints in `documentation/10 engine api reference.md` match code
- Review database schema for changes not reflected in `documentation/03 db_schema.sql`
- Update copilot-instructions.md with any architectural lessons learned

### Summary Files as Living Checklists

The files in `summaries/` are NOT static reports—they are **active verification tools**:

| File | Use Case | When to Check |
|------|----------|---------------|
| `IMPLEMENTATION_READY.md` | Feature completion checklist | Before each commit, mark completed items |
| `README_DOCUMENTATION.md` | Documentation completeness | Before release, verify all areas documented |
| `DELIVERY_SUMMARY.md` | What was built | At feature milestone reviews |
| `PROBLEMS_FIXED_REPORT.md` | Known issues & solutions | When similar errors occur during development |
| `SOLUTION_SUMMARY.md` | Quick troubleshooting reference | When debugging problems |

---

## Code Patterns & Conventions

### Naming
- **Variables/Functions**: `snake_case` (e.g., `calculate_adherence_rate`).
- **Classes**: `PascalCase` (e.g., `User`, `AdherenceService`).
- **Database**: `snake_case` tables/columns (e.g., `adherence_log`).
- **API Routes**: `kebab-case` paths (e.g., `/api/v1/action-items`).
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `ITEM_TYPE_HOLISTIC`).

### Service Responsibilities
| Service | Dependencies | Database Role | Network |
|---------|--------------|---------------|---------|
| **App** | FastAPI, Pydantic, httpx (Engine calls), redis, python-jose | `lifebuddy_rw` (read/write safe tables, **no vectors**) | `frontend-network` + `core-network` (internal only) |
| **Engine** | FastAPI, psycopg2, pgvector, langchain, ollama, rq | `cognitive_engine_full` (admin) + `cognitive_engine_rls` (live queries) | `core-network` only |

### RLS Enforcement (Non-Negotiable)
- All user-owned data access **must** enforce RLS: `current_setting('app.current_user_id')::uuid`.
- Use `get_rls_session(user_id)` context manager in Engine for **all** live user data.
- The Engine **never trusts** the user; it trusts the App's JWT validation and sets the session context.
- `data_access_grants` table enables secondary user access (e.g., doctors) with granular `access_scope` JSONB field.

### JSON Serialization (`*_json` Fields)
- Fields like `actionable_items.data_json` store stringified JSON.
- **App** treats as **opaque** (passes through); **Engine** validates, serializes, deserializes.
- Prevents silent data corruption and maintains integrity.

### Data Retention
- `user_cognitive_state`: 4-day rolling window (nightly purge via stored procedure).
- `pre_synthesis_answers`: 4-day rolling window (aligned with cognitive state).

---

## JWT & Authentication Flow

### Token Claims (Mandatory)
```json
{
  "sub": "user-uuid",      // User ID from users table
  "aud": "life-buddy-app",  // Audience
  "iat": 1234567890,        // Issued At
  "exp": 1234671490         // Expiration
}
```

### App-to-Engine Auth Endpoints
- `POST /auth/login`: App forwards username/password, Engine hashes/validates, returns JWT.
- `POST /auth/register`: App forwards email/username/password, Engine creates user.
- **ALWAYS** synchronous (no async queue for auth).

### Async Job Pattern
1. **Initiate**: `POST /api/v1/synthesis/job` → App queues on Redis, returns `job_id` (202 Accepted).
2. **Poll**: `GET /api/v1/synthesis/job/{job_id}` → App queries Redis for status.
3. **Retrieve**: `GET /api/v1/synthesis/{synthesis_id}` → RLS-protected query from database.

---

## Hypothesis Tracking (Core to Engine Logic)

All Engine logic targets validation of:
- **H1**: Identity-focused (holistic) items yield better adherence than action-only items.
- **H2**: Unconscious/spiritual misalignment predicts non-adherence 3–5 days ahead.
- **H3**: Cultivate→Execute→Contribute path improves adherence to 80%.

The `cognitive_efficacy_metrics` table must track these metrics continuously.

---

## RAG System & Advisor Architecture

### Vector Storage & Retrieval
- **`document_vectors` table**: Stores embeddings (pgvector/1536d) for all `documents` entries (DREAM, SPIRITUAL, QNA_USER).
- **Engine RAG Workflow**: For synthesis, Engine performs vector similarity search to retrieve semantically relevant historical documents.
- **Use Case**: When analyzing new dreams, Engine compares extracted themes against historical vectors to calculate **Disalignment Frequency Count (DFC)**.
- **Security**: `document_vectors` is RLS-enforced; only the Engine (`cognitive_engine_full` for admin tasks, `cognitive_engine_rls` for user queries) accesses vectors via `user_id` filtering.

### Three Advisors (Cognitive Definitions)
Each advisor is a composition of **base role template** + **preference modifiers**:

| Advisor | CULTIVATE Phase | EXECUTE Phase | CONTRIBUTE Phase |
|---------|-----------------|---------------|------------------|
| **The Cultivator (Dream/Spiritual)** | Dream analysis + Spiritual mode (TAROT/GOD/NEUTRAL) + Tone (GUIDANCE/MENTOR/EXPERT) | N/A | N/A |
| **The Executor (Action/Habit)** | N/A | Actionable item generation (HOLISTIC vs. MANDATED) | N/A |
| **The Contributor (Health)** | N/A | N/A | Health metric synthesis (RHR, SLEEP_SCORE, etc.) |

- **`cognitive_definitions` table**: Stores system prompts, role templates, and mode-specific modifiers (e.g., `CULTIVATE_MODE_TAROT`).
- **Non-RLS**: This table is global config; Engine's `cognitive_engine_full` role manages it.
- **Customization**: User selections (e.g., `spiritual_mode='TAROT'`) in `user_preferences` dynamically inject modifiers into LLM prompts.

### Admin Prompt Management & User Customization

**System Prompts (Admin-Only)**:
- Only **admins** can modify `cognitive_definitions` table via direct DB access or future admin dashboard.
- Changes require Engine restart or cache invalidation to take effect.

**User Custom Questions**:
- Users add advisor-specific questions via `/api/v1/user-preferences/custom-questions` (POST/PATCH).
- Storage: `user_preferences.custom_advisor_questions` (JSONB, max 3 questions per advisor).
- Integration: Engine appends user custom questions to system prompts during synthesis: *"Please also consider the user's specific focus areas: [custom_questions]"*.

**Preferences Screen** (Unified Management):
Users manage all advisor/theme settings from single preferences panel:
- Color scheme/theme selection
- Advisor name customization (default: "The Cultivator", "The Executor", "The Contributor")
- Spiritual mode (TAROT/GOD/NEUTRAL)
- Communication tone (GUIDANCE/MENTOR/EXPERT)
- Custom advisor questions (add/edit/delete per advisor type)

### Synthesis Matrix (User-Controlled Advisor Weighting)
- **`user_preferences.synthesis_matrix` (JSONB)**: User defines which advisors interact and how data is weighted.
- **Engine Interpretation**: During synthesis, Engine respects the matrix to prioritize/exclude data sources.
- **Example**: `{"cultivate_enabled": true, "cultivate_weight": 0.6, "execute_weight": 0.3, "contribute_weight": 0.1}`.
- **See**: [04 standards guide.md`documentation/04 standards guide.md` (JSON Serialization Standard).

### Daily Cognitive Check (Gating Mechanism)
- **`pre_synthesis_questions` table**: Global, non-RLS list of mandatory questions for CULTIVATE/EXECUTE/CONTRIBUTE phases.
- **`user_cognitive_state` table**: Tracks daily completion status (PENDING → ANSWERED_EXPLICIT/ANSWERED_IMPLICIT).
- **`pre_synthesis_answers` table**: Stores user responses with 4-day retention.
- **Flow**: App blocks main chat until all questions for the day are answered → Engine can then synthesize.
- **Implicit Completion**: Engine analyzes incoming chat text to auto-mark questions answered (if user mentions "I slept 6 hours" in conversation).
- **See**: [06 ui technical specifications.md`documentation/06 ui technical specifications.md` (Daily Check Flow) and [07 engine logic specifications.md`documentation/07 engine logic specifications.md` (Synthesis Logic).

### Synthesis Process (Cultivate → Execute → Contribute)
1. **CULTIVATE**: Analyze new DREAM/SPIRITUAL documents via LLM (extract theme, emotion). Compare vectors against historical synthesis to compute DFC. If DFC > 3 in 7 days → "Limiting Subconscious Misalignment." If DFC > 5 in 14 days → "Spiritual Disalignment."
2. **EXECUTE**: Generate HOLISTIC actionable item (identity-aligned, addresses the misalignment) OR MANDATED item (health-driven).
3. **CONTRIBUTE**: Monitor health metrics (health_metrics table) for adherence to items and correlation with identity-focused actions.
4. **H2 Prediction**: If new misalignment detected AND 7-day HOLISTIC adherence < 70% → log NON_ADHERENCE prediction to `user_cognitive_state` with HIGH confidence.

---

## Health Data Ingestion & Multi-Frontend Support

### Data Sources
- **DIRECT_DB**: User enters health metrics directly via App UI (`health_metrics` table).
- **APPLE_HEALTH / ANDROID_HEALTH**: Future mobile apps sync via App Service → Engine processes.
- **User Selection**: `user_preferences.health_data_ingestion` determines source strategy.

### Health Metrics Schema
- **`health_metrics` table**: `metric_name` (RHR, SLEEP_SCORE, BLOOD_GLUCOSE, WEIGHT), `metric_value`, `recorded_at`, `source_metadata` (JSONB for ingestion details).
- **Current Data Entry (MVP)**: Direct user input via web form (`/api/v1/health-metrics` POST) only.
- **Future Integration**: Apple Health (iOS app) and Android Health Connect will sync via App Service → Engine upon native app release.
- **RLS Dual-Mode**: Primary user owns; Professionals access via `data_access_grants` with scope check (`access_scope -> 'health_metrics' ? 'read'`).

### Multi-Frontend API Contracts
- **Web (Vue 3)**, **iOS**, **Android** all call App Service (`app:8000`) via identical HTTP API.
- **App Service Responsibilities**: Auth gateway, CRUD proxying, async job queueing, JWT validation, RLS context passing.
- **Engine Service**: Processes all logic; both web and mobile clients receive identical responses.
- **No Mobile-Specific Endpoints**: Keep API response formats consistent; client-side UI adapts (responsive design via Tailwind).
- **See**: [06 ui technical specifications.md`documentation/06 ui technical specifications.md` (API Contracts) for full endpoint definitions.

---

## Engine Synthesis Workflow (Detailed)

### CULTIVATE Phase: Dream/Spiritual Analysis
**File**: [07 engine logic specifications.md`documentation/07 engine logic specifications.md`

1. **Input**: All new `documents` with `document_type IN ('DREAM', 'JOURNAL', 'SPIRITUAL')` since last synthesis.
2. **LLM Task**: Extract **dominant emotion** and **core subconscious theme** (e.g., "Lack of self-worth", "Fear of commitment").
3. **Vector Search**: 
   - Vectorize the extracted theme
   - Query `document_vectors` for historical documents with similar themes (using pgvector cosine similarity)
   - Count matches in 7-day and 14-day windows
4. **Classification Logic**:
   - **DFC (Disalignment Frequency Count)** > 3 in 7 days → "Limiting Subconscious Misalignment"
   - **DFC** > 5 in 14 days → "Spiritual Disalignment" (severe pattern)
5. **Storage**: Log findings to `synthesis_log` table with theme, DFC, classification, and timestamp.

### EXECUTE Phase: Actionable Item Generation
**Holistic Item Generation (H1 Focus)**:
- **Prerequisite**: Limiting Subconscious Misalignment identified in CULTIVATE
- **Input**: Synthesis result + `users.identity_statement` (user's core identity)
- **LLM Prompt**: "Generate one specific Actionable Item that directly contradicts the misalignment and reaffirms the user's identity. Type: HOLISTIC."
- **Output**: Insert into `actionable_items` with `item_type='HOLISTIC'`, `status='PENDING'`

**Mandated Item Generation (Health Focus)**:
- **Prerequisite**: New `health_metrics` entries or poor health scores
- **Input**: Latest health data + current `actionable_items`
- **LLM Prompt**: "Generate one behavioral item to address the worst metric (e.g., 'Go to bed 30 min earlier'). Type: MANDATED."
- **Output**: Insert into `actionable_items` with `item_type='MANDATED'`, `status='PENDING'`

### H2 Validation: Non-Adherence Prediction
**Logic**:
- **IF** (New synthesis contains "Limiting Subconscious Misalignment")
- **AND** (7-day adherence to HOLISTIC items < 70%)
- **THEN** Log to `user_cognitive_state` with `prediction_type='NON_ADHERENCE'`, `prediction_confidence='HIGH'`
- **App Action**: Inject supportive intervention message into chat UI

### CONTRIBUTE Phase: Health Metric Correlation
- Monitor `health_metrics` for improvements (RHR↓, SLEEP_SCORE↑)
- Correlate adherence to HOLISTIC items with positive health outcomes
- Track `cognitive_efficacy_metrics` for H3 validation (80% adherence rate)

---

## Secondary User (Professional) Access Pattern

### Data Access Grants Flow
1. **Primary User** grants access via `/api/v1/grants` (POST) with:
   - `professional_user_id`: UUID of doctor/coach
   - `access_scope`: JSONB defining granular permissions
   - Example scope: `{"documents": {"read": true}, "health_metrics": {"read": true}, "start_date": "2025-01-01"}`
2. **Professional Login**: Receives JWT with `sub=professional_user_id`
3. **RLS Enforcement**: All queries check:
   - Active grant exists in `data_access_grants`
   - `revoked_at IS NULL` (not revoked)
   - Granular scope check: `access_scope -> 'table_name' ? 'read'`
4. **Revocation**: Primary user calls `/api/v1/grants/{professional_user_id}` (DELETE) to set `revoked_at`

**Critical**: Write access ALWAYS restricted to primary user (RLS WITH CHECK clause).

---

## Async Job Pattern (Synthesis, Reports)

**File**: [07 engine logic specifications.md`documentation/07 engine logic specifications.md` - Section VI

### Job Polling (Exponential Backoff)
- **Initial Delay**: 1000ms (1 second)
- **Backoff Multiplier**: 1.5x
- **Maximum Delay**: 15000ms (15 seconds)
- **Max Retries**: 60 (≈15 min total)
- **Calculation**: `Delay(n) = min(1000 * (1.5 ^ n), 15000)`

### Job Status Responses
```json
// PENDING
{"status": "PROCESSING", "progress": 55, "message": "Analyzing dream documents..."}

// COMPLETE
{"status": "COMPLETE", "result_uri": "/api/v1/synthesis-report/{job_id}", "message": "Report is ready."}
```

### App-to-Engine Job Initiation
1. App calls `POST /api/v1/synthesis/job` with `user_id` and synthesis params
2. Engine queues job on Redis, returns `job_id` (202 Accepted)
3. App stores `job_id` in Pinia state
4. Client polls `GET /api/v1/synthesis/job/{job_id}` with exponential backoff
5. On COMPLETE, retrieve final result via `GET /api/v1/synthesis/{synthesis_id}` (RLS-protected)

---

## Engine Root Endpoint (Security & Documentation)

### GET /

When accessed via browser (`http://localhost:8001`), the Engine returns an HTML landing page that:

1. **Displays Security Notice**: Clearly states the service is restricted and internal only
2. **Lists All API Endpoints**: Complete reference of all 30+ endpoints with:
   - HTTP method (GET, POST, PATCH, DELETE)
   - Full path (e.g., `/api/v1/synthesis/job`)
   - Purpose/description
   - Auth requirement (✅ required or ❌ not required)
   - RLS enforcement status (✅ enforced or ❌ global config)
3. **Contact Information**: Instructions for unauthorized users to request administrator access
4. **Links to Interactive Docs**: References to `/docs` (Swagger UI) and `/redoc` (ReDoc)

**Purpose**: Prevent casual browser discovery of internal service while providing authorized users (administrators, developers) with immediate access to API documentation.

**See**: [10 engine api reference.md`documentation/10 engine api reference.md` for complete API endpoint list and landing page HTML template.

---

## Critical API Endpoints (App Service)

### Authentication (Synchronous)
- `POST /api/v1/auth/login`: Forward credentials to Engine, return JWT
- `POST /api/v1/auth/register`: Forward user data to Engine, create user
- `POST /api/v1/auth/request-password-reset`: Queue email task asynchronously (202 Accepted)

### Daily Check (Gateway for all other features)
- `GET /api/v1/daily-check/status`: Check if all mandatory questions answered
- `GET /api/v1/daily-check/question`: Get next unanswered question
- `POST /api/v1/daily-check/answer`: Submit user answer
- **Requirement**: Synthesis NEVER starts if status is PENDING

### Synthesis & Reports (Asynchronous)
- `POST /api/v1/synthesis/job`: Queue synthesis job, return `job_id`
- `GET /api/v1/synthesis/job/{job_id}`: Poll job status (use exponential backoff)
- `GET /api/v1/synthesis/{synthesis_id}`: Retrieve completed synthesis (RLS-protected)

### User Data Management
- `GET /api/v1/action-items`: Fetch actionable items
- `POST /api/v1/action-items`: Create new item
- `POST /api/v1/action-items/{item_id}/adherence`: Log adherence/completion
- `GET /api/v1/health-metrics`: Fetch health data
- `POST /api/v1/health-metrics`: Log new health metric

### User Preferences
- `GET /api/v1/user-preferences`: Fetch advisor names, modes, tones, synthesis_matrix
- `PATCH /api/v1/user-preferences`: Update preferences (including JSONB synthesis_matrix)

### Professional Access (Secondary Users)
- `GET /api/v1/grants`: List active grants for current user
- `POST /api/v1/grants`: Grant access to a professional
- `DELETE /api/v1/grants/{professional_user_id}`: Revoke access
- **RLS Enforcement**: Professional requests use same API but with dual-mode RLS checks

---

## Database Tables Summary (RLS Enforcement Status)

| Table | RLS Enabled | Write Isolation | Read (Dual-Mode) | Purpose |
|-------|-------------|-----------------|------------------|---------|
| `users` | ✅ | Primary only | Primary only | Identity & auth root |
| `user_preferences` | ✅ | Primary only | Primary only | Advisor config, synthesis_matrix |
| `actionable_items` | ✅ | Primary only | ✅ Dual-mode | EXECUTE phase items |
| `adherence_log` | ✅ | Primary only | Primary only | Execution tracking |
| `documents` | ✅ | Primary only | ✅ Dual-mode | CULTIVATE raw data |
| `document_vectors` | ✅ | Primary only | Primary only | RAG storage (Engine only) |
| `health_metrics` | ✅ | Primary only | ✅ Dual-mode | CONTRIBUTE data |
| `data_access_grants` | ✅ | Primary only | Primary only | Professional access config |
| `user_cognitive_state` | ✅ | Primary only | Primary only | Daily check status |
| `pre_synthesis_answers` | ✅ | Primary only | Primary only | Daily check answers (4-day retention) |
| `cognitive_definitions` | ❌ | N/A | N/A | System config (non-RLS global) |
| `cognitive_efficacy_metrics` | ❌ | N/A | N/A | H1/H2/H3 tracking (non-RLS global) |
| `pre_synthesis_questions` | ❌ | N/A | N/A | Daily check questions (non-RLS global) |

---

## Error Handling & Validation Standards

### Standardized API Error Response

All error responses **MUST** follow this format:

```json
{
  "error": {
    "code": "ERR_VALIDATION_FAILED",
    "message": "One or more fields are invalid",
    "status": 422,
    "timestamp": "2025-01-15T10:30:00Z",
    "details": [
      {
        "field": "email",
        "issue": "Invalid email format",
        "suggestion": "Use format: user@example.com"
      }
    ],
    "trace_id": "req_abc123xyz"
  }
}
```

### Error Code Categories

| Category | Codes | HTTP Status | Client Action |
|----------|-------|------------|----------------|
| **Authentication** | `ERR_AUTH_FAILED`, `ERR_TOKEN_EXPIRED`, `ERR_INVALID_CREDENTIALS` | 401 | Redirect to login, refresh token |
| **Authorization** | `ERR_INSUFFICIENT_PERMISSIONS`, `ERR_GRANT_REVOKED` | 403 | Show permission denied message |
| **Validation** | `ERR_VALIDATION_FAILED`, `ERR_MISSING_REQUIRED_FIELD` | 422 | Highlight invalid fields, show suggestions |
| **Not Found** | `ERR_RESOURCE_NOT_FOUND`, `ERR_USER_NOT_FOUND` | 404 | Show "Not found" message |
| **Conflict** | `ERR_USERNAME_EXISTS`, `ERR_EMAIL_EXISTS`, `ERR_DUPLICATE_DAILY_ANSWER` | 409 | Show conflict message, suggest action |
| **Rate Limit** | `ERR_RATE_LIMIT_EXCEEDED` | 429 | Show retry-after message, exponential backoff |
| **Server** | `ERR_INTERNAL_SERVER_ERROR`, `ERR_DATABASE_ERROR`, `ERR_LLM_UNAVAILABLE` | 500 | Log error, show generic user message, enable retry |
| **Service** | `ERR_ENGINE_UNAVAILABLE`, `ERR_SERVICE_DEGRADED` | 503 | Show "Service unavailable, try again later" |

### Field Validation Standards

| Field | Rules | Error Code |
|-------|-------|---------------|
| **email** | Valid RFC 5322, unique in users table, max 100 chars | `ERR_INVALID_EMAIL`, `ERR_EMAIL_EXISTS` |
| **username** | 3-50 alphanumeric + underscores, unique, case-insensitive | `ERR_USERNAME_TOO_SHORT`, `ERR_USERNAME_EXISTS` |
| **password** | Min 12 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char | `ERR_PASSWORD_TOO_WEAK` |
| **identity_statement** | Max 500 chars, plain text (no HTML) | `ERR_IDENTITY_STATEMENT_TOO_LONG` |
| **dream_content** | Max 5000 chars, plain text | `ERR_CONTENT_TOO_LONG` |
| **metric_value** | Numeric, within valid range per metric type | `ERR_INVALID_METRIC_VALUE` |

### Retry Strategy (Client-Side)
- **Non-retryable** (4xx errors): 400, 401, 403, 404, 409, 422 → Show error to user, don't retry
- **Retryable** (5xx errors): 500, 503 → Exponential backoff (1s, 2s, 4s, 8s, max 32s), max 5 attempts
- **Rate-limited** (429): Parse `Retry-After` header, wait and retry up to 3 times

### RLS Violation Handling
- **Error Code**: `ERR_INSUFFICIENT_PERMISSIONS`
- **Status**: 403 Forbidden
- **Message**: "You do not have permission to access this resource"
- **Logging**: Log attempted access (user_id, resource_type, timestamp) for security audit
- **Action**: App clears session, redirects to login

---

## Common Pitfalls to Avoid

1. **Network Isolation**: App **cannot** import `psycopg2` or Ollama. App **cannot** call DB/LLM directly.
2. **Blocking Calls**: App **must never** make synchronous requests to Engine for heavy tasks (synthesis, vectorization). Always use the async queue.
3. **RLS Bypass**: Never use `cognitive_engine_full` role for live queries. Use `cognitive_engine_rls` with proper session context.
4. **Env Variables**: Don't hardcode secrets. Load from `.env.dev` / `.env.prod`.
5. **Data Retention**: Always delete old `user_cognitive_state` and `pre_synthesis_answers` rows (enforced nightly via `db_maintenance_purge_old_state()` stored procedure).
6. **JSON Handling**: Engine validates and parses JSON from `*_json` fields; App must not interpret.
7. **Vector Operations**: Only Engine can read `document_vectors` table. Never expose embedding values to App or client.
8. **Advisor Config**: Changes to `cognitive_definitions` require Engine restart or cache invalidation. Don't modify advisor prompts via App endpoints.
9. **Synthesis Matrix Validation**: App passes `synthesis_matrix` JSONB opaquely; Engine must validate structure before applying weights.
10. **Secondary User Access**: Always check `data_access_grants` + `revoked_at IS NULL` + granular scope (`access_scope -> 'table_name' ? 'read'`) in RLS policies. Don't trust the `X-User-ID` header alone.
11. **Daily Check Blocker**: Ensure synthesis NEVER starts if `user_cognitive_state` has PENDING questions. Validate on App-side before queueing job.
12. **Health Metric Timestamps**: Use `recorded_at` (when metric was measured), not `created_at` (when logged). Affects adherence calculations.

---

## Documentation Stack

### Core System Design
- **[01 Project Definition`documentation/01 project definition.md`**: Business goals, hypotheses (H1/H2/H3), philosophical framework
- **[02 Infrastructure Setup`documentation/02 infratructure setup.md`**: Network isolation, service architecture, ports, environment variables
- **[03 Database Schema`documentation/03 db_schema.sql`**: RLS policies, table definitions, indexes, constraints

### Implementation Guides
- **[04 Standards Guide`documentation/04 standards guide.md`**: Naming conventions, service responsibilities, data serialization, retention policies
- **[05 Functionality Guide`documentation/05 functionality guide.md`**: User flows, business rules, feature descriptions (non-technical)
- **[06 UI Technical Specs`documentation/06 ui technical specifications.md`**: API contracts, response schemas, daily check flow, async patterns
- **[07 Engine Logic Specifications`documentation/07 engine logic specifications.md`**: Synthesis algorithms, DFC calculation, hypothesis validation

### Operations & Deployment
- **[08 DevOps Deployment Guide`documentation/08 devops deployment guide.md`**: Build/deploy procedures, backup/restore, security hardening, troubleshooting
- **[09 LLM Prompts & Advisor Config`documentation/09 llm prompts advisor config.md`**: System prompts, mode/tone modifiers, user custom questions, prompt management
- **[10 Engine API Reference`documentation/10 engine api reference.md`**: Complete Engine endpoint documentation, landing page specification, security notice

### Supporting Resources
- **[Docker Commands Reference`helpful_command_lines/Docker Commands.md`**: Quick Docker operations
