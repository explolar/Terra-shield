"use client";

import { motion } from "framer-motion";
import { moduleMeta } from "@/components/modules";
import {
  ClimateControls,
  DroughtControls,
  FloodControls,
  InfraControls,
  WeatherControls,
  GroundwaterControls,
  type ClimateControlState,
  type DroughtControlState,
  type FloodControlState,
  type InfraControlState,
  type WeatherControlState,
} from "@/components/Controls";
import {
  ResultPanel,
  MultiYearPanel,
  MlRiskPanel,
  ExtremesPanel,
  CriticalityPanel,
  WeatherPanel,
  GroundwaterPanel,
} from "@/components/ResultPanel";
import { ErrorNote, ResultSkeleton, EmptyState } from "@/components/ui";
import { BarChart3 } from "lucide-react";
import type {
  FloodFactor,
  FloodWatch,
  FloodWeights,
  LayerResponse,
  ModuleId,
  MultiYearResponse,
  MlRiskResponse,
  ClimateExtremesResponse,
  InfraCriticalityResponse,
  WeatherForecastResponse,
  GroundwaterResponse,
} from "@/lib/types";

export interface RightPanelProps {
  moduleId: Exclude<ModuleId, "copilot">;
  loading: boolean;
  error: string | null;
  layer: LayerResponse | null;
  // control state
  flood: FloodControlState;
  setFlood: (s: FloodControlState) => void;
  climate: ClimateControlState;
  setClimate: (s: ClimateControlState) => void;
  drought: DroughtControlState;
  setDrought: (s: DroughtControlState) => void;
  infra: InfraControlState;
  setInfra: (s: InfraControlState) => void;
  weather: WeatherControlState;
  setWeather: (s: WeatherControlState) => void;
  onRun: () => void;
  // FloodAI 11-factor AHP extras
  ahpDefaults?: FloodWeights | null;
  activeFactors?: FloodFactor[];
  onToggleFactor?: (f: FloodFactor) => void;
  // FloodAI multi-year + ML-risk products (no map tile; rendered as panels)
  multiYear?: MultiYearResponse | null;
  mlRisk?: MlRiskResponse | null;
  // ClimateLens extremes (no map tile) + InfraRisk criticality (map grid)
  extremes?: ClimateExtremesResponse | null;
  criticality?: InfraCriticalityResponse | null;
  // WeatherCast forecast (no map tile; rendered as a panel)
  weatherForecast?: WeatherForecastResponse | null;
  // GroundwaterAI: GRACE storage (map tile/grid + panel)
  groundwater?: GroundwaterResponse | null;
  // FloodAI susceptibility: live 7-day flood nowcast (fire-and-forget)
  floodWatch?: FloodWatch | null;
  // SAR severity overlay toggle
  severityOn?: boolean;
  onToggleSeverity?: () => void;
}

export function RightPanel(props: RightPanelProps) {
  const {
    moduleId,
    loading,
    error,
    layer,
    flood,
    setFlood,
    climate,
    setClimate,
    drought,
    setDrought,
    infra,
    setInfra,
    weather,
    setWeather,
    onRun,
    ahpDefaults,
    activeFactors,
    onToggleFactor,
    multiYear,
    mlRisk,
    extremes,
    criticality,
    weatherForecast,
    groundwater,
    floodWatch,
    severityOn,
    onToggleSeverity,
  } = props;
  const meta = moduleMeta(moduleId);

  // FloodAI products that render a dedicated panel instead of a LayerResponse.
  const floodProduct = flood.product;
  const isMultiYear = moduleId === "flood" && floodProduct === "multiyear";
  const isMlRisk = moduleId === "flood" && floodProduct === "ml_risk";
  // ClimateLens extremes + InfraRisk criticality render dedicated panels.
  const isExtremes = moduleId === "climate" && climate.product === "extremes";
  const isCriticality =
    moduleId === "infra" && infra.product === "criticality";
  // WeatherCast is panel-only (no map tile), like multi-year / ML-risk.
  const isWeather = moduleId === "weather";
  // GroundwaterAI renders a dedicated panel AND a map layer (tile/grid).
  const isGroundwater = moduleId === "groundwater";

  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* header */}
      <div className="flex items-center gap-3 border-b border-line px-4 py-3.5">
        <span
          className={`inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-surface-subtle ${meta.accent}`}
        >
          <meta.icon size={18} />
        </span>
        <div>
          <div className="text-sm font-semibold text-ink">{meta.name}</div>
          <div className="text-[11px] text-ink-subtle">{meta.tagline}</div>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-4 py-4">
        {/* controls */}
        <div>
          {moduleId === "flood" && (
            <FloodControls
              state={flood}
              setState={setFlood}
              loading={loading}
              onRun={onRun}
              ahpDefaults={ahpDefaults}
            />
          )}
          {moduleId === "climate" && (
            <ClimateControls
              state={climate}
              setState={setClimate}
              loading={loading}
              onRun={onRun}
            />
          )}
          {moduleId === "drought" && (
            <DroughtControls
              state={drought}
              setState={setDrought}
              loading={loading}
              onRun={onRun}
            />
          )}
          {moduleId === "infra" && (
            <InfraControls
              state={infra}
              setState={setInfra}
              loading={loading}
              onRun={onRun}
            />
          )}
          {moduleId === "weather" && (
            <WeatherControls
              state={weather}
              setState={setWeather}
              loading={loading}
              onRun={onRun}
            />
          )}
          {moduleId === "groundwater" && (
            <GroundwaterControls loading={loading} onRun={onRun} />
          )}
        </div>

        {/* results */}
        <div className="border-t border-line pt-5">
          {/* Multi-year + ML-risk render dedicated panels (handle their own
              loading / error / empty states). */}
          {isMultiYear ? (
            multiYear || loading || error ? (
              <motion.div
                key={`multiyear-${multiYear?.source ?? "pending"}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <MultiYearPanel
                  data={multiYear ?? null}
                  loading={loading}
                  error={error}
                />
              </motion.div>
            ) : (
              <EmptyState
                icon={BarChart3}
                title="No results yet"
                message="Run the multi-year trend to see annual flooded-area over time."
              />
            )
          ) : isMlRisk ? (
            mlRisk || loading || error ? (
              <motion.div
                key={`mlrisk-${mlRisk?.model ?? "pending"}-${mlRisk?.source ?? ""}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <MlRiskPanel
                  data={mlRisk ?? null}
                  loading={loading}
                  error={error}
                />
              </motion.div>
            ) : (
              <EmptyState
                icon={BarChart3}
                title="No model yet"
                message="Pick a model and train it to see metrics and feature importance."
              />
            )
          ) : isExtremes ? (
            extremes || loading || error ? (
              <motion.div
                key={`extremes-${extremes?.scenario ?? "pending"}-${extremes?.horizon ?? ""}-${extremes?.source ?? ""}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <ExtremesPanel
                  data={extremes ?? null}
                  loading={loading}
                  error={error}
                />
              </motion.div>
            ) : (
              <EmptyState
                icon={BarChart3}
                title="No extremes yet"
                message="Pick a scenario and horizon, then run to see climate extreme indices."
              />
            )
          ) : isCriticality ? (
            criticality || loading || error ? (
              <motion.div
                key={`criticality-${criticality?.source ?? "pending"}-${criticality?.stats?.segments ?? 0}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <CriticalityPanel
                  data={criticality ?? null}
                  loading={loading}
                  error={error}
                />
              </motion.div>
            ) : (
              <EmptyState
                icon={BarChart3}
                title="No criticality yet"
                message="Run criticality to find the roads most important to keep open."
              />
            )
          ) : isWeather ? (
            weatherForecast || loading || error ? (
              <motion.div
                key={`weather-${weatherForecast?.days ?? "pending"}-${weatherForecast?.source ?? ""}`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <WeatherPanel
                  data={weatherForecast ?? null}
                  loading={loading}
                  error={error}
                />
              </motion.div>
            ) : (
              <EmptyState
                icon={BarChart3}
                title="No forecast yet"
                message="Pick a forecast horizon and get the live short-range rainfall forecast for your AOI."
              />
            )
          ) : isGroundwater ? (
            groundwater || loading || error ? (
              <motion.div
                key={`groundwater-${groundwater?.source ?? "pending"}-${
                  groundwater?.stats?.stress_class ?? ""
                }`}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <GroundwaterPanel
                  data={groundwater ?? null}
                  loading={loading}
                  error={error}
                />
              </motion.div>
            ) : (
              <EmptyState
                icon={BarChart3}
                title="No analysis yet"
                message="Run the analysis to see groundwater storage and depletion trends for your area."
              />
            )
          ) : (
            <>
              {error && <ErrorNote message={error} />}
              {!error && loading && !layer && <ResultSkeleton />}
              {!error && layer && (
                <motion.div
                  key={`${layer.module}-${layer.product}-${layer.source}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <ResultPanel
                    moduleId={moduleId}
                    layer={layer}
                    activeFactors={activeFactors}
                    onToggleFactor={onToggleFactor}
                    severityOn={severityOn}
                    onToggleSeverity={onToggleSeverity}
                    floodWatch={floodWatch}
                  />
                </motion.div>
              )}
              {!error && !loading && !layer && (
                <EmptyState
                  icon={BarChart3}
                  title="No results yet"
                  message="Configure the controls above and run an analysis to see results."
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
