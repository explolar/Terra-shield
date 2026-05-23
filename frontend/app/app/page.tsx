"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { Layers } from "lucide-react";

import { TopBar } from "@/components/TopBar";
import { LeftRail } from "@/components/LeftRail";
import { AoiBar } from "@/components/AoiBar";
import { RightPanel } from "@/components/RightPanel";
import { CopilotPanel } from "@/components/CopilotPanel";
import { ResiliencePanel } from "@/components/ResiliencePanel";
import { SourceBadge } from "@/components/ui";
import { moduleMeta } from "@/components/modules";
import { DEFAULT_WEIGHTS } from "@/components/Controls";
import type {
  ClimateControlState,
  DroughtControlState,
  FloodControlState,
  InfraControlState,
} from "@/components/Controls";

import {
  climateProjection,
  droughtSpi,
  droughtVegetation,
  floodRoadRisk,
  floodSarExtent,
  floodSusceptibility,
  getStatus,
  infraExposure,
} from "@/lib/api";
import type {
  AOI,
  EarthdataStatus,
  LayerResponse,
  ModuleId,
  PointFeatureCollection,
  LineFeatureCollection,
} from "@/lib/types";
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
    <div className="flex h-full w-full items-center justify-center bg-space-950 text-sm text-slate-600">
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

  // --- per-module control state ---
  const [flood, setFlood] = useState<FloodControlState>({
    weights: { ...DEFAULT_WEIGHTS },
    rainfall_scenario: "normal",
    product: "susceptibility",
  });
  const [climate, setClimate] = useState<ClimateControlState>({
    scenario: "ssp585",
    variable: "pr",
    horizon: "2050s",
  });
  const [drought, setDrought] = useState<DroughtControlState>({
    product: "spi",
    scale_months: 3,
  });
  const [infra, setInfra] = useState<InfraControlState>({ hazard: "flood" });

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

  // run analysis for the active module
  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let res: LayerResponse;
      if (moduleId === "flood") {
        if (flood.product === "susceptibility") {
          res = await floodSusceptibility({
            aoi,
            weights: flood.weights,
            rainfall_scenario: flood.rainfall_scenario,
          });
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
        e?.detail || e?.message || "Analysis failed. Check the backend is running.",
      );
      setLayer(null);
    } finally {
      setLoading(false);
    }
  }, [moduleId, aoi, flood, climate, drought, infra]);

  // --- AOI handlers ---
  function clearOrOverlays() {
    setShelters(null);
    setRoute(null);
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

  function switchModule(id: ModuleId) {
    setModuleId(id);
    // clear non-copilot layer when switching to keep the map honest
    if (id !== moduleId) {
      setLayer(null);
      setError(null);
      clearOrOverlays();
    }
  }

  const meta = moduleMeta(moduleId);

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-space-950">
      <TopBar status={status} statusLoading={statusLoading} />

      <div className="flex min-h-0 flex-1">
        <LeftRail active={moduleId} onSelect={switchModule} />

        {/* map */}
        <div className="relative min-w-0 flex-1">
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
            onSelectState={selectStateFromMap}
          />

          {/* floating active-layer badge */}
          {layer && (
            <div className="pointer-events-none absolute bottom-4 left-4 z-[1000] flex items-center gap-2.5 rounded-xl border border-line bg-space-900/85 px-3.5 py-2.5 shadow-panel backdrop-blur-xl">
              <span
                className={`inline-flex h-7 w-7 items-center justify-center rounded-lg bg-space-850 ${meta.accent}`}
              >
                <Layers size={14} />
              </span>
              <div>
                <div className="text-xs font-semibold capitalize text-white">
                  {layer.module} · {layer.product.replace(/_/g, " ")}
                </div>
                <div className="text-[10px] text-slate-500">
                  bbox {bbox.map((b) => b.toFixed(2)).join(", ")}
                </div>
              </div>
              <div className="ml-1">
                <SourceBadge source={layer.source} />
              </div>
            </div>
          )}
        </div>

        {/* right panel */}
        <aside className="z-20 flex w-[360px] shrink-0 flex-col border-l border-line bg-space-900/95 backdrop-blur-xl">
          {moduleId === "copilot" ? (
            <CopilotPanel aoi={aoi} onLayer={(l) => setLayer(l)} />
          ) : moduleId === "resilience" ? (
            <ResiliencePanel
              aoi={aoi}
              onShelters={setShelters}
              onRoute={setRoute}
            />
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
              onRun={runAnalysis}
            />
          )}
        </aside>
      </div>
    </div>
  );
}
