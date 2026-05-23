# TerraShield AI — backend + geo-engine image
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System deps for geospatial wheels (geopandas/shapely/pyproj) kept minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the geo-engine first (changes least often -> better layer caching).
COPY geo-engine/ ./geo-engine/
RUN pip install ./geo-engine

# Then the backend.
COPY backend/ ./backend/
RUN pip install ./backend

WORKDIR /app/backend
EXPOSE 8000

# Cloud Run / generic: honour $PORT if provided.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
