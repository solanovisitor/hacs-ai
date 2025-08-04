# HACS MCP Server Dockerfile
# Multi-stage build for HACS Healthcare Agent Communication Standard MCP Server

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy UV workspace configuration
COPY pyproject.toml uv.lock ./

# Copy all HACS packages
COPY packages/ packages/

# Install dependencies and HACS packages in development mode
RUN uv sync --all-extras --dev

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/packages/hacs-core/src:/app/packages/hacs-tools/src:/app/packages/hacs-utils/src:/app/packages/hacs-persistence/src:/app/packages/hacs-registry/src:/app/packages/hacs-cli/src"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from base stage
COPY --from=base /app/.venv /app/.venv

# Copy application code
COPY --from=base /app/packages /app/packages
COPY --from=base /app/pyproject.toml /app/uv.lock ./

# Create non-root user for security with home directory
RUN groupadd -r hacsuser && useradd -r -g hacsuser -m hacsuser && \
    mkdir -p /home/hacsuser/.cache && \
    chown -R hacsuser:hacsuser /app /home/hacsuser
USER hacsuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "hacs_utils.mcp.cli", "--host", "0.0.0.0", "--port", "8000"]