"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { Layers, SlidersHorizontal, X, ChevronUp } from "lucide-react";

import { TopBar } from "@/components/TopBar";
import { LeftRail } from "@/components/LeftRail";
import { AoiBar } from "@/components/AoiBar";
import { RightPanel } from "@/components/RightPanel";
import { CopilotPanel } from "@/components/CopilotPanel";
import { ResiliencePanel } from "@/components/ResiliencePanel";
import { SourceBadge } from "@/components/ui";
import { moduleMeta } from "@/components/modules";
import { DEFAULT_WEIGHTS, DEFAULT_WEATHER } from "@/components/Controls";
import type {
  ClimateControlState,
  DroughtControlState,
  FloodControlState,
  InfraControlState,
  WeatherControlState,
} from "@/components/Controls";

import {
  climateProjection,
  climateExtremes,
  droughtSpi,
  droughtVegetation,
  floodMlRisk,
  floodMultiyear,
  floodRoadRisk,
  floodSarExtent,
  floodSusceptibility,
  getAhpDefault,
  getStatus,
  infraExposure,
  infraCriticality,
  weatherForecast,
  groundwaterStorage,
} from "@/lib/api";
import type {
  AOI,
  EarthdataStatus,
  FloodFactor,
  FloodWeights,
  LayerResponse,
  ModuleId,
  MultiYearResponse,
  MlRiskResponse,
  ClimateExtremesResponse,
  InfraCriticalityResponse,
  WeatherForecastResponse,
  GroundwaterResponse,
  FloodWatch,
  PointFeatureCollection,
  LineFeatureCollection,
} from "@/lib/types";
import { FLOOD_FACTORS } from "@/lib/types";
import {
  DEFAULT_LOCATION,
  bboxToAOI,
  type LocationPreset,
  type StatePreset,
} from "@/lib/presets";

// Leaflet must be client-only.
const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-surface-muted text-sm text-ink-subtle">
      Loading map…
    </div>
  ),
});

export default function Dashboard() {
  // --- engine status ---
  const [status, setStatus] = useState<EarthdataStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  // --- AOI ---
  const [bbox, setBbox] = useState<[number, number, number, number]>(
    DEFAULT_LOCATION.bbox,
  );
  const [activeLocId, setActiveLocId] = useState<string | null>(
    DEFAULT_LOCATION.id,
  );
  const [activeStateName, setActiveStateName] = useState<string | null>(null);
  const [drawMode, setDrawMode] = useState(false);

  const aoi: AOI = useMemo(() => bboxToAOI(bbox), [bbox]);

  // --- ResilienceOR map overlays ---
  const [shelters, setShelters] = useState<PointFeatureCollection | null>(null);
  const [route, setRoute] = useState<LineFeatureCollection | null>(null);

  // --- active module ---
  const [moduleId, setModuleId] = useState<ModuleId>("flood");

  // --- mobile bottom-sheet (controls / results) ---
  const [sheetOpen, setSheetOpen] = useState(false);

  // --- per-module control state ---
  const [flood, setFlood] = useState<FloodControlState>({
    weights: { ...DEFAULT_WEIGHTS },
    rainfall_scenario: "normal",
    product: "susceptibility",
    ml_model: "gbm",
  });
  const [climate, setClimate] = useState<ClimateControlState>({
    scenario: "ssp585",
    variable: "pr",
    horizon: "2050s",
    product: "projection",
  });
  const [drought, setDrought] = useState<DroughtControlState>({
    product: "spi",
    scale_months: 3,
  });
  const [infra, setInfra] = useState<InfraControlState>({
    hazard: "flood",
    product: "exposure",
  });
  const [weather, setWeather] = useState<WeatherControlState>({
    ...DEFAULT_WEATHER,
  });

  // --- AHP default weights (from GET /optimize/ahp/default) ---
  const [ahpDefaults, setAhpDefaults] = useState<FloodWeights | null>(null);

  // --- per-factor map overlays (live mode only) ---
  const [activeFactors, setActiveFactors] = useState<FloodFactor[]>([]);

  // --- SAR severity overlay toggle (live mode only) ---
  const [severityOn, setSeverityOn] = useState(false);

  // --- FloodAI panel-only products (no map tile) ---
  const [multiYear, setMultiYear] = useState<MultiYearResponse | null>(null);
  const [mlRisk, setMlRisk] = useState<MlRiskResponse | null>(null);

  // --- ClimateLens extremes (panel-only) + InfraRisk criticality (map grid) ---
  const [extremes, setExtremes] = useState<ClimateExtremesResponse | null>(
    null,
  );
  const [criticality, setCriticality] =
    useState<InfraCriticalityResponse | null>(null);

  // --- WeatherCast forecast (panel-only) + FloodAI flood-nowcast chip ---
  const [forecast, setForecast] = useState<WeatherForecastResponse | null>(
    null,
  );
  const [floodWatch, setFloodWatch] = useState<FloodWatch | null>(null);

  // --- GroundwaterAI (GRACE storage): map layer (tile/grid) + panel ---
  const [groundwater, setGroundwater] = useState<GroundwaterResponse | null>(
    null,
  );

  // --- layer + request state ---
  const [layer, setLayer] = useState<LayerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // fetch engine status
  useEffect(() => {
    let alive = true;
    getStatus()
      .then((s) => alive && setStatus(s))
      .catch(() => alive && setStatus(null))
      .finally(() => alive && setStatusLoading(false));
    return () => {
      alive = false;
    };
  }, []);

  // fetch AHP default weights once and seed the flood sliders with them.
  useEffect(() => {
    let alive = true;
    getAhpDefault()
      .then((r) => {
        if (!alive) return;
        const w = FLOOD_FACTORS.reduce((acc, k) => {
          acc[k] = typeof r.weights?.[k] === "number" ? r.weights[k] : 0;
          return acc;
        }, {} as FloodWeights);
        setAhpDefaults(w);
        // Only seed the sliders if the user hasn't touched them yet.
        setFlood((prev) =>
          prev.weightsTouched ? prev : { ...prev, weights: { ...w } },
        );
      })
      .catch(() => {
        // Non-fatal: fall back to the equal-weight DEFAULT_WEIGHTS already set.
      });
    return () => {
      alive = false;
    };
  }, []);

  // run analysis for the active module
  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    // Per-factor + severity overlays belong to a specific result; reset on run.
    setActiveFactors([]);
    setSeverityOn(false);

    // FloodAI panel-only products: multi-year trend + ML-risk classifier.
    // These return their own response shapes (no LayerResponse / map tile).
    if (moduleId === "flood" && flood.product === "multiyear") {
      setLayer(null);
      setMlRisk(null);
      setExtremes(null);
      setCriticality(null);
      setGroundwater(null);
      try {
        const res = await floodMultiyear(aoi);
        setMultiYear(res);
      } catch (e: any) {
        setError(e?.detail || e?.message || "Multi-year analysis failed.");
        setMultiYear(null);
      } finally {
        setLoading(false);
      }
      return;
    }
    if (moduleId === "flood" && flood.product === "ml_risk") {
      setLayer(null);
      setMultiYear(null);
      setExtremes(null);
      setCriticality(null);
      setGroundwater(null);
      try {
        const res = await floodMlRisk(aoi, flood.ml_model);
        setMlRisk(res);
      } catch (e: any) {
        setError(e?.detail || e?.message || "Model training failed.");
        setMlRisk(null);
      } finally {
        setLoading(false);
      }
      return;
    }

    // ClimateLens extremes: ETCCDI indices, panel-only (no map tile).
    if (moduleId === "climate" && climate.product === "extremes") {
      setLayer(null);
      setMultiYear(null);
      setMlRisk(null);
      setCriticality(null);
      setGroundwater(null);
      try {
        const res = await climateExtremes(
          aoi,
          climate.scenario,
          climate.horizon,
          "ensemble",
        );
        setExtremes(res);
      } catch (e: any) {
        setError(e?.detail || e?.message || "Extremes analysis failed.");
        setExtremes(null);
      } finally {
        setLoading(false);
      }
      return;
    }

    // WeatherCast: live short-range forecast, panel-only (no map tile).
    if (moduleId === "weather") {
      setLayer(null);
      setMultiYear(null);
      setMlRisk(null);
      setExtremes(null);
      setCriticality(null);
      setGroundwater(null);
      try {
        const res = await weatherForecast(aoi, weather.days);
        setForecast(res);
      } catch (e: any) {
        setError(
          e?.status === 503
            ? "Weather provider unavailable — try again."
            : e?.detail || e?.message || "Forecast failed.",
        );
        setForecast(null);
      } finally {
        setLoading(false);
      }
      return;
    }

    // GroundwaterAI: GRACE storage — renders BOTH a map layer (tile/grid)
    // and a panel. Uses its own response shape (not a LayerResponse).
    if (moduleId === "groundwater") {
      setLayer(null);
      setMultiYear(null);
      setMlRisk(null);
      setExtremes(null);
      setCriticality(null);
      setForecast(null);
      setFloodWatch(null);
      try {
        const res = await groundwaterStorage(aoi);
        setGroundwater(res);
      } catch (e: any) {
        setError(e?.detail || e?.message || "Groundwater analysis failed.");
        setGroundwater(null);
      } finally {
        setLoading(false);
      }
      return;
    }

    // InfraRisk criticality: road-network LineString grid colored by tier.
    if (moduleId === "infra" && infra.product === "criticality") {
      setLayer(null);
      setMultiYear(null);
      setMlRisk(null);
      setExtremes(null);
      setGroundwater(null);
      try {
        const res = await infraCriticality(aoi);
        setCriticality(res);
      } catch (e: any) {
        setError(e?.detail || e?.message || "Criticality analysis failed.");
        setCriticality(null);
      } finally {
        setLoading(false);
      }
      return;
    }

    // Tile / grid based products clear any panel-only results.
    setMultiYear(null);
    setMlRisk(null);
    setExtremes(null);
    setCriticality(null);
    setGroundwater(null);
    setFloodWatch(null);
    try {
      let res: LayerResponse;
      if (moduleId === "flood") {
        if (flood.product === "susceptibility") {
          res = await floodSusceptibility({
            aoi,
            weights: flood.weights,
            rainfall_scenario: flood.rainfall_scenario,
          });
          // Fire-and-forget: fetch a live 7-day flood nowcast for the chip.
          // Failures are swallowed so the susceptibility result is never blocked.
          weatherForecast(aoi, 7)
            .then((wx) => setFloodWatch(wx.summary.flood_watch))
            .catch(() => setFloodWatch(null));
        } else if (flood.product === "sar") {
          res = await floodSarExtent({ aoi });
        } else {
          res = await floodRoadRisk({ aoi });
        }
      } else if (moduleId === "climate") {
        res = await climateProjection({
          aoi,
          scenario: climate.scenario,
          variable: climate.variable,
          horizon: climate.horizon,
          model: "ensemble",
        });
      } else if (moduleId === "drought") {
        res =
          drought.product === "spi"
            ? await droughtSpi({ aoi, scale_months: drought.scale_months })
            : await droughtVegetation({ aoi });
      } else if (moduleId === "infra") {
        res = await infraExposure({ aoi, hazard: infra.hazard });
      } else {
        return;
      }
      setLayer(res);
    } catch (e: any) {
      setError(
        e?.detail ||
          e?.message ||
          "Analysis failed. Check the backend is running.",
      );
      setLayer(null);
    } finally {
      setLoading(false);
    }
  }, [moduleId, aoi, flood, climate, drought, infra, weather]);

  // --- AOI handlers ---
  function clearOrOverlays() {
    setShelters(null);
    setRoute(null);
    setActiveFactors([]);
    setSeverityOn(false);
    setMultiYear(null);
    setMlRisk(null);
    setExtremes(null);
    setCriticality(null);
    setForecast(null);
    setGroundwater(null);
    setFloodWatch(null);
  }

  function selectLocation(loc: LocationPreset) {
    setDrawMode(false);
    setActiveLocId(loc.id);
    setActiveStateName(null);
    setBbox(loc.bbox);
    clearOrOverlays();
  }

  function selectState(s: StatePreset) {
    setDrawMode(false);
    setActiveLocId(null);
    setActiveStateName(s.name);
    setBbox(s.bbox);
    clearOrOverlays();
  }

  function onDrawComplete(b: [number, number, number, number]) {
    setBbox(b);
    setActiveLocId(null);
    setActiveStateName(null);
    setDrawMode(false);
    clearOrOverlays();
  }

  // Click a state polygon on the map to set it as AOI.
  function selectStateFromMap(
    name: string,
    b: [number, number, number, number],
  ) {
    setDrawMode(false);
    setActiveLocId(null);
    setActiveStateName(name);
    setBbox(b);
    clearOrOverlays();
  }

  function toggleFactor(f: FloodFactor) {
    setActiveFactors((prev) =>
      prev.includes(f) ? prev.filter((x) => x !== f) : [...prev, f],
    );
  }

  function toggleSeverity() {
    setSeverityOn((on) => !on);
  }

  function switchModule(id: ModuleId) {
    setModuleId(id);
    // On mobile, surface the panel when a module is selected.
    setSheetOpen(true);
    // clear non-copilot layer when switching to keep the map honest
    if (id !== moduleId) {
      setLayer(null);
      setError(null);
      clearOrOverlays();
    }
  }

  const meta = moduleMeta(moduleId);

  // The panel content is shared between the desktop aside and the mobile sheet.
  const panelContent =
    moduleId === "copilot" ? (
      <CopilotPanel aoi={aoi} onLayer={(l) => setLayer(l)} />
    ) : moduleId === "resilience" ? (
      <ResiliencePanel aoi={aoi} onShelters={setShelters} onRoute={setRoute} />
    ) : (
      <RightPanel
        moduleId={moduleId}
        loading={loading}
        error={error}
        layer={layer}
        flood={flood}
        setFlood={setFlood}
        climate={climate}
        setClimate={setClimate}
        drought={drought}
        setDrought={setDrought}
        infra={infra}
        setInfra={setInfra}
        weather={weather}
        setWeather={setWeather}
        onRun={runAnalysis}
        ahpDefaults={ahpDefaults}
        activeFactors={activeFactors}
        onToggleFactor={toggleFactor}
        multiYear={multiYear}
        mlRisk={mlRisk}
        extremes={extremes}
        criticality={criticality}
        weatherForecast={forecast}
        groundwater={groundwater}
        floodWatch={floodWatch}
        severityOn={severityOn}
        onToggleSeverity={toggleSeverity}
      />
    );

  return (
    <div className="flex h-[100dvh] flex-col overflow-hidden bg-white">
      <TopBar status={status} statusLoading={statusLoading} />

      <div className="relative flex min-h-0 flex-1">
        {/* Module navigation: vertical rail (desktop) + bottom nav (mobile) */}
        <LeftRail active={moduleId} onSelect={switchModule} />

        {/* map */}
        <div className="relative min-w-0 flex-1">
          {/* thin top loading bar while a request is in flight */}
          {loading && <div className="top-loader" />}

          <AoiBar
            activeId={activeLocId}
            drawMode={drawMode}
            bbox={bbox}
            activeStateName={activeStateName}
            onSelectLocation={selectLocation}
            onSelectState={selectState}
            onToggleDraw={() => setDrawMode((d) => !d)}
          />

          <MapView
            bbox={bbox}
            layer={layer}
            drawMode={drawMode}
            onDrawComplete={onDrawComplete}
            shelters={shelters}
            route={route}
            criticality={criticality}
            groundwater={groundwater}
            onSelectState={selectStateFromMap}
            factorUrls={layer?.factor_urls ?? null}
            activeFactors={activeFactors}
            severityUrl={layer?.severity_url ?? null}
            severityOn={severityOn}
            invalidateKey={`${sheetOpen}-${moduleId}`}
          />

          {/* floating active-layer badge */}
          {layer && (
            <div className="pointer-events-none absolute bottom-20 left-3 z-[1000] flex max-w-[calc(100%-1.5rem)] items-center gap-2.5 rounded-xl border border-line bg-white/90 px-3 py-2 shadow-panel backdrop-blur-xl sm:bottom-4 sm:left-4 sm:px-3.5 sm:py-2.5 lg:bottom-4">
              <span
                className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-surface-subtle ${meta.accent}`}
              >
                <Layers size={14} />
              </span>
              <div className="min-w-0">
                <div className="truncate text-xs font-semibold capitalize text-ink">
                  {layer.module} · {layer.product.replace(/_/g, " ")}
                </div>
                <div className="truncate text-[10px] text-ink-subtle">
                  bbox {bbox.map((b) => b.toFixed(2)).join(", ")}
                </div>
              </div>
              <div className="ml-1 shrink-0">
                <SourceBadge source={layer.source} />
              </div>
            </div>
          )}

          {/* floating active-layer badge — GroundwaterAI (no LayerResponse) */}
          {!layer && moduleId === "groundwater" && groundwater && (
            <div className="pointer-events-none absolute bottom-20 left-3 z-[1000] flex max-w-[calc(100%-1.5rem)] items-center gap-2.5 rounded-xl border border-line bg-white/90 px-3 py-2 shadow-panel backdrop-blur-xl sm:bottom-4 sm:left-4 sm:px-3.5 sm:py-2.5 lg:bottom-4">
              <span
                className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-surface-subtle ${meta.accent}`}
              >
                <Layers size={14} />
              </span>
              <div className="min-w-0">
                <div className="truncate text-xs font-semibold capitalize text-ink">
                  groundwater · water storage
                </div>
                <div className="truncate text-[10px] text-ink-subtle">
                  bbox {bbox.map((b) => b.toFixed(2)).join(", ")}
                </div>
              </div>
              <div className="ml-1 shrink-0">
                <SourceBadge source={groundwater.source} />
              </div>
            </div>
          )}

          {/* Mobile: floating button to open the controls / results sheet */}
          <button
            onClick={() => setSheetOpen(true)}
            className="btn-primary fixed bottom-[76px] right-4 z-[1100] !min-h-[48px] rounded-full px-5 shadow-float md:hidden"
            aria-label="Open controls and results"
          >
            <SlidersHorizontal size={16} />
            <span>{meta.short}</span>
            <ChevronUp size={16} />
          </button>
        </div>

        {/* right panel — docked on tablet/desktop (md+); FAB sheet below md */}
        <aside className="z-20 hidden w-[330px] shrink-0 flex-col border-l border-line bg-white md:flex xl:w-[380px]">
          {panelContent}
        </aside>
      </div>

      {/* ---- Mobile bottom sheet ---- */}
      <AnimatePresence>
        {sheetOpen && (
          <>
            <motion.div
              key="sheet-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => setSheetOpen(false)}
              className="fixed inset-0 z-[1200] bg-slate-900/30 backdrop-blur-[2px] md:hidden"
            />
            <motion.div
              key="sheet"
              role="dialog"
              aria-modal="true"
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 320 }}
              className="pb-safe fixed inset-x-0 bottom-0 z-[1300] flex max-h-[85dvh] flex-col overflow-hidden rounded-t-2xl border border-line bg-white shadow-float md:hidden"
            >
              {/* grab handle + close (the panel renders its own titled header below) */}
              <div className="relative flex items-center justify-center py-2">
                <span
                  className="h-1.5 w-10 rounded-full bg-surface-sunken"
                  aria-hidden
                />
                <button
                  onClick={() => setSheetOpen(false)}
                  aria-label="Close panel"
                  className="absolute right-2 top-1 inline-flex h-9 w-9 items-center justify-center rounded-lg text-ink-muted transition hover:bg-surface-subtle hover:text-ink"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="min-h-0 flex-1 overflow-hidden">{panelContent}</div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
