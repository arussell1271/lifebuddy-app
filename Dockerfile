# Stage 1: builder (Used for compilation and dependency installation)
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

# CRITICAL: Copy and install App dependencies (must be stripped of DB/AI libs by the user)
COPY ./app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# CRITICAL: Copy and install Engine dependencies (must contain DB/AI libs like psycopg2-binary, pgvector-python)
# ASSUMPTION: You have created the file: ./engine/requirements.txt
COPY ./engine/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core application and engine code
COPY ./app /usr/src/app/app
COPY ./engine /usr/src/app/engine

# --------------------------------------------------------------------------------------

# Stage 2: runner (The final, minimal image for production/runtime)
FROM python:3.11-slim-bullseye AS runner

# Install only essential runtime dependencies (libpq5 is the runtime dependency for libpq-dev)
RUN apt-get update && apt-get install -y \
    libpq5 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set the consistent working directory
WORKDIR /usr/src/app

# Copy the installed Python dependencies from the builder stage
# This copies ALL dependencies (App and Engine) for the multi-service image
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copy the application code and entrypoints
COPY --from=builder /usr/src/app/app /usr/src/app/app
COPY --from=builder /usr/src/app/engine /usr/src/app/engine

# Expose the ports specified in the docker-compose commands
EXPOSE 8000 8001

# NOTE: The CMD is set by the docker-compose service definition (e.g., gunicorn app.main:app)