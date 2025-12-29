# Engine Root Endpoint Implementation Guide

**Created**: December 29, 2025  
**Purpose**: Provide security notice and API documentation when accessing Engine via browser (`http://localhost:8001`)

---

## What Has Been Delivered

### 1. **Complete Engine API Reference Document** 
📄 File: [documentation/10 engine api reference.md](../documentation/10 engine api reference.md)

**Contains**:
- Full HTML template for the landing page (copy-paste ready)
- Complete list of 30+ Engine API endpoints organized by category
- Summary table showing HTTP method, endpoint path, purpose, auth requirement, and RLS status
- Security notice text (copy-paste ready)
- Contact information for access requests
- Architecture notes, rate limiting strategy, logging guidance
- Future enhancement roadmap

**Use Case**: When users access `http://localhost:8001` via web browser, they see:
1. ⚠️ **Security Notice** - Explains the service is restricted and internal
2. 📡 **API Listing** - Shows all available endpoints with descriptions
3. 📞 **Contact Info** - Instructions to request access from administrator
4. 🔗 **Links** - Direct access to `/docs` (Swagger), `/redoc` (ReDoc), and full API reference

### 2. **Updated Copilot Instructions**
📄 File: [.github/copilot-instructions.md](../.github/copilot-instructions.md)

**New Section Added**: "Engine Root Endpoint (Security & Documentation)"
- Documents the behavior when accessing GET /
- References the full API reference document
- Explains security purpose and user guidance

**Updated Documentation Stack**:
- Added entry for `10 engine api reference.md`
- Reorganized Tier 3 (Operations & Deployment) to include new document

### 3. **FastAPI Implementation Example**
📄 File: [engine/example_root_endpoint.py](../engine/example_root_endpoint.py)

**Shows**:
- How to implement the root endpoint (GET /) in FastAPI
- Health check endpoints (GET /health, GET /ready)
- Example of protected endpoint with JWT authentication
- Docstring patterns for all endpoints
- How to return the HTML landing page

**Can be**: Copy → Modify → Integrate directly into your Engine service code

### 4. **Updated Documentation Manifest**
📄 File: [documentation/DOCUMENTATION_MANIFEST.md](../documentation/DOCUMENTATION_MANIFEST.md)

**Reflects**:
- New `10 engine api reference.md` file in Tier 3
- Updated change log with Engine root endpoint feature
- Updated line count (now 3,500+ lines total documentation)

---

## How the Landing Page Works

### User Journey

```
User opens browser → http://localhost:8001
    ↓
    GET / endpoint triggered
    ↓
    Server returns HTML page (from 10 engine api reference.md)
    ↓
Browser displays:
    1. 🧠 Title: "Life Buddy Cognitive Engine"
    2. ⚠️  Security Warning (yellow box)
    3. 📡 API Endpoints listing (organized by category)
    4. 📞 Contact administrator section
    5. 🔗 Links to /docs and /redoc
```

### Security Benefits

✅ **Prevents Casual Discovery**: Random port scanning won't expose sensitive endpoints—just a notice  
✅ **Clear Access Control**: Visitors know they need approval  
✅ **Audit Trail**: Every access is logged (recommended in implementation)  
✅ **Documentation**: Authorized users get immediate API reference  
✅ **Professional Appearance**: Shows security is taken seriously  

---

## Implementation Checklist

When building the Engine service, use this checklist:

### Phase 1: Core Setup
- [ ] Copy HTML from [10 engine api reference.md](../documentation/10 engine api reference.md) into your Engine code
- [ ] Create GET / endpoint that returns the HTML
- [ ] Implement logging for all root endpoint access
- [ ] Create GET /health (returns 200 if running)
- [ ] Create GET /ready (checks database, Ollama, Redis)

### Phase 2: Security
- [ ] Add request logging (timestamp, IP, user agent)
- [ ] Log unauthorized access attempts to audit table
- [ ] Consider IP-based rate limiting (future enhancement)
- [ ] Ensure HTML doesn't expose internal details beyond endpoint names
- [ ] Add security headers (X-Frame-Options, X-Content-Type-Options, etc.)

### Phase 3: Integration
- [ ] Use example_root_endpoint.py as template for your main FastAPI app
- [ ] Keep API endpoint documentation in sync with /docs (Swagger auto-generates from decorators)
- [ ] Update [10 engine api reference.md](../documentation/10 engine api reference.md) whenever you add/remove endpoints
- [ ] Verify landing page renders correctly at `http://localhost:8001`

### Phase 4: Testing
- [ ] Test browser access to root endpoint
- [ ] Verify /docs and /redoc links work
- [ ] Confirm health check endpoints return correct status
- [ ] Test with various browsers (Chrome, Firefox, Safari)
- [ ] Verify responsive design on mobile (if needed)

---

## Key Files to Reference

| File | Purpose |
|------|---------|
| [10 engine api reference.md](../documentation/10 engine api reference.md) | Complete endpoint listing + HTML template |
| [example_root_endpoint.py](../engine/example_root_endpoint.py) | FastAPI implementation example |
| [.github/copilot-instructions.md](../.github/copilot-instructions.md) | AI agent guidance (section: "Engine Root Endpoint") |
| [02 infrastructure setup.md](../documentation/02 infratructure setup.md) | Network/port configuration |
| [06 ui technical specifications.md](../documentation/06 ui technical specifications.md) | API contract patterns |

---

## HTML Template Customization

The HTML in [10 engine api reference.md](../documentation/10 engine api reference.md) can be customized:

### Change Colors
```html
/* Security notice box background */
.security-notice { background: #fff3cd; } /* Yellow */

/* Endpoint cards */
.endpoint { border-left: 4px solid #007bff; } /* Blue */
```

### Add Your Logo
```html
<img src="/static/logo.png" alt="Life Buddy Logo" style="width: 200px;">
```

### Adjust Endpoint List
- Copy entire endpoint blocks from the template
- Modify to match your actual implementation
- Keep HTTP method color coding consistent (GET=blue, POST=green, PATCH=orange, DELETE=red)

### Add More Sections
- Admin endpoints section
- Deprecated endpoints section
- Rate limit information
- Status page link

---

## Environment Variables

Make sure your `.env.dev` and `.env.prod` include:

```bash
# Engine Service Configuration
ENGINE_HOST=localhost  # or 0.0.0.0 for Docker
ENGINE_PORT=8001
ENGINE_LOG_LEVEL=info

# Database (for Engine)
DATABASE_URL=postgresql://cognitive_engine_full:password@postgres:5432/postgres

# LLM (Ollama)
OLLAMA_BASE_URL=http://ollama:11434

# Cache/Queue (Redis)
REDIS_URL=redis://message-broker:6379/0

# Security
JWT_SECRET_KEY=<random-32-byte-hex>  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
```

---

## Monitoring & Logging

### Log Entry Points
When implementing, log these events:

1. **All requests to GET /**
   ```
   2025-01-15 10:30:45 | INFO | GET / | IP=192.168.1.100 | User-Agent=Mozilla/5.0
   ```

2. **All auth requests** (login, register)
   ```
   2025-01-15 10:31:20 | INFO | POST /api/v1/auth/login | user=john_doe | status=200
   2025-01-15 10:31:25 | WARN | POST /api/v1/auth/login | user=jane_doe | status=401 (5th attempt)
   ```

3. **Unauthorized access attempts**
   ```
   2025-01-15 10:32:00 | ERROR | GET /api/v1/synthesis/123 | IP=10.0.0.5 | Error=Invalid Token | RLS_Violation=false
   2025-01-15 10:32:15 | ERROR | GET /api/v1/users/other-user-id | IP=10.0.0.5 | Error=RLS Violation
   ```

### Health Check Monitoring
- **GET /health** - Check every 30 seconds (load balancer)
- **GET /ready** - Check before serving traffic (startup probe)

---

## Troubleshooting

### Landing Page Not Loading
**Problem**: `http://localhost:8001` shows 404 or blank page  
**Solution**: 
1. Verify Engine service is running: `docker logs engine`
2. Check if root endpoint is implemented: `docker exec engine python -c "from main import app; print(app.routes)"`
3. Verify FastAPI app is listening on port 8001: `netstat -tuln | grep 8001`

### Swagger UI Not Loading
**Problem**: `http://localhost:8001/docs` is blank or gives 404  
**Solution**:
1. Verify FastAPI has `docs_url="/docs"` parameter in app initialization
2. Check if network allows access to `/docs` endpoint
3. Reload page (Cmd/Ctrl + Shift + R for hard refresh)

### Security Notice Not Displaying
**Problem**: HTML loads but styling is broken  
**Solution**:
1. Copy the entire CSS `<style>` section from template
2. Ensure no HTML is escaped (use `response_class=HTMLResponse`)
3. Check browser console for any JavaScript errors

### Rate Limiting Not Working
**Problem**: `http://localhost:8001` accepts unlimited requests  
**Solution**: 
1. Implement rate limiting middleware (slowapi library recommended)
2. Configure in `.env`: `RATE_LIMIT_ENABLED=true`, `RATE_LIMIT_PER_MINUTE=60`
3. Test with: `for i in {1..100}; do curl http://localhost:8001/; done`

---

## What's Next?

Now that the Engine root endpoint and API reference are fully documented:

1. **Implement the Core Engine Service** → Use `example_root_endpoint.py` as a template
2. **Build App Service** → Reference [06 ui technical specifications.md](../documentation/06 ui technical specifications.md)
3. **Set Up Database** → Use [03 db_schema.sql](../documentation/03 db_schema.sql)
4. **Test Integration** → Follow [DOCUMENTATION_MANIFEST.md](../documentation/DOCUMENTATION_MANIFEST.md) Phase checklist
5. **Deploy to Production** → Use [08 devops deployment guide.md](../documentation/08 devops deployment guide.md)

---

**Last Updated**: December 29, 2025  
**Status**: ✅ Complete - Ready for implementation  
**Audience**: Backend Engineers, DevOps, System Architects
