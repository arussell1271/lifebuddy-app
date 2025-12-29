# Engine API Reference (Internal Service)

**Service**: Cognitive Engine (Internal)  
**Port**: 8001 (Development & Testing)  
**Access**: Internal only via `core-network` (Docker)  
**Root Endpoint**: `http://localhost:8001/` (Browser: Security notice + API listing)  
**Swagger Docs**: `http://localhost:8001/docs` (Interactive API explorer)  
**ReDoc Docs**: `http://localhost:8001/redoc` (Alternative documentation)

---

## Security Notice

The Engine service is **NOT publicly accessible** and handles:
- Direct database access (user data, proprietary algorithms)
- LLM integration (Ollama/Mistral)
- Vector operations (embeddings, RAG)
- Synthesis logic (Cultivate→Execute→Contribute)

**Access is restricted to**:
- ✅ App Service (internal via `core-network`)
- ✅ Database (`postgres` container)
- ✅ LLM (`ollama` container)
- ✅ Message Queue (`redis` container)

**Unauthorized Access Attempts**:
- Will be logged with timestamp, IP, and request details
- Should be reported to administrator immediately
- May trigger rate limiting / IP blocking (future)

---

## Root Landing Page (GET /)

When users access `http://localhost:8001` via browser:

### Response Format: HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Life Buddy Cognitive Engine</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .security-notice { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 30px; }
        .security-notice h2 { margin-top: 0; color: #856404; }
        .api-section { margin: 30px 0; }
        .endpoint { background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .method { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; margin-right: 10px; }
        .get { background: #61affe; color: white; }
        .post { background: #49cc90; color: white; }
        .patch { background: #fca130; color: white; }
        .delete { background: #f93e3e; color: white; }
        .path { font-family: monospace; color: #0066cc; }
        .contact { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin-top: 30px; }
        h3 { color: #333; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Life Buddy Cognitive Engine</h1>
        
        <div class="security-notice">
            <h2>⚠️ Restricted Access</h2>
            <p><strong>This service is internal and secured.</strong></p>
            <p>The Cognitive Engine handles sensitive operations including:</p>
            <ul>
                <li>Direct database access to user health and cognitive data</li>
                <li>LLM (Large Language Model) integration and synthesis</li>
                <li>Proprietary algorithms (Hypothesis H1/H2/H3 validation)</li>
                <li>Vector embeddings and semantic analysis</li>
            </ul>
            <p><strong>If you are an authorized administrator or developer and need access, please contact the administrator.</strong></p>
        </div>

        <div class="api-section">
            <h2>📡 Available Endpoints</h2>
            <p>This service exposes the following internal API endpoints:</p>

            <h3>Authentication</h3>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/auth/register</span>
                <br><small>Register new user account</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/auth/login</span>
                <br><small>Authenticate user, return JWT token</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/auth/validate-token</span>
                <br><small>Validate JWT token and return claims</small>
            </div>

            <h3>User Data Management</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/users/{user_id}</span>
                <br><small>Retrieve user profile and preferences</small>
            </div>
            <div class="endpoint">
                <span class="method patch">PATCH</span>
                <span class="path">/api/v1/users/{user_id}</span>
                <br><small>Update user identity statement, preferences</small>
            </div>

            <h3>Daily Check (Pre-Synthesis Gating)</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/daily-check/status/{user_id}</span>
                <br><small>Check if all mandatory questions answered for today</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/daily-check/next-question/{user_id}</span>
                <br><small>Get next unanswered question</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/daily-check/submit-answer</span>
                <br><small>Submit user answer to daily check question</small>
            </div>

            <h3>Documents (CULTIVATE Phase Input)</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/documents/{user_id}</span>
                <br><small>Retrieve user's dreams, journals, spiritual notes (RLS-protected)</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/documents</span>
                <br><small>Create new dream, journal, or spiritual document</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/documents/{document_id}</span>
                <br><small>Retrieve specific document (RLS-protected)</small>
            </div>

            <h3>Synthesis & Analysis (Core Engine Logic)</h3>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/synthesis/job</span>
                <br><small>Queue synthesis job (Cultivate→Execute→Contribute), returns job_id</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/synthesis/job/{job_id}</span>
                <br><small>Poll synthesis job status (PROCESSING, COMPLETE, ERROR)</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/synthesis/{synthesis_id}</span>
                <br><small>Retrieve completed synthesis result (RLS-protected)</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/synthesis/report/{synthesis_id}</span>
                <br><small>Get full synthesis report with DFC, classifications, recommendations</small>
            </div>

            <h3>Actionable Items (EXECUTE Phase)</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/action-items/{user_id}</span>
                <br><small>Retrieve user's pending/completed actionable items (RLS-protected)</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/action-items</span>
                <br><small>Create new actionable item (HOLISTIC or MANDATED)</small>
            </div>
            <div class="endpoint">
                <span class="method patch">PATCH</span>
                <span class="path">/api/v1/action-items/{item_id}</span>
                <br><small>Update item status (PENDING → IN_PROGRESS → COMPLETED)</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/action-items/{item_id}/log-adherence</span>
                <br><small>Log user adherence/completion of actionable item</small>
            </div>

            <h3>Health Metrics (CONTRIBUTE Phase)</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/health-metrics/{user_id}</span>
                <br><small>Retrieve user's health metrics (RHR, SLEEP_SCORE, etc., RLS-protected)</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/health-metrics</span>
                <br><small>Log new health metric (metric_name, metric_value, recorded_at)</small>
            </div>
            <div class="endpoint">
                <span class="method delete">DELETE</span>
                <span class="path">/api/v1/health-metrics/{metric_id}</span>
                <br><small>Delete health metric (if user changes entry)</small>
            </div>

            <h3>Adherence Analysis</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/adherence-report/{user_id}</span>
                <br><small>Calculate adherence rate to HOLISTIC vs. MANDATED items (RLS-protected)</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/efficacy-metrics/{user_id}</span>
                <br><small>Retrieve H1/H2/H3 hypothesis validation metrics</small>
            </div>

            <h3>User Preferences & Customization</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/user-preferences/{user_id}</span>
                <br><small>Retrieve advisor names, spiritual mode, tone, synthesis_matrix, custom questions</small>
            </div>
            <div class="endpoint">
                <span class="method patch">PATCH</span>
                <span class="path">/api/v1/user-preferences/{user_id}</span>
                <br><small>Update advisor config, custom questions (max 3 per advisor)</small>
            </div>

            <h3>Professional Access (Secondary Users)</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/data-access-grants/{user_id}</span>
                <br><small>List active grants for professional/secondary user access</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/data-access-grants</span>
                <br><small>Create new grant (professional_user_id, access_scope, start_date)</small>
            </div>
            <div class="endpoint">
                <span class="method delete">DELETE</span>
                <span class="path">/api/v1/data-access-grants/{grant_id}</span>
                <br><small>Revoke professional access</small>
            </div>

            <h3>Admin & Configuration (Engine-Internal Only)</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/config/cognitive-definitions</span>
                <br><small>Retrieve system prompts and advisor templates (non-RLS global config)</small>
            </div>
            <div class="endpoint">
                <span class="method patch">PATCH</span>
                <span class="path">/api/v1/config/cognitive-definitions/{advisor_type}</span>
                <br><small>Update advisor system prompt (admin-only, requires special role)</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/config/cache-invalidate</span>
                <br><small>Force invalidate prompt/definition caches (admin-only)</small>
            </div>

            <h3>Health & Monitoring</h3>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/health</span>
                <br><small>Health check endpoint (returns 200 if service is running)</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/ready</span>
                <br><small>Readiness check (verifies database, LLM, Redis connectivity)</small>
            </div>

        </div>

        <div class="contact">
            <h3>📞 Need Access?</h3>
            <p>If you believe you should have access to this service, please contact the system administrator with:</p>
            <ul>
                <li>Your name and email</li>
                <li>Your role (Developer, DevOps, AI Engineer, etc.)</li>
                <li>The specific task or feature you need to work on</li>
                <li>Request timestamp</li>
            </ul>
            <p><strong>Access will be granted only with explicit administrator approval.</strong></p>
        </div>

        <hr>
        <p style="color: #666; font-size: 12px;">
            <strong>For Authorized Users</strong>: View interactive API documentation at 
            <a href="/docs" target="_blank">/docs (Swagger UI)</a> or 
            <a href="/redoc" target="_blank">/redoc (ReDoc)</a>
        </p>
    </div>
</body>
</html>
```

---

## API Endpoint Summary Table

| Category | HTTP | Endpoint | Purpose | Auth | RLS |
|----------|------|----------|---------|------|-----|
| **Auth** | POST | /api/v1/auth/register | Create user | ❌ | N/A |
| | POST | /api/v1/auth/login | Authenticate | ❌ | N/A |
| | POST | /api/v1/auth/validate-token | Validate JWT | ✅ | N/A |
| **Users** | GET | /api/v1/users/{user_id} | Get profile | ✅ | ✅ |
| | PATCH | /api/v1/users/{user_id} | Update profile | ✅ | ✅ |
| **Daily Check** | GET | /api/v1/daily-check/status/{user_id} | Check completion | ✅ | ✅ |
| | GET | /api/v1/daily-check/next-question/{user_id} | Get question | ✅ | ✅ |
| | POST | /api/v1/daily-check/submit-answer | Submit answer | ✅ | ✅ |
| **Documents** | GET | /api/v1/documents/{user_id} | List documents | ✅ | ✅ |
| | POST | /api/v1/documents | Create document | ✅ | ✅ |
| | GET | /api/v1/documents/{document_id} | Get document | ✅ | ✅ |
| **Synthesis** | POST | /api/v1/synthesis/job | Queue job | ✅ | ✅ |
| | GET | /api/v1/synthesis/job/{job_id} | Poll status | ✅ | ✅ |
| | GET | /api/v1/synthesis/{synthesis_id} | Get result | ✅ | ✅ |
| | GET | /api/v1/synthesis/report/{synthesis_id} | Get report | ✅ | ✅ |
| **Action Items** | GET | /api/v1/action-items/{user_id} | List items | ✅ | ✅ |
| | POST | /api/v1/action-items | Create item | ✅ | ✅ |
| | PATCH | /api/v1/action-items/{item_id} | Update item | ✅ | ✅ |
| | POST | /api/v1/action-items/{item_id}/log-adherence | Log adherence | ✅ | ✅ |
| **Health Metrics** | GET | /api/v1/health-metrics/{user_id} | List metrics | ✅ | ✅ |
| | POST | /api/v1/health-metrics | Log metric | ✅ | ✅ |
| | DELETE | /api/v1/health-metrics/{metric_id} | Delete metric | ✅ | ✅ |
| **Adherence** | GET | /api/v1/adherence-report/{user_id} | Adherence stats | ✅ | ✅ |
| | GET | /api/v1/efficacy-metrics/{user_id} | H1/H2/H3 metrics | ✅ | ✅ |
| **Preferences** | GET | /api/v1/user-preferences/{user_id} | Get preferences | ✅ | ✅ |
| | PATCH | /api/v1/user-preferences/{user_id} | Update preferences | ✅ | ✅ |
| **Grants** | GET | /api/v1/data-access-grants/{user_id} | List grants | ✅ | ✅ |
| | POST | /api/v1/data-access-grants | Create grant | ✅ | ✅ |
| | DELETE | /api/v1/data-access-grants/{grant_id} | Revoke grant | ✅ | ✅ |
| **Admin** | GET | /api/v1/config/cognitive-definitions | Get definitions | ✅ | ❌ |
| | PATCH | /api/v1/config/cognitive-definitions/{advisor_type} | Update definitions | ✅ (admin) | ❌ |
| | POST | /api/v1/config/cache-invalidate | Invalidate cache | ✅ (admin) | ❌ |
| **Health** | GET | /health | Service health | ❌ | N/A |
| | GET | /ready | Readiness check | ❌ | N/A |

---

## Architecture Notes

### Request Flow

```
Browser/Admin → GET http://localhost:8001/ 
                    ↓
                (Landing page with security notice)
                    ↓
            Shows all endpoints above
                    ↓
        Links to /docs (Swagger) or /redoc (ReDoc)
```

### Response Headers

All Engine responses should include:
```
X-Request-ID: unique-trace-id
X-Service: cognitive-engine
X-Version: 1.0
Cache-Control: no-store
X-Content-Type-Options: nosniff
```

### Authentication Flow

1. **Public Endpoints** (no auth required):
   - `POST /api/v1/auth/register`
   - `POST /api/v1/auth/login`
   - `GET /health`
   - `GET /ready`

2. **Protected Endpoints** (JWT required in `Authorization: Bearer <token>` header):
   - All other endpoints require valid JWT token
   - Token claims must include `sub` (user_id), `aud` (life-buddy-app), `exp`

3. **Admin Endpoints** (special role required):
   - `PATCH /api/v1/config/cognitive-definitions/{advisor_type}` - Only `admin` role
   - `POST /api/v1/config/cache-invalidate` - Only `admin` role

---

## Rate Limiting

**To be implemented**:
- Auth endpoints: 5 attempts per 15 minutes per IP
- Synthesis jobs: 10 per day per user
- Health metrics: 100 per day per user
- All endpoints: 1000 requests per hour per authenticated user

---

## Logging & Security

### Logged Events

- ✅ All auth attempts (success + failure)
- ✅ All data access (user_id, table, operation)
- ✅ All synthesis jobs (user_id, status, DFC, duration)
- ✅ All unauthorized access attempts
- ✅ All admin operations (who, what, when)
- ✅ All RLS violations

### Monitoring Points

- Database connection pool usage
- Ollama/LLM availability and response times
- Redis queue depth
- Synthesis job queue depth and processing time
- Error rates by endpoint
- Unauthorized access attempts per IP
- JWT token validation failures

---

## Future Enhancements (Phase 2+)

- [ ] GraphQL endpoint for complex queries
- [ ] WebSocket support for real-time chat with advisors
- [ ] Batch endpoint for bulk metric ingestion
- [ ] Event streaming (Kafka/RabbitMQ) for synthesis notifications
- [ ] API rate limit configuration per user tier
- [ ] Endpoint metrics dashboard (response times, success rates)
- [ ] SDK generation (Python, JavaScript, Go)

