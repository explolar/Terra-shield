# TerraShield AI — Architecture

This document describes the system design: layers, data flow, and the contracts
between them. The north star is a clean separation between **compute**
(geo-engine), **orchestration** (backend), and **experience** (frontend), so any
module can grow independently.

## 1. Layered overview

```mermaid
flowchart TB
    subgraph FE["Frontend · Next.js 14"]
        MAP[Leaflet map workspace]
        PANELS[Module panels<br/>flood · climate · drought · infra]
        COPILOT[GeoCopilot chat]
        CLIENT[Typed API client]
    end

    subgraph BE["Backend · FastAPI (async)"]
        ROUTES[Routers<br/>/flood /climate /drought /infra /copilot /earthdata]
        SVC[Services<br/>per-module orchestration]
        CORE[Core<br/>config · logging · cache · rate-limit]
    end

    subgraph GE["geo-engine · terrashield_geo"]
        GEE[GEE auth + init<br/>graceful demo fallback]
        AOI[AOI utils]
        IDX[Spectral indices]
        FLOOD[Flood compute]
        CLIM[Climate compute]
        DRY[Drought compute]
        INFRA[Infra compute]
        TILES[Tile / mapid serving]
    end

    subgraph EXT["External data"]
        EE[(Google Earth Engine)]
        CMIP[(NEX-GDDP-CMIP6)]
        S1[(Sentinel-1 SAR)]
        CHIRPS[(CHIRPS rainfall)]
        OSM[(OpenStreetMap roads)]
    end

    CLIENT -->|REST JSON/GeoJSON/tileURL| ROUTES
    MAP --> CLIENT
    PANELS --> CLIENT
    COPILOT --> CLIENT
    ROUTES --> SVC --> GE
    CORE -.-> ROUTES
    GEE --> EE
    CLIM --> CMIP
    FLOOD --> S1
    DRY --> CHIRPS
    INFRA --> OSM
```

## 2. Why these boundaries

| Boundary | Rule | Reason |
|----------|------|--------|
| frontend ↔ backend | Only typed REST. No GEE logic in the browser. | Keeps secrets server-side; lets us swap the UI or add a CLI/SDK client. |
| backend ↔ geo-engine | Backend imports the package; never calls GEE directly. | The compute library is reusable (notebooks, batch jobs, other apps) and independently testable. |
| geo-engine ↔ Earth Engine | A single `gee.init()` gateway with a **demo fallback**. | The whole stack runs offline for development and CI; live data is a config flip. |

## 3. Request lifecycle (FloodAI example)

```mermaid
sequenceDiagram
    participant U as User (map)
    participant FE as Frontend
    participant API as FastAPI /flood/susceptibility
    participant SVC as FloodService
    participant GEO as geo-engine.flood
    participant EE as Earth Engine

    U->>FE: draw AOI, set weights, submit
    FE->>API: POST {aoi, weights, rainfall_scenario}
    API->>API: validate (pydantic) · check TTL cache
    API->>SVC: run_susceptibility(request)
    SVC->>GEO: susceptibility(aoi, weights)
    GEO->>EE: build DEM/slope/TWI/drainage/LULC stack
    EE-->>GEO: weighted index image
    GEO-->>SVC: {tile_url, stats, legend}
    SVC-->>API: FloodSusceptibilityResponse
    API-->>FE: JSON (cached)
    FE->>U: overlay tiles + stats panel
```

## 4. Tile serving strategy

We do **not** ship GeoTIFFs to the browser. The geo-engine asks Earth Engine for
a `mapid`/tile-URL template for a styled `ee.Image`, and the backend returns that
URL. Leaflet then streams XYZ tiles directly from Google's edge. This is the same
proven pattern used in the `soil_prop` platform and keeps payloads tiny.

Vector results (flood extent polygons, inaccessible road segments) are returned
as **GeoJSON** with a size guard; large geometries are simplified server-side.

## 5. Cross-cutting concerns

- **Config** — `pydantic-settings`, env-driven, single `Settings` object.
- **Logging** — structured (JSON in prod, pretty in dev), request-id middleware.
- **Caching** — in-process TTL cache keyed by `(endpoint, normalized request)`;
  swappable for Redis in production. GEE calls are expensive — caching is not optional.
- **Rate limiting** — per-IP token bucket on compute endpoints.
- **Errors** — typed error envelope `{error, detail, hint}`; never leak GEE traces.

## 6. Deployment topology (target)

```mermaid
flowchart LR
    GH[GitHub push] --> CI[GitHub Actions<br/>lint · test · build]
    CI --> AR[Artifact Registry]
    AR --> RUN1[Cloud Run · backend]
    AR --> RUN2[Cloud Run · frontend]
    RUN1 -. ADC .-> EE[(Earth Engine)]
    USER[Browser] --> RUN2 --> RUN1
```

Single-region Cloud Run services, Earth Engine via Application Default
Credentials (no auth UI in prod), min-instances=1 to avoid cold starts on the
compute service. See [`infra/`](../infra) and the [roadmap](roadmap.md) Phase 5.
