# ==========================================
# Stage 1: Build the React + TypeScript frontend
# ==========================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source and compile production bundle
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Python production runtime
# ==========================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install minimal OS dependencies for psycopg and pdf generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Python environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000 \
    APP_ENV=production

# Install Python production dependencies with reproducible constraints
COPY backend/requirements.txt ./requirements.txt
COPY backend/constraints.txt ./constraints.txt
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

# Copy Python backend code and migrations
COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/alembic.ini ./alembic.ini

# Copy compiled frontend assets from Stage 1 into /app/static
COPY --from=frontend-builder /app/frontend/dist ./static

# Create non-root system user and group
RUN groupadd --system --gid 10001 appgroup && \
    useradd --system --uid 10001 --gid appgroup --no-create-home appuser

# Set ownership and secure read/execute permissions for application files
RUN chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser:appgroup

# Expose dynamic application port (Render assigns $PORT)
EXPOSE 8000

# Start Uvicorn server honoring dynamic $PORT and binding to 0.0.0.0
# Note: Migrations are executed via Render preDeployCommand, not container startup
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
