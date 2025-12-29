# ðŸ“š Documentation Manifest & Update Log

**Purpose**: Track all documentation files and changes to ensure consistency and completeness across the project.

**Last Updated**: December 29, 2025  
**Next Review**: As features are implemented

---

## Documentation Stack (Complete)

### Tier 1: Strategic Docs (Read First)
| File | Purpose | Audience | Status |
|------|---------|----------|--------|
| [01 project definition.md`documentation/01 project definition.md` | Business goals, hypotheses, philosophy | Leadership, All Team | âœ… Complete |
| [02 infrastructure setup.md`documentation/02 infratructure setup.md` | Network isolation, service ports, env vars | DevOps, Architects | âœ… Complete |
| [03 db_schema.sql`documentation/03 db_schema.sql` | Database DDL, RLS policies, constraints | Backend, DBAs | âœ… Complete |

### Tier 2: Implementation Docs (Reference During Build)
| File | Purpose | Audience | Status |
|------|---------|----------|--------|
| [04 standards guide.md`documentation/04 standards guide.md` | Naming, patterns, data retention | All Developers | âœ… Complete |
| [05 functionality guide.md`documentation/05 functionality guide.md` | User flows, business rules (non-technical) | Product, QA, Design | âœ… Complete |
| [06 ui technical specifications.md`documentation/06 ui technical specifications.md` | API contracts, async patterns, daily check | Frontend, Backend | âœ… Complete |
| [07 engine logic specifications.md`documentation/07 engine logic specifications.md` | Synthesis logic, DFC, H1/H2/H3 validation | AI/ML, Backend | âœ… Complete |

### Tier 3: Operations & Deployment Docs (During DevOps/Deployment)
| File | Purpose | Audience | Status |
|------|---------|----------|--------|
| [08 devops deployment guide.md`documentation/08 devops deployment guide.md` | Build, deploy, backup, scaling, security | DevOps, Release Engineers | âœ… Complete |
| [09 llm prompts advisor config.md`documentation/09 llm prompts advisor config.md` | System prompts, mode/tone modifiers, custom questions | AI Engineers, Prompt Engineers | âœ… Complete |
| [10 engine api reference.md`documentation/10 engine api reference.md` | Complete Engine API endpoint documentation, landing page spec, security notice | Developers, AI Agents, Architects | âœ… Complete |

### AI Agent Guidance
| File | Purpose | Audience | Status |
|------|---------|----------|--------|
| [.github/copilot-instructions.md`.github/copilot-instructions.md` | AI agent coding instructions (main reference) | AI Agents, Developers | âœ… Complete |

---

## Change Log

### December 29, 2025 - Initial Documentation Completion

**Added Files**:
- âœ… `08 devops deployment guide.md` - Complete DevOps workflow, backup/restore, scaling, security hardening
- âœ… `09 llm prompts advisor config.md` - LLM system prompts, advisor templates, mode/tone modifiers, user custom questions
- âœ… `10 engine api reference.md` - Complete Engine API reference, landing page HTML template, security notice, endpoint listing
- âœ… `.github/copilot-instructions.md` - AI agent reference document (updated with error handling, deployment stage, admin prompt management)

**Updated Files**:
- âœ… `.github/copilot-instructions.md` - Added:
  - Engine root endpoint specification (GET / with security notice and API listing)
  - Deployment stage (MVP: responsive web, Future: iOS/Android)
  - Admin prompt management & user customization
  - Health data MVP (direct entry only)
  - Comprehensive error handling standards (8 categories, retry logic)
  - Validation standards for key fields

**Key Decisions Documented**:
- Engine root endpoint: Security notice + full API listing when accessed via browser
- Mobile access: Responsive web MVP only (native apps future)
- Health data: Direct user entry only (Apple Health/Android Health Connect future)
- Prompts: Admin-only modification, user custom questions supported
- Billing: Free with ads (structure TBD)
- Error handling: Standardized JSON format with trace IDs
- Deployment: Emphasis on easy builds + strong security

---

## Documentation Maintenance Protocol

### Before Implementation Starts
- [ ] Review all documentation files for consistency
- [ ] Verify all inter-document links are correct
- [ ] Confirm database schema matches standards guide
- [ ] Test DevOps scripts with sample data
- [ ] Review `summaries/IMPLEMENTATION_READY.md` for what's being built

### During Implementation
- [ ] Update relevant docs within 24 hours of code changes
- [ ] Track all API endpoint changes in section 06
- [ ] Document all new database tables/columns in section 03
- [ ] Log all new error codes in this manifest
- [ ] Update `summaries/README_DOCUMENTATION.md` with new documentation
- [ ] Mark progress in `summaries/IMPLEMENTATION_READY.md`

### Before Finalizing Code (Pre-Commit) âš ï¸ CRITICAL
- [ ] **Run error check: `Ctrl+Shift+M` in VS Code (expect 0 errors)** - FIX ANY ERRORS BEFORE COMMITTING
- [ ] Verify all documentation links resolve correctly
- [ ] Check `summaries/IMPLEMENTATION_READY.md` - all features listed and marked?
- [ ] Check `summaries/README_DOCUMENTATION.md` - all related docs linked?
- [ ] Confirm no broken cross-references between documentation files
- [ ] Verify all error codes in code match documentation in standards guide

### After Feature Completion
- [ ] Update copilot-instructions.md if architecture changes
- [ ] Add examples to relevant documentation sections
- [ ] Review error handling completeness
- [ ] Update deployment guide with new deployment steps
- [ ] Update summaries to reflect completed work
- [ ] Run final error check to confirm 0 problems

### Quarterly Review
- [ ] Verify all docs reflect current system state
- [ ] Identify gaps or outdated information
- [ ] Update DevOps scripts based on lessons learned
- [ ] Archive old versions in Git history
- [ ] Review summaries files for accuracy

---

## Error Prevention Strategy (MANDATORY FOR ALL COMMITS)

### Before Every Commit: Zero-Error Verification

**REQUIRED**: Every developer **MUST** verify zero documentation errors before committing code or documentation changes.

**Step 1: Run Error Check**
```powershell
# Open VS Code Problems Panel
Ctrl+Shift+M

# Expected: "No errors found" or empty panel
# If errors appear â†’ DO NOT COMMIT until fixed
```

**Step 2: Fix Any Errors That Appear**

Common error causes:
- âŒ Broken markdown links: `[text](./wrong/path.md)` â†’ âœ… Use file path in code format: `` `documentation/correct/path.md` ``
- âŒ Misspelled file names in links
- âŒ Missing or extra spaces in file paths
- âŒ Inconsistent directory structure references
- âŒ Forgotten file extensions (`.md`, `.sql`, etc.)

**Step 3: Verify Before Commit**
1. Make changes to documentation
2. Save all files
3. Open Problems Panel (`Ctrl+Shift+M`)
4. **Verify: 0 errors** â† This is your gate
5. Only then commit and push

### Why This Matters

Documentation errors are **NOT cosmetic** â€” they:
- Break links for developers trying to navigate the system
- Corrupt the developer experience
- Spread to all team members when merged
- Become increasingly difficult to fix as they accumulate

**Once you commit an error, it's everyone's problem.** Verify locally first.

### Automated Validation (Future Enhancement)

A pre-commit Git hook should enforce:
```bash
# Check for any markdown errors before allowing commit
Ctrl+Shift+M â†’ Must return: "No errors found"
```

---

## Critical Documentation Relationships

```
.github/copilot-instructions.md (MAIN REFERENCE)
    â†“
    â”œâ”€â†’ 01 project definition
    â”œâ”€â†’ 02 infrastructure setup
    â”œâ”€â†’ 03 db_schema.sql
    â”œâ”€â†’ 04 standards guide
    â”œâ”€â†’ 05 functionality guide
    â”œâ”€â†’ 06 ui technical specs
    â”œâ”€â†’ 07 engine logic specs
    â”œâ”€â†’ 08 devops deployment
    â””â”€â†’ 09 llm prompts config
```

**Golden Rule**: If you make a change to ANY implementation file, update the corresponding doc section within 24 hours.

---

## Documentation Quality Checklist

Use this checklist before committing any documentation changes:

- [ ] **Accuracy**: Information matches actual code/architecture
- [ ] **Completeness**: All necessary details included (no "fill this in later")
- [ ] **Clarity**: Non-technical readers can understand intent
- [ ] **Examples**: Real examples from codebase where helpful
- [ ] **Links**: All cross-references use correct markdown links
- [ ] **Formatting**: Consistent markdown structure, tables, code blocks
- [ ] **Security**: No secrets, passwords, or private keys included
- [ ] **Version**: Header includes last update date
- [ ] **Audience**: Stated audience matches content complexity
- [ ] **Scope**: Clearly defines what's IN and OUT of scope

---

## Key Decision Points (Version Control)

These decisions are documented and should not change without team consensus:

### Architecture Decisions
- [x] Dual-service system (App + Engine) with network isolation
- [x] RLS-enforced multi-tenancy
- [x] Async job pattern with exponential backoff polling
- [x] Ollama for local LLM (proprietary IP protection)

### Data Decisions
- [x] Responsive web MVP (mobile via responsive design)
- [x] Direct health data entry (no external API integration yet)
- [x] User custom questions stored in JSONB (flexible, not encrypted)
- [x] 4-day data retention for cognitive state/answers

### Security Decisions
- [x] Password min 12 chars, 1 upper, 1 lower, 1 digit, 1 special
- [x] JWT for stateless auth
- [x] RLS in database, not application logic
- [x] Environment variables for secrets (not .env in Git)
- [x] Rate limiting on auth endpoints (TBD: exact limits)

### Monetization Decisions
- [x] Free with ads (MVP)
- [x] Billing/tier structure TBD (Phase 2+)
- [x] No data export at this stage
- [x] Professional access via explicit grants (not general licensing)

---

## Known Gaps (To Be Addressed)

### Before Build Starts
- [ ] **Email Service**: Specify provider (SendGrid, AWS SES, etc.) and integration
- [ ] **Rate Limiting**: Define exact limits per endpoint (e.g., 5 auth attempts / 15 min)
- [ ] **Testing Strategy**: Unit test patterns, integration test approach, test fixtures
- [ ] **Ad Strategy**: Where/how ads appear, tracking/analytics approach
- [ ] **Frontend Component Structure**: Vue 3 folder hierarchy, component naming

### During Build
- [ ] **CI/CD Pipeline**: GitHub Actions workflow (build, test, deploy stages)
- [ ] **Monitoring/Logging**: ELK stack, APM tool selection, alerting rules
- [ ] **Session Management**: JWT expiration times, refresh token strategy
- [ ] **CORS Configuration**: Allowed origins for each environment
- [ ] **Cache Strategy**: Redis usage patterns, cache invalidation

### Phase 2+ (Not Required for MVP)
- [ ] **API Versioning**: Version strategy as API evolves
- [ ] **GraphQL**: Consider GraphQL alongside REST (future optimization)
- [ ] **WebSocket**: Real-time chat with advisors (if needed)
- [ ] **Mobile App Specs**: iOS/Android-specific requirements
- [ ] **Analytics**: User behavior tracking, anonymized insights

---

## Error Codes Inventory

### Authentication (401)
- `ERR_AUTH_FAILED` - General authentication failure
- `ERR_TOKEN_EXPIRED` - JWT expired
- `ERR_INVALID_CREDENTIALS` - Wrong username/password

### Authorization (403)
- `ERR_INSUFFICIENT_PERMISSIONS` - RLS violation
- `ERR_GRANT_REVOKED` - Professional access revoked

### Validation (422)
- `ERR_VALIDATION_FAILED` - One or more fields invalid
- `ERR_MISSING_REQUIRED_FIELD` - Required field not provided
- `ERR_INVALID_EMAIL` - Email format invalid
- `ERR_PASSWORD_TOO_WEAK` - Password doesn't meet strength requirements
- `ERR_USERNAME_TOO_SHORT` - Username < 3 chars
- `ERR_IDENTITY_STATEMENT_TOO_LONG` - > 500 chars
- `ERR_CONTENT_TOO_LONG` - Dream/journal > 5000 chars
- `ERR_INVALID_METRIC_VALUE` - Health metric outside valid range

### Conflict (409)
- `ERR_USERNAME_EXISTS` - Username already registered
- `ERR_EMAIL_EXISTS` - Email already registered
- `ERR_DUPLICATE_DAILY_ANSWER` - User already answered question today

### Rate Limit (429)
- `ERR_RATE_LIMIT_EXCEEDED` - Too many requests

### Server Error (500)
- `ERR_INTERNAL_SERVER_ERROR` - Generic server error
- `ERR_DATABASE_ERROR` - Database connection/query error
- `ERR_LLM_UNAVAILABLE` - Ollama service unavailable

### Service Unavailable (503)
- `ERR_ENGINE_UNAVAILABLE` - Cognitive Engine service down
- `ERR_SERVICE_DEGRADED` - Reduced functionality

---

## Documentation Files Checklist

Before building, ensure these files exist and are complete:

- [x] 01 project definition.md (92 lines)
- [x] 02 infrastructure setup.md (102 lines)
- [x] 03 db_schema.sql (649 lines)
- [x] 04 standards guide.md (200+ lines)
- [x] 05 functionality guide.md (141 lines)
- [x] 06 ui technical specifications.md (324 lines)
- [x] 07 engine logic specifications.md (131 lines)
- [x] 08 devops deployment guide.md (500+ lines)
- [x] 09 llm prompts advisor config.md (400+ lines)
- [x] 10 engine api reference.md (350+ lines)
- [x] .github/copilot-instructions.md (500+ lines)

**Total Documentation**: ~3,500+ lines providing complete system specification

---

## How to Use This Manifest

1. **Before each development session**: Review the relevant tier docs for your task
2. **After implementing a feature**: Update the corresponding doc section + this manifest
3. **When unsure about a pattern**: Check the standards guide (04) first
4. **Before deploying**: Review the DevOps guide (08) and error handling section
5. **For AI agents**: Start with copilot-instructions.md, then dive into specific docs

---

## Contact & Ownership

| Role | Responsibility | Updates |
|------|-----------------|---------|
| **Product Owner** | Business requirements (docs 01, 05) | As features evolve |
| **Architects** | System design (docs 02, 04, 07) | During design phase |
| **Backend Developers** | API/Engine specs (docs 06, 07) | During implementation |
| **DevOps Engineer** | Deployment & ops (docs 02, 08) | As infrastructure changes |
| **AI/Prompt Engineer** | Prompt templates (doc 09) | As models evolve |

---

**Remember**: Documentation is the contract between intention and implementation. Keep it current, specific, and actionable.
