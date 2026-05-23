# Contributing to TerraShield AI

Thanks for your interest. This guide gets you productive fast.

## Architecture in one line
`frontend` (Next.js) → typed REST → `backend` (FastAPI) → imports `geo-engine`
(`terrashield_geo`) → Google Earth Engine (or deterministic demo mode).

Read [`docs/architecture.md`](docs/architecture.md) and [`docs/engineering.md`](docs/engineering.md) first.

## Setup

```bash
# Python side (geo-engine + backend, editable)
pip install -e ./geo-engine[dev,stats] -e ./backend[dev]
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

No Earth Engine credentials are needed for development — the engine runs in
**demo mode** (deterministic synthetic layers). Set `TERRASHIELD_GEE_PROJECT`
to go live. See [`.env.example`](.env.example).

## Tests (run before every PR)

```bash
cd geo-engine && pytest tests -q     # 22 tests
cd backend    && pytest tests -q     # 10 tests
cd frontend   && npm run build       # must compile with no type errors
```

## Conventions

- **Compute lives in `geo-engine`**, not the backend. The backend orchestrates,
  validates (pydantic), caches, and serves. Never call Earth Engine from a route.
- **Every analytic has a live and a demo path** with the *same* response shape and
  a `source: live|demo` field. New modules must support both.
- **Cite your methods.** Anything scientific gets a reference in the docstring and,
  if user-facing, in `docs/engineering.md`. Keep terms scientifically accurate.
- **Optimization** code goes in `geo-engine/terrashield_geo/optimize.py` with a
  documented complexity and (where relevant) an approximation guarantee.
- Keep functions small; prefer pure functions; type everything.

## Adding a module

1. `geo-engine/terrashield_geo/<module>.py` with live + demo paths.
2. `backend/app/schemas/modules.py` request models.
3. `backend/app/api/routes/<module>.py` router (cache + rate limit).
4. Mount it in `backend/app/main.py`.
5. Tests in both `geo-engine/tests` and `backend/tests`.
6. Frontend panel + `lib/api.ts` client function.
7. Update `docs/modules.md`.
