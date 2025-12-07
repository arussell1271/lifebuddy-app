# Dockerfile.app (The Body - Public Facing)
# CRITICAL: ONLY includes dependencies and code for the App Service (e.g., no Engine code). 
# Stage 1: builder (Used for compilation and dependency installation) [cite: 2]
FROM python:3.11-slim-bullseye AS builder

# Install necessary system dependencies for building native Python packages (e.g., psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libpq-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set the consistent working directory in the container
WORKDIR /usr/src/app

# CRITICAL: Copy and install ONLY App dependencies
COPY ./app/app_requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# CRITICAL: Copy only the SHARED and APP code
COPY ./shared /usr/src/app/shared
COPY ./app /usr/src/app/app

# --------------------------------------------------------------------------------------

# Stage 2: runner (The final, minimal image for production/runtime) [cite: 3]
FROM python:3.11-slim-bullseye AS runner

# Install only essential runtime dependencies (libpq5 is the runtime dependency for libpq-dev)
RUN apt-get update && apt-get install -y \
    libpq5 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set the consistent working directory
WORKDIR /usr/src/app

# Copy the installed Python dependencies from the builder stage (libraries)
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# CRITICAL FIX: Copy the executables (like 'gunicorn', 'uvicorn') from the builder stage
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the application code and entrypoints
COPY --from=builder /usr/src/app/app /usr/src/app/app

# Default command for the App Service
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]