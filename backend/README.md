# TerraShield AI — Backend

FastAPI orchestration service. Thin by design: it validates requests, caches and
rate-limits, and delegates all geospatial compute to the `terrashield_geo`
package (the EarthData Engine).

## Run

```bash
pip install -e ../geo-engine -e .[dev]
python -m uvicorn app.main:app --reload --port 8000
# Interactive API docs -> http://localhost:8000/docs
# Tip: use `python -m uvicorn` (the bare `uvicorn` needs the pip Scripts dir on PATH).
```

Runs in **demo mode** without Earth Engine credentials. Configure via env
(prefix `TERRASHIELD_`) — see [`../.env.example`](../.env.example).

## Layout

```
app/
├── main.py              app factory: middleware, routers, lifespan (GEE init)
├── core/                config · logging (request-id) · cache (TTL) · ratelimit
├── api/
│   ├── deps.py          shared dependencies (rate limiter)
│   └── routes/          health · earthdata · flood · climate · drought ·
│                        infra · optimize · copilot
├── schemas/             pydantic request models + shared response models
└── services/            llm.py (Llama: groq/ollama) · copilot.py (agent)
```

## Endpoints (prefix `/api/v1`)

| Group | Routes |
|-------|--------|
| FloodAI | `POST /flood/susceptibility` · `/flood/sar-extent` · `/flood/road-risk` |
| ClimateLens | `GET /climate/scenarios` · `POST /climate/projection` · `/climate/anomaly` |
| DroughtAI | `POST /drought/spi` · `/drought/vegetation` |
| InfraRisk | `POST /infra/exposure` |
| ResilienceOR | `GET /optimize/ahp/default` · `POST /optimize/{ahp,topsis,shelters,evacuation,mitigation}` |
| GeoCopilot | `GET /copilot/tools` · `POST /copilot/ask` |
| EarthData | `GET /earthdata/{status,datasets,basemaps}` · `POST /earthdata/aoi/validate` |
| system | `GET /health` · `/version` · `/cache/stats` |

## Tests

```bash
pytest tests -q
```
