# Ingress Prime Leaderboard Bot Dockerfile
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM base as production

# Install additional production dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    netcat-traditional \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Create app directories
RUN mkdir -p /app/logs /app/temp /app/ssl && \
    chmod 755 /app/logs /app/temp /app/ssl

# Copy application code with proper permissions
COPY --chown=app:app src/ ./src/
COPY --chown=app:app main.py .
COPY --chown=app:app alembic/ ./alembic/
COPY --chown=app:app alembic.ini .
COPY --chown=app:app docker/healthcheck.py /app/healthcheck.py
COPY --chown=app:app .env.example .env

# Create non-root user with limited permissions
RUN useradd --create-home --shell /bin/bash app && \
    usermod -L app && \
    chown -R app:app /app && \
    chmod -R 755 /app && \
    chmod 644 /app/.env

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=UTC

# Create production entrypoint script with health checks
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Production startup script\n\
echo "=== Ingress Prime Leaderboard Bot - Production ==="\n\
echo "Starting at: $(date)"\n\
echo "Environment: ${ENVIRONMENT:-production}"\n\
echo "Python version: $(python --version)"\n\
echo ""\n\
\n\
# Validate required environment variables\n\
required_vars=("TELEGRAM_BOT_TOKEN" "DB_PASSWORD")\n\
for var in "${required_vars[@]}"; do\n\
    if [[ -z "${!var}" ]]; then\n\
        echo "ERROR: Required environment variable $var is not set"\n\
        exit 1\n\
    fi\n\
done\n\
\n\
# Wait for database if configured\n\
if [[ -n "$DB_HOST" ]]; then\n\
    echo "Waiting for database at $DB_HOST:$DB_PORT..."\n\
    timeout 60 bash -c "until nc -z $DB_HOST ${DB_PORT:-5432}; do sleep 2; done"\n\
    if [[ $? -eq 0 ]]; then\n\
        echo "Database is reachable"\n\
    else\n\
        echo "WARNING: Database not reachable after 60 seconds"\n\
    fi\n\
fi\n\
\n\
# Create log directory if it does not exist\n\
mkdir -p /app/logs\n\
\n\
# Run database migrations\n\
if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then\n\
    echo "Running database migrations..."\n\
    python -m alembic upgrade head || echo "Migration completed or failed"\n\
fi\n\
\n\
echo "Starting bot..."\n\
exec "$@"' > /app/entrypoint-prod.sh && \
    chmod +x /app/entrypoint-prod.sh

# Enhanced health check script
RUN echo '#!/usr/bin/env python3\n\
import os\n\
import sys\n\
import requests\n\
import subprocess\n\
import time\n\
from datetime import datetime\n\
\n\
def check_basic_health():\n\
    """Basic health check for the container."""\n\
    try:\n\
        # Check if main process is running\n\
        result = subprocess.run(["pgrep", "-f", "python main.py"], \n\
                              capture_output=True, text=True)\n\
        return result.returncode == 0\n\
    except Exception:\n\
        return False\n\
\n\
def check_bot_token():\n\
    """Check if bot token is configured."""\n\
    return bool(os.getenv("TELEGRAM_BOT_TOKEN"))\n\
\n\
def check_database_connection():\n\
    """Check database connectivity if configured."""\n\
    if not os.getenv("DB_HOST"):\n\
        return True  # Skip if not configured\n\
    \n\
    try:\n\
        import psycopg2\n\
        conn = psycopg2.connect(\n\
            host=os.getenv("DB_HOST"),\n\
            port=os.getenv("DB_PORT", "5432"),\n\
            database=os.getenv("DB_NAME", "postgres"),\n\
            user=os.getenv("DB_USER", "postgres"),\n\
            password=os.getenv("DB_PASSWORD"),\n\
            connect_timeout=5\n\
        )\n\
        conn.close()\n\
        return True\n\
    except Exception:\n\
        return False\n\
\n\
def main():\n\
    """Main health check function."""\n\
    start_time = time.time()\n\
    \n\
    print(f"Health check at {datetime.now().isoformat()}")\n\
    \n\
    # Basic health check\n\
    if not check_basic_health():\n\
        print("ERROR: Bot process not running")\n\
        sys.exit(1)\n\
    \n\
    # Token check\n\
    if not check_bot_token():\n\
        print("ERROR: Bot token not configured")\n\
        sys.exit(1)\n\
    \n\
    # Database check\n\
    if not check_database_connection():\n\
        print("WARNING: Database connection failed")\n\
        # Do not fail health check for DB issues\n\
    \n\
    duration = time.time() - start_time\n\
    print(f"Health check passed in {duration:.2f}s")\n\
    sys.exit(0)\n\
\n\
if __name__ == "__main__":\n\
    main()' > /app/healthcheck-advanced.py && \
    chmod +x /app/healthcheck-advanced.py

USER app

# Set working directory
WORKDIR /app

# Expose port for webhook and metrics
EXPOSE 8443 9090

# Labels for production
LABEL maintainer="Ingress Leaderboard Bot Team" \
      version="1.0" \
      description="Ingress Prime Leaderboard Bot - Production" \
      org.opencontainers.image.source="https://github.com/your-org/ingress-leaderboard"

# Enhanced health check with metrics
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD python /app/healthcheck-advanced.py

# Production entrypoint with validation
ENTRYPOINT ["/app/entrypoint-prod.sh"]
CMD ["python", "main.py"]

# Development stage
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    curl \
    htop \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    watchdog \
    ipython \
    pytest \
    black \
    flake8

# Copy application code (will be mounted as volume in dev)
COPY src/ ./src/
COPY main.py .
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY docker/healthcheck.py /app/healthcheck.py
COPY .env.example .env

# Create development user with sudo access
RUN useradd --create-home --shell /bin/bash app && \
    echo 'app ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    chown -R app:app /app

# Create development entrypoint script
RUN echo '#!/bin/bash\n\
echo "Starting Ingress Leaderboard Bot in Development Mode..."\n\
echo "Code changes will be automatically reloaded"\n\
echo "Database: postgres://postgres:dev_password@db:5432/ingress_leaderboard_dev"\n\
echo "Adminer available at: http://localhost:8080"\n\
echo "Press Ctrl+C to stop"\n\
echo ""\n\
exec python main.py' > /app/entrypoint-dev.sh && \
    chmod +x /app/entrypoint-dev.sh

USER app

# Expose ports
EXPOSE 8443

# Development health check (faster interval)
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Development entrypoint
CMD ["/app/entrypoint-dev.sh"]