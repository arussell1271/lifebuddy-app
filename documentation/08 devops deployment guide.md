# 🚀 DevOps & Deployment Guide

**File Path:** 08 devops deployment guide.md  
**Audience:** DevOps Engineers, Full-Stack Developers, Infrastructure Team.

---

## Purpose

Defines the complete DevOps workflow, from local development through production deployment, emphasizing **ease of build** and **strong security**.

---

## I. Local Development Workflow

### A. Prerequisites

- Docker Desktop (with Docker Compose)
- PowerShell 5.1+ (Windows) or Bash (Linux/macOS)
- Git
- Code editor (VS Code recommended)

### B. Initial Setup

```powershell
# Clone the repository
git clone https://github.com/arussell1271/lifebuddy-app.git
cd lifebuddy-app

# Create environment files (DO NOT commit to Git)
copy .env.dev.example .env.dev
copy .env.prod.example .env.prod

# Edit .env files with your secrets
# Generate JWT_SECRET_KEY: openssl rand -hex 32
```

### C. Development Startup

```powershell
# From repository root, using docker_manager.ps1 script
.\scripts\docker_manager.ps1 -Action rebuild -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev

# Monitor startup
docker compose logs -f

# Wait for services to be ready (~30 seconds)
# Check readiness:
curl http://localhost:8000/docs  # App API Swagger
curl http://localhost:8001/docs  # Engine API Swagger
```

### D. Stopping Services

```powershell
# Stop (preserves data volumes)
.\scripts\docker_manager.ps1 -Action stop -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev

# Remove all project containers/volumes (use with caution)
.\scripts\docker_manager.ps1 -Action remove_project -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev
```

### E. Pulling Ollama Model

```powershell
# After initial startup, pull the Mistral model
.\scripts\docker_manager.ps1 -Action pull_mistral -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev

# Verify model is available
docker exec ollama ollama list
```

---

## II. Database Management

### A. Backup Workflow (Preserves Data)

```powershell
# Backup development database
.\scripts\docker_transfer.ps1 -Direction From -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev

# Creates: ./backups/postgres_backup_dev.tar.gz
# File size: ~10-50MB (depends on data volume)
```

### B. Restore Workflow

```powershell
# Restore from backup
.\scripts\docker_transfer.ps1 -Direction To -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev

# Restarts services and verifies data integrity
```

### C. Database Shell Access (Development Only)

```bash
# Connect to PostgreSQL directly
psql -h localhost -U lifebuddy_rw -d postgres -p 5432

# Password: (from .env.dev POSTGRES_PASSWORD)

# Useful commands:
\dt                 # List all tables
\d users            # Describe users table
SELECT COUNT(*) FROM users;  # Count users
```

### D. RLS Testing

```sql
-- Set RLS context for user_id
SET app.current_user_id = 'user-uuid-here';

-- Query with RLS enforced
SELECT * FROM actionable_items;  -- Only returns items for set user_id
```

---

## III. Environment Variable Management

### A. .env.dev Structure

```bash
# === POSTGRES (Development Database) ===
POSTGRES_DB=postgres
POSTGRES_USER=lifebuddy_rw
POSTGRES_PASSWORD=dev_password_change_this
POSTGRES_ROOT_PASSWORD=postgres_root_pass_change_this

# === JWT Configuration ===
JWT_SECRET_KEY=your_secret_key_here_min_32_chars  # Use: openssl rand -hex 32
JWT_ALGORITHM=HS256

# === App Service Config ===
APP_SECRET_KEY=app_internal_key_min_32_chars
DATABASE_URL=postgresql://lifebuddy_rw:dev_password@lifebuddy-db:5432/postgres

# === Engine Service Config ===
ENGINE_DATABASE_URL=postgresql://cognitive_engine_full:engine_pass@lifebuddy-db:5432/postgres
ENGINE_REDIS_URL=redis://message-broker:6379

# === Ollama (LLM) Config ===
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=mistral
```

### B. .env.prod Structure

```bash
# === POSTGRES (Production Database) ===
POSTGRES_DB=postgres
POSTGRES_USER=lifebuddy_rw
POSTGRES_PASSWORD=secure_prod_password_32_chars_min  # Use: openssl rand -hex 32
POSTGRES_ROOT_PASSWORD=secure_root_password

# === JWT Configuration (MUST use secure random) ===
JWT_SECRET_KEY=secure_random_key_min_32_chars  # openssl rand -hex 32
JWT_ALGORITHM=HS256

# === App Service Config ===
APP_SECRET_KEY=secure_internal_key_min_32_chars  # openssl rand -hex 32
DATABASE_URL=postgresql://lifebuddy_rw:secure_prod_password@prod_db:5432/postgres

# === Engine Service Config ===
ENGINE_DATABASE_URL=postgresql://cognitive_engine_full:secure_engine_pass@prod_db:5432/postgres
ENGINE_REDIS_URL=redis://message-broker:6379

# === Ollama (LLM) Config ===
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=mistral

# === Security Headers (Optional - for reverse proxy) ===
CORS_ALLOWED_ORIGINS=https://yourdomain.com
SECURE_COOKIES=true
HSTS_MAX_AGE=31536000
```

### C. Secret Generation Best Practices

```powershell
# PowerShell: Generate secure random string
$RandomBytes = [byte[]]::new(32)
$RNG = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
$RNG.GetBytes($RandomBytes)
$RandomString = [System.Convert]::ToBase64String($RandomBytes)
Write-Host $RandomString

# Or use OpenSSL (cross-platform)
openssl rand -hex 32

# NEVER commit .env files to Git
```

### D. .gitignore Protection

Ensure `.gitignore` contains:

```
.env.dev
.env.prod
.env.cognitive
*.env
.DS_Store
__pycache__/
*.pyc
venv/
node_modules/
.vscode/settings.json
```

---

## IV. Service Health Checks

### A. App Service Health

```bash
# Check API is responding
curl -X GET http://localhost:8000/docs

# Check health endpoint (if implemented)
curl -X GET http://localhost:8000/api/v1/health

# Expected response: 200 OK
```

### B. Engine Service Health

```bash
# Check API is responding
curl -X GET http://localhost:8001/docs

# Expected response: 200 OK
```

### C. Database Health

```bash
# Check PostgreSQL is running
docker exec lifebuddy-db pg_isready -h localhost -U lifebuddy_rw

# Expected output: accepting connections
```

### D. Redis Health

```bash
# Check Redis is running
docker exec message-broker redis-cli ping

# Expected output: PONG
```

### E. Ollama Health

```bash
# Check Ollama is running
docker exec ollama ollama list

# Check if Mistral model is loaded
docker exec ollama curl -s http://ollama:11434/api/tags
```

---

## V. Logging & Debugging

### A. Service Logs

```powershell
# View all service logs (follow mode, last 50 lines)
docker compose -f lifebuddy-app.yml --profile dev logs -f --tail=50

# View specific service logs
docker compose logs -f lifebuddy-app       # App service
docker compose logs -f lifebuddy-engine    # Engine service
docker compose logs -f lifebuddy-db        # Database
docker compose logs -f message-broker      # Redis
docker compose logs -f ollama              # LLM

# Save logs to file
docker compose logs > docker_logs.txt
```

### B. Database Logs

```bash
# Connect to PostgreSQL and check logs
psql -h localhost -U lifebuddy_rw -d postgres

# Inside psql:
SELECT pg_current_logfile();  -- Show log file location
SHOW log_statement;            -- Check what's being logged
```

### C. Application-Level Logging

Structure logs as JSON for easy parsing:

```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "ERROR",
  "service": "app",
  "user_id": "uuid-here",
  "error_code": "ERR_DATABASE_ERROR",
  "message": "Failed to fetch user preferences",
  "trace_id": "req_abc123xyz"
}
```

---

## VI. Production Deployment Strategy

### A. Pre-Deployment Checklist

- [ ] All `.env.prod` variables set with secure values (use `openssl rand -hex 32`)
- [ ] Database migrations run and verified
- [ ] Ollama Mistral model pulled and available
- [ ] SSL/TLS certificates configured
- [ ] Backup of current database taken
- [ ] Health checks pass for all services
- [ ] Documentation updated in Git

### B. Deployment Steps

```powershell
# 1. Backup current production data
.\scripts\docker_transfer.ps1 -Direction From -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName prod

# 2. Pull latest code changes
git pull origin main

# 3. Rebuild services with new code
.\scripts\docker_manager.ps1 -Action rebuild -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName prod

# 4. Run database migrations (if any)
docker exec lifebuddy-engine alembic upgrade head  # If using Alembic

# 5. Verify health checks
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health

# 6. Monitor logs for errors
docker compose -f lifebuddy-app.yml --profile prod logs -f --tail=100

# 7. Run smoke tests (optional)
# ./scripts/smoke_tests.sh
```

### C. Rollback Procedure

If deployment fails:

```powershell
# 1. Stop current services
.\scripts\docker_manager.ps1 -Action stop -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName prod

# 2. Restore database from backup
.\scripts\docker_transfer.ps1 -Direction To -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName prod

# 3. Checkout previous version
git checkout <previous_commit_hash>

# 4. Rebuild with previous code
.\scripts\docker_manager.ps1 -Action rebuild -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName prod

# 5. Verify services are healthy
curl http://localhost:8000/api/v1/health
curl http://localhost:8001/api/v1/health
```

---

## VII. Scaling Considerations (Future)

### A. Horizontal Scaling (Multiple App Instances)

```yaml
# docker-compose.yml modification for production
services:
  lifebuddy-app:
    deploy:
      replicas: 3  # Multiple instances
    ports:
      - "8000-8002:8000"  # Map to different ports
```

### B. Load Balancing

Use Nginx or HAProxy in front of App service:

```nginx
upstream app_upstream {
    server lifebuddy-app:8000;
    server lifebuddy-app:8001;
    server lifebuddy-app:8002;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://app_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### C. Database Scaling

- **Read Replicas**: PostgreSQL replication for read-heavy workloads
- **Partitioning**: Partition large tables like `documents`, `health_metrics` by user_id
- **Connection Pooling**: PgBouncer between App and Database

---

## VIII. Security Hardening Checklist

### A. Network Security

- [ ] Firewall: Only expose ports 80 (HTTP) and 443 (HTTPS) to public
- [ ] App Service (8000): Only accessible from frontend network or reverse proxy
- [ ] Engine Service (8001): Only accessible from core-network (internal)
- [ ] Database (5432): Only accessible from Engine/App on core-network
- [ ] Redis (6379): Only accessible from core-network

### B. Data Security

- [ ] Enable PostgreSQL SSL connections (`sslmode=require` in connection strings)
- [ ] Enable encryption at rest (file-system level or TDE if available)
- [ ] Hash passwords using bcrypt (min 10 rounds)
- [ ] Disable JWT in logs (redact from audit logs)

### C. Application Security

- [ ] HTTPS/TLS enforced (redirect HTTP to HTTPS)
- [ ] CORS configured to specific origins (not `*`)
- [ ] Rate limiting on auth endpoints (max 5 attempts per 15 minutes)
- [ ] CSRF protection on form submissions
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (sanitize user input, use Content-Security-Policy header)

### D. Monitoring & Alerts

- [ ] Error logging with trace IDs for debugging
- [ ] Health check endpoints monitored (uptime monitoring service)
- [ ] Slow query logging (PostgreSQL queries > 1s)
- [ ] Failed login attempts tracked (account lockout after 5 failures)
- [ ] Backup verification (daily test restore)

---

## IX. Maintenance Tasks

### A. Weekly

- [ ] Review logs for errors
- [ ] Backup verification (test restore from backup)
- [ ] Database VACUUM & ANALYZE

### B. Monthly

- [ ] Update Docker base images (`docker pull`)
- [ ] Review and rotate secrets if needed
- [ ] Performance analysis (slow queries, connection pool usage)
- [ ] RLS policy audit (ensure no unintended access)

### C. Quarterly

- [ ] Load testing (simulate 10x normal user load)
- [ ] Security audit (review RLS policies, network isolation)
- [ ] Disaster recovery drill (test full restoration)

---

## X. PowerShell Script Usage

### A. docker_manager.ps1

```powershell
# Syntax:
.\scripts\docker_manager.ps1 -Action <action> -ComposeFilePath <path> -ProfileName <profile>

# Actions:
rebuild          # Rebuild and start all services
pull_mistral     # Pull Mistral model into Ollama
stop             # Stop services (preserves volumes)
remove_all       # Delete all Docker containers/images/volumes (system-wide)
remove_project   # Delete project-specific containers/volumes

# Examples:
.\scripts\docker_manager.ps1 -Action rebuild -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev
.\scripts\docker_manager.ps1 -Action pull_mistral -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev
.\scripts\docker_manager.ps1 -Action stop -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev
```

### B. docker_transfer.ps1

```powershell
# Syntax:
.\scripts\docker_transfer.ps1 -Direction <From|To> -ComposeFilePath <path> -ProfileName <profile>

# Directions:
From             # Backup database to local file
To               # Restore database from local file

# Examples:
.\scripts\docker_transfer.ps1 -Direction From -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev
.\scripts\docker_transfer.ps1 -Direction To -ComposeFilePath ".\lifebuddy-app.yml" -ProfileName dev
```

---

## XI. Troubleshooting Common Issues

### A. "Address already in use" Error

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```

### B. Database Connection Refused

```bash
# Check if database is running
docker ps | grep lifebuddy-db

# Check database logs
docker logs lifebuddy-db

# Verify connection string in .env.dev/.env.prod
```

### C. Ollama Model Not Loading

```bash
# SSH into Ollama container
docker exec -it ollama bash

# Check available models
ollama list

# Pull model manually
ollama pull mistral

# Check logs
docker logs ollama
```

### D. RLS Queries Returning Empty

```sql
-- Verify RLS context is set
SHOW app.current_user_id;

-- If empty, set it
SET app.current_user_id = 'your-user-uuid';

-- Retry query
SELECT * FROM actionable_items;
```

---

## XII. Disaster Recovery Plan

### A. Complete Data Loss Scenario

1. **Backup exists**: Restore from backup using `docker_transfer.ps1 -Direction To`
2. **No backup**: Data is lost, restart from schema only:
   - `docker exec lifebuddy-engine psql -U cognitive_engine_full -d postgres -f /path/to/03_db_schema.sql`

### B. Service Corruption Scenario

1. Remove all project containers: `docker_manager.ps1 -Action remove_project`
2. Restore database: `docker_transfer.ps1 -Direction To`
3. Rebuild services: `docker_manager.ps1 -Action rebuild`

### C. Security Breach Scenario

1. Immediately rotate all secrets in `.env.prod`
2. Check logs for unauthorized access
3. Review RLS policies for misconfigurations
4. Force password reset for all users
5. Audit database for unauthorized changes

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Infrastructure Setup](../documentation/02 infratructure setup.md)
- [Database Schema](../documentation/03 db_schema.sql)
