# example_root_endpoint.py
# Example FastAPI implementation of the Engine root endpoint with security notice and API listing

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Life Buddy Cognitive Engine",
    description="Internal service - Database and LLM access only",
    version="1.0.0"
)

# HTML template for the landing page (see 10 engine api reference.md for full template)
ROOT_LANDING_PAGE_HTML = """<!DOCTYPE html>
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
            <h2>📡 Available Endpoints (Summary)</h2>
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

            <h3>Synthesis (Core Logic)</h3>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/synthesis/job</span>
                <br><small>Queue synthesis job, returns job_id</small>
            </div>
            <div class="endpoint">
                <span class="method get">GET</span>
                <span class="path">/api/v1/synthesis/job/{job_id}</span>
                <br><small>Poll synthesis job status</small>
            </div>

            <h3>User Data</h3>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/documents</span>
                <br><small>Create dream/journal/spiritual document</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/action-items</span>
                <br><small>Create actionable item</small>
            </div>
            <div class="endpoint">
                <span class="method post">POST</span>
                <span class="path">/api/v1/health-metrics</span>
                <br><small>Log health metric</small>
            </div>

            <p><strong>For complete endpoint listing, see the documentation:</strong></p>
            <ul>
                <li><a href="/docs" target="_blank">Swagger UI (/docs)</a></li>
                <li><a href="/redoc" target="_blank">ReDoc (/redoc)</a></li>
                <li><a href="https://docs.lifebuddy.local/10-engine-api-reference" target="_blank">Full API Reference (10 engine api reference.md)</a></li>
            </ul>
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
            Life Buddy Cognitive Engine v1.0 | Restricted Access
        </p>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """
    Root endpoint (GET /)
    
    Returns an HTML landing page with security notice and API endpoint listing
    when accessed via web browser. This endpoint is NOT meant for API clients,
    but rather for administrators and developers to view service information.
    
    For API integration, use the endpoints listed in the Swagger UI (/docs)
    or check the full Engine API Reference (documentation/10 engine api reference.md).
    """
    return ROOT_LANDING_PAGE_HTML


@app.get("/health", tags=["Health"])
async def health():
    """
    Health check endpoint
    
    Returns 200 OK if the service is running.
    Used by load balancers and monitoring systems.
    
    Response:
        {"status": "ok", "service": "cognitive-engine"}
    """
    return {"status": "ok", "service": "cognitive-engine"}


@app.get("/ready", tags=["Health"])
async def readiness():
    """
    Readiness check endpoint
    
    Verifies that all critical dependencies are available:
    - PostgreSQL database connection
    - Ollama LLM service
    - Redis message broker
    
    Returns 200 OK only if all dependencies are healthy.
    Returns 503 if any dependency is unavailable.
    """
    # Implementation would check:
    # 1. PostgreSQL connection pool
    # 2. Ollama API availability (curl http://ollama:11434/api/tags)
    # 3. Redis connection
    # 4. pgvector extension status
    
    return {
        "status": "ready",
        "service": "cognitive-engine",
        "dependencies": {
            "database": "connected",
            "llm": "available",
            "cache": "available"
        }
    }


# Example of a protected endpoint
from fastapi.security import HTTPBearer, HTTPAuthCredential
from typing import Optional

security = HTTPBearer()


@app.post("/api/v1/auth/login", tags=["Authentication"])
async def login(username: str, password: str):
    """
    User login endpoint
    
    Authenticates user credentials and returns JWT token.
    This endpoint should:
    1. Validate username/password against database
    2. Hash password comparison (bcrypt)
    3. Generate JWT token with proper claims
    4. Log authentication attempt
    5. Rate limit by IP (5 attempts per 15 minutes)
    
    Args:
        username: User's username or email
        password: User's password
    
    Returns:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer",
            "user_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    
    Raises:
        401: Invalid credentials
        429: Rate limit exceeded
    """
    # Implementation here
    pass


@app.get("/api/v1/synthesis/{synthesis_id}", tags=["Synthesis"])
async def get_synthesis(synthesis_id: str, credentials: HTTPAuthCredential = security):
    """
    Retrieve completed synthesis result
    
    Gets the full synthesis result for a completed job.
    RLS is enforced - user can only access their own synthesis.
    
    Args:
        synthesis_id: The synthesis ID returned from POST /api/v1/synthesis/job
        credentials: JWT token in Authorization header
    
    Returns:
        {
            "synthesis_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440001",
            "cultivate_phase": {...},
            "execute_phase": {...},
            "contribute_phase": {...},
            "created_at": "2025-01-15T10:30:00Z",
            "status": "COMPLETE"
        }
    
    Raises:
        401: Unauthorized (invalid/expired token)
        403: Forbidden (RLS violation - not user's synthesis)
        404: Not found
    """
    # Implementation here
    pass


if __name__ == "__main__":
    import uvicorn
    
    # Run with: uvicorn example_root_endpoint:app --host 0.0.0.0 --port 8001 --reload
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
