# TerraShield AI — developer shortcuts
.PHONY: install backend frontend test test-geo test-api lint up build geo-assets

install:        ## install geo-engine + backend (editable) and frontend deps
	pip install -e ./geo-engine[dev,stats] -e ./backend[dev]
	cd frontend && npm install

backend:        ## run the FastAPI backend (http://localhost:8000/docs)
	cd backend && python -m uvicorn app.main:app --reload --port 8000

frontend:       ## run the Next.js frontend (http://localhost:3000)
	cd frontend && npm run dev

test: test-geo test-api  ## run all tests

test-geo:
	cd geo-engine && pytest tests -q

test-api:
	cd backend && pytest tests -q

lint:
	ruff check backend/app geo-engine/terrashield_geo

up:             ## full stack via docker compose
	docker compose -f infra/docker-compose.yml up --build

build:          ## build both images
	docker build -f infra/backend.Dockerfile -t terrashield-backend .
	docker build -f infra/frontend.Dockerfile -t terrashield-frontend .

geo-assets:     ## rebuild India GeoJSON + gazetteer from the shapefile
	python scripts/build_geo_assets.py
