# Stage 1: builder (Used for dev, with system dependencies for package compilation)
FROM python:3.11-slim-bullseye AS builder

# Install necessary system dependencies for building native Python packages
# These are only needed for the compilation step (e.g., pgvector)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libpq-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set the consistent working directory in the container
WORKDIR /usr/src/app

# Install required Python packages (requirements.txt is assumed to be in ./app)
COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the core application and engine code
COPY ./app /usr/src/app/app
COPY ./engine /usr/src/app/engine

# --------------------------------------------------------------------------------------

# Stage 2: runner (Used for prod, a minimal image with only runtime dependencies)
FROM python:3.11-slim-bullseye AS runner

# Install only essential runtime dependencies (libpq5 is the runtime dependency for libpq-dev)
RUN apt-get update && apt-get install -y \
    libpq5 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set the consistent working directory
WORKDIR /usr/src/app

# Copy the installed Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# Copy the core application and engine code
COPY ./app /usr/src/app/app
COPY ./engine /usr/src/app/engine

# Default command (will be overridden by docker-compose for Body and Brain services)
CMD ["python", "app/main.py"]