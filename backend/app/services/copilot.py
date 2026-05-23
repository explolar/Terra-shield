"""GeoCopilot — an agent over TerraShield's own analytics.

Pipeline: parse the natural-language question -> resolve AOI + scenario ->
choose and call a geo-engine tool -> ground a natural-language answer in the real
computed numbers (via Llama if configured, else a deterministic template).

This is intentionally a *grounded* agent: the LLM never invents numbers; it only
phrases the stats the engine produced. v1 uses a deterministic intent router;
swapping in LLM-driven tool selection / RAG is a roadmap item.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from terrashield_geo import aoi as geo_aoi
from terrashield_geo import climate, drought, flood, gee, infra, ml_flood, optimize

from . import llm

# Tiny gazetteer so questions can name a place instead of drawing an AOI.
GAZETTEER: dict[str, list[float]] = {
    "satara": [73.9, 17.5, 74.3, 17.9],
    "pune": [73.7, 18.4, 74.0, 18.7],
    "kolhapur": [74.1, 16.6, 74.4, 16.9],
    "sangli": [74.4, 16.7, 74.8, 17.0],
    "mumbai": [72.75, 18.9, 73.0, 19.3],
    "chennai": [80.1, 12.9, 80.35, 13.2],
    "kerala": [76.0, 9.5, 77.0, 10.5],
    "assam": [91.5, 26.0, 92.5, 26.8],
    "patna": [85.0, 25.5, 85.3, 25.7],
    "delhi": [76.9, 28.4, 77.4, 28.9],
    "bangalore": [77.4, 12.8, 77.8, 13.1],
    "hyderabad": [78.3, 17.3, 78.6, 17.6],
    "ahmedabad": [72.4, 22.9, 72.8, 23.2],
    "guwahati": [91.6, 26.0, 91.9, 26.3],
}
DEFAULT_AOI = {"type": "bbox", "bbox": [77.0, 18.0, 79.0, 20.0]}  # central India


def _load_national_gazetteer() -> dict[str, list[float]]:
    """Load the 492-entry India gazetteer (states + districts) built from the
    official shapefile, so the copilot can resolve any Indian place by name."""
    try:
        import terrashield_geo

        path = Path(terrashield_geo.__file__).parent / "data" / "india_gazetteer.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return {k: v["bbox"] for k, v in data.items()}
    except Exception:
        return {}


# Curated city bboxes override the (coarser) district bboxes for tightness.
PLACES: dict[str, list[float]] = {**_load_national_gazetteer(), **GAZETTEER}


def _resolve_place(ql: str) -> str | None:
    """Longest word-boundary match of a place name in the query."""
    best = None
    for name in PLACES:
        if len(name) < 4:
            continue
        if re.search(r"\b" + re.escape(name) + r"\b", ql):
            if best is None or len(name) > len(best):
                best = name
    return best

CITATIONS = {
    "flood": [
        "Bonafilia et al. (2020), Sen1Floods11, CVPRW",
        "Saaty (1980), Analytic Hierarchy Process",
        "Beven & Kirkby (1979), TWI, Hydrol. Sci. Bull.",
    ],
    "climate": [
        "Thrasher et al. (2022), NEX-GDDP-CMIP6, Scientific Data",
        "O'Neill et al. (2016), SSP scenarios, Geosci. Model Dev.",
        "Zhang et al. (2011), ETCCDI extreme indices, WIREs Clim. Change",
    ],
    "drought": ["McKee et al. (1993), SPI, AMS Conf. Applied Climatology",
                "Kogan (1995), Vegetation Condition Index, Adv. Space Research"],
    "infra": [
        "WorldPop (2018), Bondarenko et al., population modelling",
        "Freeman (1977), betweenness centrality, Sociometry",
    ],
    "weather": ["Open-Meteo (2023), open-data weather forecast API (CC-BY 4.0)"],
    "optimize": [
        "Saaty (1980), Analytic Hierarchy Process",
        "Church & ReVelle (1974), Maximal Covering Location Problem, Papers Reg. Sci.",
        "Nemhauser et al. (1978), submodular greedy (1-1/e) bound, Math. Programming",
        "Dijkstra (1959), shortest paths, Numerische Mathematik",
    ],
}


# --------------------------------------------------------------------------- #
# Tool registry
# --------------------------------------------------------------------------- #
def _tool_flood_susceptibility(aoi, e):
    return flood.susceptibility(aoi, rainfall_scenario=e.get("scenario_rain", "normal"))


def _tool_flood_sar(aoi, e):
    return flood.sar_extent(aoi)


def _tool_flood_road(aoi, e):
    return flood.road_risk(aoi)


def _tool_flood_multiyear(aoi, e):
    r = flood.multiyear(aoi)
    return {
        "module": "flood", "product": "multiyear", "source": r["source"],
        "tile_url": None, "grid": None, "legend": r.get("legend", []),
        "stats": r["stats"], "series": r["series"], "aoi": r.get("aoi", {}),
    }


def _tool_flood_ml(aoi, e):
    r = ml_flood.flood_risk_ml(aoi, model=e.get("ml_model", "gbm"))
    return {
        "module": "flood", "product": "ml_risk", "source": r["source"],
        "tile_url": None, "grid": None, "legend": [],
        "stats": r["metrics"], "model": r["model"], "top_factor": r["top_factor"],
        "feature_importance": r["feature_importance"], "aoi": r.get("aoi", {}),
    }


def _tool_climate(aoi, e):
    return climate.projection(aoi, e.get("ssp", "ssp585"), e.get("variable", "pr"),
                              e.get("horizon", "2050s"))


def _tool_drought_spi(aoi, e):
    return drought.spi(aoi, e.get("spi_scale", 3))


def _tool_drought_veg(aoi, e):
    return drought.vegetation(aoi)


def _tool_infra(aoi, e):
    return infra.exposure(aoi)


def _tool_climate_extremes(aoi, e):
    r = climate.extremes(aoi, e.get("ssp", "ssp585"), e.get("horizon", "2050s"))
    return {
        "module": "climate", "product": "extremes", "source": r["source"],
        "tile_url": None, "grid": None, "legend": [],
        "stats": {i["key"]: i["projected"] for i in r["indices"]},
        "indices": r["indices"], "scenario": r["scenario"], "horizon": r["horizon"],
        "aoi": r["aoi"],
    }


def _tool_infra_criticality(aoi, e):
    return infra.road_criticality(aoi)


def _tool_weather(aoi, e):
    from . import weather

    norm = geo_aoi.normalize(aoi)
    lon, lat = norm["centroid"]
    r = weather.forecast(lat, lon, e.get("days", 7))
    return {
        "module": "weather", "product": "forecast", "source": r["source"],
        "tile_url": None, "grid": None, "legend": [],
        "stats": r["summary"], "daily": r["daily"], "provider": r["provider"],
        "aoi": {"bbox": norm["bbox"], "centroid": norm["centroid"]},
    }


def _tool_opt_shelters(aoi, e):
    r = optimize.shelters_for_aoi(aoi, p=e.get("count", 3), radius_km=e.get("radius_km", 8.0))
    return {
        "module": "optimize", "product": "shelters", "source": gee.mode(),
        "tile_url": None, "grid": r.get("shelters_geojson"),
        "legend": [{"label": "Relief shelter", "color": "#22d3ee"}],
        "stats": {k: r[k] for k in ("coverage_pct", "uncovered_pct", "candidate_sites",
                                    "demand_points", "radius_km") if k in r},
        "or_result": r, "aoi": r.get("aoi", {}),
    }


def _tool_opt_evacuation(aoi, e):
    r = optimize.evacuation_for_aoi(aoi)
    return {
        "module": "optimize", "product": "evacuation", "source": gee.mode(),
        "tile_url": None, "grid": r.get("route_geojson"),
        "legend": [{"label": "Evacuation route", "color": "#10b981"}],
        "stats": {"reachable": r.get("reachable"), "route_km": r.get("route_km"),
                  "segments": r.get("segments"), "crosses_flood": r.get("crosses_flood")},
        "or_result": {k: v for k, v in r.items() if k != "route_geojson"},
        "aoi": r.get("aoi", {}),
    }


def _tool_opt_mitigation(aoi, e):
    r = optimize.mitigation_plan(optimize.DEFAULT_INTERVENTIONS, budget=e.get("budget", 200.0))
    return {
        "module": "optimize", "product": "mitigation", "source": "demo",
        "tile_url": None, "grid": None, "legend": [],
        "stats": {k: r[k] for k in ("total_cost", "total_risk_reduction", "budget",
                                    "budget_used_pct") if k in r},
        "or_result": r, "aoi": {},
    }


TOOLS: dict[str, dict[str, Any]] = {
    "flood_susceptibility": {"fn": _tool_flood_susceptibility, "module": "flood",
                             "desc": "Multi-criteria flood susceptibility map"},
    "flood_sar": {"fn": _tool_flood_sar, "module": "flood",
                  "desc": "Sentinel-1 SAR inundation extent"},
    "flood_road": {"fn": _tool_flood_road, "module": "flood",
                   "desc": "Road / access disruption from flooding"},
    "flood_multiyear": {"fn": _tool_flood_multiyear, "module": "flood",
                        "desc": "Multi-year flood extent trend (2019-2024)"},
    "flood_ml": {"fn": _tool_flood_ml, "module": "flood",
                 "desc": "ML flood-risk classifier (GBM/XGBoost) + SHAP"},
    "climate_projection": {"fn": _tool_climate, "module": "climate",
                           "desc": "CMIP6/SSP future-climate projection"},
    "drought_spi": {"fn": _tool_drought_spi, "module": "drought",
                    "desc": "Standardized Precipitation Index"},
    "drought_vegetation": {"fn": _tool_drought_veg, "module": "drought",
                           "desc": "NDVI/VCI vegetation-stress anomaly"},
    "infra_exposure": {"fn": _tool_infra, "module": "infra",
                       "desc": "Population / infrastructure exposure"},
    "climate_extremes": {"fn": _tool_climate_extremes, "module": "climate",
                         "desc": "ETCCDI extreme-climate indices (heatwave/heavy-rain)"},
    "infra_criticality": {"fn": _tool_infra_criticality, "module": "infra",
                          "desc": "Road-network criticality (edge betweenness)"},
    "weather_forecast": {"fn": _tool_weather, "module": "weather",
                         "desc": "Short-range weather & rainfall forecast (Open-Meteo)"},
    "optimize_shelters": {"fn": _tool_opt_shelters, "module": "optimize",
                          "desc": "Relief-shelter siting (Maximal Covering Location)"},
    "optimize_evacuation": {"fn": _tool_opt_evacuation, "module": "optimize",
                            "desc": "Flood-aware evacuation routing (Dijkstra)"},
    "optimize_mitigation": {"fn": _tool_opt_mitigation, "module": "optimize",
                            "desc": "Budget-constrained mitigation (knapsack)"},
}


def tools_manifest() -> list[dict[str, str]]:
    return [{"name": k, "module": v["module"], "description": v["desc"]} for k, v in TOOLS.items()]


# --------------------------------------------------------------------------- #
# Intent parsing
# --------------------------------------------------------------------------- #
def _parse_entities(q: str) -> dict[str, Any]:
    ql = q.lower()
    e: dict[str, Any] = {}

    # scenario
    if "ssp585" in ql or "ssp5" in ql or "worst case" in ql or "high emission" in ql:
        e["ssp"] = "ssp585"
    elif "ssp245" in ql or "ssp2" in ql or "moderate" in ql:
        e["ssp"] = "ssp245"

    # horizon
    for h in ("2030", "2050", "2080"):
        if h in ql:
            e["horizon"] = f"{h}s"
    if "end of century" in ql or "2100" in ql:
        e["horizon"] = "2080s"

    # climate variable
    if "temperature" in ql or "heat" in ql or "warming" in ql:
        e["variable"] = "tasmax" if "max" in ql or "extreme" in ql else "tas"
    elif "rain" in ql or "precip" in ql or "monsoon" in ql:
        e["variable"] = "pr"

    # rainfall scenario for flood — explicit phrasing first, else derive from SSP
    if "extreme rain" in ql or "cloudburst" in ql or "heavy rain" in ql:
        e["scenario_rain"] = "extreme"
    elif "wet" in ql:
        e["scenario_rain"] = "wet"
    elif e.get("ssp") == "ssp585":
        e["scenario_rain"] = "extreme"
    elif e.get("ssp") == "ssp245":
        e["scenario_rain"] = "wet"

    # SPI scale
    m = re.search(r"(\d+)\s*-?\s*month", ql)
    if m:
        scale = int(m.group(1))
        e["spi_scale"] = scale if scale in (1, 3, 6, 12) else 3

    # OR parameters: shelter count, budget
    mc = re.search(r"(\d+)\s+(?:relief\s+)?(?:shelters?|centres?|centers?)", ql)
    if mc:
        e["count"] = max(1, min(20, int(mc.group(1))))
    mb = re.search(r"budget\s*(?:of|=|:)?\s*\$?\s*([\d,]+)", ql)
    if mb:
        e["budget"] = float(mb.group(1).replace(",", ""))

    # ML model choice
    if "xgboost" in ql or "xgb" in ql:
        e["ml_model"] = "xgboost"
    elif "random forest" in ql or "random-forest" in ql:
        e["ml_model"] = "random_forest"

    # place — resolve against the full national gazetteer (longest match wins)
    place = _resolve_place(ql)
    if place:
        e["place"] = place
        e["aoi"] = {"type": "bbox", "bbox": PLACES[place]}
    return e


def _choose_tool(q: str) -> str:
    ql = q.lower()
    has = lambda *ws: any(w in ql for w in ws)  # noqa: E731

    # ResilienceOR intents take priority — they are explicit decision questions.
    if has("shelter", "relief cent", "where to place", "where should", "siting", "locate cent"):
        return "optimize_shelters"
    if has("evacuat", "escape route", "safe route", "evacuation"):
        return "optimize_evacuation"
    if has("budget", "mitigation", "invest", "spend", "prioriti"):
        return "optimize_mitigation"
    if has("forecast", "weather", "next week", "next few days", "rain tomorrow",
            "upcoming rain", "rainfall forecast", "will it rain"):
        return "weather_forecast"
    # Road criticality must beat flood_road (both mention "road").
    if has("critical road", "road criticality", "most critical", "network critical",
            "betweenness", "important road", "key road"):
        return "infra_criticality"
    if has("road", "access", "cut off", "stranded"):
        return "flood_road"
    if has("inundation", "sar", "satellite flood", "flood extent", "submerged"):
        return "flood_sar"
    if has("machine learning", "ml model", "ml risk", "train a model", "classifier",
            "shap", "xgboost", "gradient boost", "random forest", "predict flood"):
        return "flood_ml"
    if has("multi-year", "multiyear", "over the years", "yearly flood", "flood trend",
            "trend over", "flood history", "past years", "annual flood", "year on year"):
        return "flood_multiyear"
    if has("heatwave", "heat wave", "hot days", "extreme index", "extreme indices",
            "climate extreme", "rx1day", "consecutive dry", "extreme heat",
            "rainfall indices", "precipitation indices", "extreme precipitation"):
        return "climate_extremes"
    if has("population", "people exposed", "exposure", "buildings", "infrastructure", "settlement"):
        return "infra_exposure"
    # An explicit hazard subject wins over a generic climate/future trigger:
    # "how will FLOOD risk change under SSP585" -> flood (with SSP-derived rainfall).
    if has("flood", "flooding", "waterlog", "inundat"):
        return "flood_susceptibility"
    if has("vegetation", "ndvi", "crop stress", "greenness"):
        return "drought_vegetation"
    if has("drought", "spi", "rainfall deficit", "dry spell"):
        return "drought_spi"
    if has("ssp", "future", "projection", "climate change", "2050", "2080", "2030",
            "warming", "temperature", "rainfall", "precip", "by 20"):
        return "climate_projection"
    return "flood_susceptibility"


# --------------------------------------------------------------------------- #
# Answer composition
# --------------------------------------------------------------------------- #
def _template_answer(tool: str, entities: dict, result: dict) -> str:
    place = entities.get("place", "the selected area").title() if entities.get("place") else "the selected area"
    s = result.get("stats", {})
    src = "live Earth Engine data" if result["source"] == "live" else "demo data (no GEE credentials configured)"

    if tool == "flood_susceptibility":
        return (
            f"Flood susceptibility for {place}: mean index {s.get('mean')}, "
            f"with about {s.get('high_risk_pct', s.get('high_risk_area_km2'))}% of the area in the "
            f"high/very-high class. Driven by the weighted overlay of elevation, slope, TWI, "
            f"drainage proximity, rainfall and land use. Based on {src}."
        )
    if tool == "flood_sar":
        return (
            f"SAR-derived inundation for {place}: roughly {s.get('flooded_area_km2')} km² "
            f"({s.get('flooded_pct')}%) detected as open water/flooded. Based on {src}."
        )
    if tool == "flood_road":
        return (
            f"Road disruption for {place}: {s.get('roads_disrupted')} of {s.get('roads_total')} "
            f"modelled segments ({s.get('disrupted_pct')}%) likely impassable, out of "
            f"{s.get('network_km')} km. Based on {src}."
        )
    if tool == "climate_projection":
        return (
            f"{result.get('variable_label')} for {place} under {result.get('scenario').upper()} "
            f"by the {result.get('horizon')}: baseline {result.get('baseline')} {result.get('unit')} "
            f"-> projected {result.get('projected')} {result.get('unit')} "
            f"(change {result.get('delta')} {result.get('unit')}, {result.get('pct_change')}%). Based on {src}."
        )
    if tool == "drought_spi":
        return (
            f"{result.get('scale_months')}-month SPI for {place}: mean {s.get('mean_spi')} "
            f"({s.get('class')}); about {s.get('drought_area_pct')}% of the area in drought. Based on {src}."
        )
    if tool == "drought_vegetation":
        return (
            f"Vegetation condition for {place}: mean VCI {s.get('mean_vci')}, with "
            f"{s.get('stressed_area_pct')}% under stress. Based on {src}."
        )
    if tool == "infra_exposure":
        return (
            f"Exposure for {place}: ~{s.get('population_exposed'):,} of {s.get('population_total'):,} "
            f"people and {s.get('builtup_exposed_km2')} km² built-up area in the hazard footprint. Based on {src}."
        )
    if tool == "optimize_shelters":
        r = result.get("or_result", {})
        return (
            f"Relief-shelter siting for {place}: placing {len(r.get('chosen', []))} centres covers "
            f"{s.get('coverage_pct')}% of exposed demand within {s.get('radius_km')} km "
            f"(Maximal Covering Location, greedy >= 63% of optimal). Based on {src}."
        )
    if tool == "optimize_evacuation":
        if not s.get("reachable"):
            return f"Evacuation routing for {place}: no route to a safe exit was found. Based on {src}."
        warn = " — but the safest available route still crosses flooded road" if s.get("crosses_flood") else ", clear of flooding"
        return (
            f"Evacuation routing for {place}: a {s.get('route_km')} km path over "
            f"{s.get('segments')} segments reaches a safe exit via Dijkstra{warn}. Based on {src}."
        )
    if tool == "weather_forecast":
        return (
            f"{result.get('days', 7)}-day forecast for {place}: {s.get('total_precip_mm')} mm "
            f"total rain over {s.get('heavy_rain_days')} heavy-rain day(s); peak "
            f"{s.get('peak_precip_mm')} mm on {s.get('peak_date')} — flood watch: "
            f"{s.get('flood_watch')}. Source: Open-Meteo."
        )
    if tool == "flood_multiyear":
        return (
            f"Multi-year flood extent for {place}: the trend is {s.get('trend')} "
            f"({s.get('trend_km2_per_year')} km²/yr), peaking at {s.get('peak_km2')} km² "
            f"in {s.get('peak_year')} (SAR change detection, 2019-2024). Based on {src}."
        )
    if tool == "flood_ml":
        return (
            f"ML flood-risk model for {place} ({result.get('model')}): cross-validated "
            f"accuracy {s.get('cv_accuracy')}, AUC {s.get('cv_auc')} on {s.get('n_samples')} "
            f"samples; the most important factor is {result.get('top_factor')} (SHAP). Based on {src}."
        )
    if tool == "climate_extremes":
        idx = {i["key"]: i for i in result.get("indices", [])}
        hot = idx.get("hot_days", {})
        rx = idx.get("rx1day", {})
        return (
            f"Climate extremes for {place} under {result.get('scenario','').upper()} by the "
            f"{result.get('horizon')}: hot days (Tmax>35°C) {hot.get('baseline')}->{hot.get('projected')} "
            f"days/yr, max 1-day rain {rx.get('baseline')}->{rx.get('projected')} mm "
            f"(ETCCDI indices). Based on {src}."
        )
    if tool == "infra_criticality":
        return (
            f"Road-network criticality for {place}: {s.get('critical_segments')} of "
            f"{s.get('segments')} segments are critical links (highest edge-betweenness) — "
            f"prioritise these for flood protection. Based on {src}."
        )
    if tool == "optimize_mitigation":
        r = result.get("or_result", {})
        return (
            f"Mitigation plan within a budget of {s.get('budget')}: select "
            f"{', '.join(r.get('selected', [])) or 'no'} interventions for a total risk "
            f"reduction of {s.get('total_risk_reduction')} at {s.get('budget_used_pct')}% budget use "
            f"(0/1 knapsack optimum). Based on {src}."
        )
    return f"Analysis complete for {place}. Based on {src}."


async def ask(question: str, aoi: dict | None = None) -> dict[str, Any]:
    from ..core.sanitize import clean_question

    gee.init()
    question = clean_question(question)  # guardrail: normalize + strip injection
    entities = _parse_entities(question)
    tool_name = _choose_tool(question)
    tool = TOOLS[tool_name]

    # AOI precedence: explicit arg > parsed place > default region.
    used_aoi = aoi or entities.get("aoi") or DEFAULT_AOI
    aoi_note = None
    if not aoi and "aoi" not in entities:
        aoi_note = "No AOI given and no known place detected — used a default region over central India."

    result = tool["fn"](used_aoi, entities)
    answer = _template_answer(tool_name, entities, result)

    # Upgrade the prose with Llama, strictly grounded in the computed numbers.
    llm_used = False
    if llm.is_enabled():
        system = (
            "You are GeoCopilot, an assistant for climate-risk analysis. "
            "Answer in 2-4 sentences. You MUST only use the numbers given to you; "
            "never invent figures. Be precise and decision-useful."
        )
        user = (
            f"User question: {question}\n\n"
            f"Tool run: {tool_name}\nComputed result stats: {result.get('stats')}\n"
            f"Extra: scenario={result.get('scenario')} variable={result.get('variable_label')} "
            f"horizon={result.get('horizon')} delta={result.get('delta')} unit={result.get('unit')}\n"
            f"Draft answer to refine: {answer}"
        )
        refined = await llm.complete(system, user)
        if refined:
            answer, llm_used = refined, True

    plan = [
        {"step": "parse_intent", "tool": tool_name, "entities": entities},
        {"step": "resolve_aoi", "aoi": used_aoi},
        {"step": "execute", "module": tool["module"]},
        {"step": "summarize", "llm": llm_used},
    ]
    return {
        "question": question,
        "answer": answer,
        "tool": tool_name,
        "module": tool["module"],
        "plan": plan,
        "layers": [result],
        "citations": CITATIONS.get(tool["module"], []),
        "source": result["source"],
        "llm_used": llm_used,
        "note": aoi_note,
    }
