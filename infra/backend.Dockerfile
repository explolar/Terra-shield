# TerraShield AI — backend + geo-engine image
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# System deps for geospatial wheels (geopandas/shapely/pyproj) kept minimal.
# libgomp1 is the OpenMP runtime required by scikit-learn / xgboost (the [ml] extra).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the geo-engine with "serve,ml" so the image runs LIVE Earth Engine,
# SPI stats, road-graph criticality (/infra/criticality) AND the ML flood-risk
# endpoint (/flood/ml-risk). Plain `./geo-engine` would force DEMO mode.
COPY geo-engine/ ./geo-engine/
RUN pip install "./geo-engine[serve,ml]"

# Then the backend.
COPY backend/ ./backend/
RUN pip install ./backend

WORKDIR /app/backend
EXPOSE 8000

# Cloud Run / generic: honour $PORT if provided.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
