"use client";

import { Play, RotateCcw, Loader2 } from "lucide-react";
import { Slider } from "@/components/Slider";
import { Toggle, SectionLabel } from "@/components/ui";
import {
  FLOOD_FACTORS,
  FLOOD_FACTOR_LABELS,
  ML_MODELS,
  type ClimateHorizon,
  type ClimateScenario,
  type ClimateVariable,
  type FloodFactor,
  type FloodWeights,
  type Hazard,
  type MlModel,
  type RainfallScenario,
  type SpiScale,
} from "@/lib/types";

// Equal-weight fallback used until the AHP defaults are fetched from the API.
export const DEFAULT_WEIGHTS: FloodWeights = FLOOD_FACTORS.reduce(
  (acc, k) => ({ ...acc, [k]: 1 / FLOOD_FACTORS.length }),
  {} as FloodWeights,
);

export type FloodProduct =
  | "susceptibility"
  | "sar"
  | "road"
  | "multiyear"
  | "ml_risk";

export interface FloodControlState {
  weights: FloodWeights;
  rainfall_scenario: RainfallScenario;
  product: FloodProduct;
  // ML-risk classifier model selection.
  ml_model: MlModel;
  // True once the user edits a slider; gates auto-seeding from AHP defaults.
  weightsTouched?: boolean;
}

// ClimateLens products: the existing delta projection + the ETCCDI extremes.
export type ClimateProduct = "projection" | "extremes";

export interface ClimateControlState {
  scenario: ClimateScenario;
  variable: ClimateVariable;
  horizon: ClimateHorizon;
  product: ClimateProduct;
}

export interface DroughtControlState {
  product: "spi" | "spei" | "vegetation";
  scale_months: SpiScale;
}

// InfraRisk products: hazard exposure + road-network criticality.
export type InfraProduct = "exposure" | "criticality";

export interface InfraControlState {
  hazard: Hazard;
  product: InfraProduct;
}

// WeatherCast: live short-range forecast (Open-Meteo). Panel-only (no map tile).
export type WeatherDays = 3 | 7 | 10 | 14;

export interface WeatherControlState {
  days: WeatherDays;
}

export const DEFAULT_WEATHER: WeatherControlState = {
  days: 7,
};

// GroundwaterAI: NASA GRACE terrestrial water storage. Single run, no params.
export interface GroundwaterControlState {
  product: "storage";
}

export const DEFAULT_GROUNDWATER: GroundwaterControlState = {
  product: "storage",
};

// LandslideAI: ML susceptibility — choose the classifier.
export interface LandslideControlState {
  model: MlModel;
}

export const DEFAULT_LANDSLIDE: LandslideControlState = {
  model: "random_forest",
};

export type ResilienceTool =
  | "shelters"
  | "evacuation"
  | "mitigation"
  | "ahp";

export interface ResilienceControlState {
  tool: ResilienceTool;
  num_shelters: number; // 1..20
  radius_km: number; // covering radius
  budget: number; // mitigation budget
}

export const DEFAULT_RESILIENCE: ResilienceControlState = {
  tool: "shelters",
  num_shelters: 5,
  radius_km: 5,
  budget: 200,
};

function RunButton({
  loading,
  onClick,
  label = "Analyze",
}: {
  loading: boolean;
  onClick: () => void;
  label?: string;
}) {
  return (
    // Pinned to the bottom of the scrolling panel so it's reachable without
    // scrolling past long control lists (e.g. FloodAI's 11 factor sliders).
    <div className="sticky bottom-0 z-10 -mx-4 border-t border-line bg-white/95 px-4 pb-1 pt-3 backdrop-blur">
      <button
        onClick={onClick}
        disabled={loading}
        aria-busy={loading}
        className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-70"
      >
        {loading ? (
          <Loader2 size={15} className="animate-spin" />
        ) : (
          <Play size={15} />
        )}
        {loading ? "Running…" : label}
      </button>
    </div>
  );
}

// Small reusable progress hint for slow Earth Engine modules.
function EeProgressHint() {
  return (
    <p className="-mt-2 flex items-center justify-center gap-1.5 text-center text-[11px] text-ink-subtle">
      <Loader2 size={11} className="animate-spin" />
      Computing on Earth Engine — large areas can take 20–40s.
    </p>
  );
}

// ---------------- Flood ----------------
export function FloodControls({
  state,
  setState,
  loading,
  onRun,
  ahpDefaults,
}: {
  state: FloodControlState;
  setState: (s: FloodControlState) => void;
  loading: boolean;
  onRun: () => void;
  // AHP default weights from GET /optimize/ahp/default (used by Reset).
  ahpDefaults?: FloodWeights | null;
}) {
  const setWeight = (k: FloodFactor, v: number) =>
    setState({
      ...state,
      weights: { ...state.weights, [k]: v },
      weightsTouched: true,
    });

  const resetWeights = () =>
    setState({
      ...state,
      weights: { ...(ahpDefaults ?? DEFAULT_WEIGHTS) },
      weightsTouched: true,
    });

  // Per-product run-button label.
  const runLabel =
    state.product === "ml_risk"
      ? "Train"
      : state.product === "multiyear"
        ? "Analyze trend"
        : "Analyze";

  // Slow live products that compute on Earth Engine.
  const isSlowProduct =
    state.product === "susceptibility" ||
    state.product === "sar" ||
    state.product === "multiyear" ||
    state.product === "ml_risk";

  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Product</SectionLabel>
        {/* 5 products — wrap into a 2-row pill grid so labels stay readable
            on the narrow panel (no horizontal overflow). */}
        <div className="grid grid-cols-3 gap-1 rounded-xl border border-line bg-surface-muted p-1">
          {(
            [
              { value: "susceptibility", label: "Suscept." },
              { value: "sar", label: "SAR extent" },
              { value: "road", label: "Road risk" },
              { value: "multiyear", label: "Multi-year" },
              { value: "ml_risk", label: "ML risk" },
            ] as { value: FloodProduct; label: string }[]
          ).map((opt) => (
            <button
              key={opt.value}
              onClick={() => setState({ ...state, product: opt.value })}
              className={`rounded-lg px-2 py-2 text-xs font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan/40 ${
                state.product === opt.value
                  ? "bg-white text-ink shadow-card"
                  : "text-ink-subtle hover:text-ink"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {state.product === "susceptibility" && (
        <>
          <div>
            <div className="mb-2 flex items-center justify-between gap-2">
              <SectionLabel>Factor weights · AHP-weighted, 11 factors</SectionLabel>
              <button
                onClick={resetWeights}
                disabled={!ahpDefaults}
                title={
                  ahpDefaults
                    ? "Reset all sliders to the recommended weights"
                    : "Loading recommended weights…"
                }
                className="inline-flex shrink-0 items-center gap-1 text-[11px] text-ink-subtle transition hover:text-brand-cyan disabled:opacity-40 disabled:hover:text-ink-subtle"
              >
                <RotateCcw size={11} /> Reset weights
              </button>
            </div>
            <div className="space-y-3">
              {FLOOD_FACTORS.map((k) => (
                <Slider
                  key={k}
                  label={FLOOD_FACTOR_LABELS[k]}
                  value={state.weights[k] ?? 0}
                  onChange={(v) => setWeight(k, v)}
                  exact
                />
              ))}
            </div>
          </div>
          <div>
            <SectionLabel>Rainfall scenario</SectionLabel>
            <Toggle
              value={state.rainfall_scenario}
              onChange={(v) => setState({ ...state, rainfall_scenario: v })}
              options={[
                { value: "normal", label: "Normal" },
                { value: "wet", label: "Wet" },
                { value: "extreme", label: "Extreme" },
              ]}
            />
          </div>
        </>
      )}

      {state.product === "sar" && (
        <p className="note-box text-xs leading-relaxed">
          Maps flood water from Sentinel-1 radar — works through cloud, day or
          night.
        </p>
      )}

      {state.product === "road" && (
        <p className="note-box text-xs leading-relaxed">
          Shows which roads flooding is likely to cut off. Red = disrupted, blue
          = passable.
        </p>
      )}

      {state.product === "multiyear" && (
        <p className="note-box text-xs leading-relaxed">
          Tracks how flooded area has changed year over year.
        </p>
      )}

      {state.product === "ml_risk" && (
        <div>
          <SectionLabel>Classifier model</SectionLabel>
          <select
            value={state.ml_model}
            onChange={(e) =>
              setState({ ...state, ml_model: e.target.value as MlModel })
            }
            className="w-full appearance-none rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink shadow-xs transition-colors focus:border-brand-cyan/60 focus:outline-none focus:ring-2 focus:ring-brand-cyan/30"
          >
            {ML_MODELS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
          <p className="note-box mt-3 text-[11px] leading-relaxed">
            Trains a flood-risk model on historical flooding and ranks what
            drives the risk.
          </p>
        </div>
      )}

      <RunButton loading={loading} onClick={onRun} label={runLabel} />
      {loading && isSlowProduct && <EeProgressHint />}
    </div>
  );
}

// ---------------- Climate ----------------
export function ClimateControls({
  state,
  setState,
  loading,
  onRun,
}: {
  state: ClimateControlState;
  setState: (s: ClimateControlState) => void;
  loading: boolean;
  onRun: () => void;
}) {
  const isExtremes = state.product === "extremes";
  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Product</SectionLabel>
        <Toggle
          value={state.product}
          onChange={(v) => setState({ ...state, product: v })}
          options={[
            { value: "projection", label: "Projection" },
            { value: "extremes", label: "Extremes" },
          ]}
        />
      </div>
      <div>
        <SectionLabel>Emission scenario</SectionLabel>
        <Toggle
          value={state.scenario}
          onChange={(v) => setState({ ...state, scenario: v })}
          options={[
            { value: "ssp245", label: "SSP2-4.5" },
            { value: "ssp585", label: "SSP5-8.5" },
          ]}
        />
      </div>
      {/* Variable applies only to the delta projection product. */}
      {!isExtremes && (
        <div>
          <SectionLabel>Variable</SectionLabel>
          <Toggle
            value={state.variable}
            onChange={(v) => setState({ ...state, variable: v })}
            options={[
              { value: "pr", label: "Rainfall" },
              { value: "tas", label: "Mean temp" },
              { value: "tasmax", label: "Max temp" },
            ]}
          />
        </div>
      )}
      <div>
        <SectionLabel>Horizon</SectionLabel>
        <Toggle
          value={state.horizon}
          onChange={(v) => setState({ ...state, horizon: v })}
          options={[
            { value: "2030s", label: "2030s" },
            { value: "2050s", label: "2050s" },
            { value: "2080s", label: "2080s" },
          ]}
        />
      </div>
      <p className="note-box text-[11px] leading-relaxed">
        {isExtremes
          ? "Climate extreme indices from the downscaled CMIP6 ensemble, vs the 1995–2014 baseline."
          : "Downscaled CMIP6 ensemble, vs the 1995–2014 baseline."}
      </p>
      <RunButton
        loading={loading}
        onClick={onRun}
        label={isExtremes ? "Analyze extremes" : "Forecast"}
      />
      {loading && <EeProgressHint />}
    </div>
  );
}

// ---------------- Drought ----------------
export function DroughtControls({
  state,
  setState,
  loading,
  onRun,
}: {
  state: DroughtControlState;
  setState: (s: DroughtControlState) => void;
  loading: boolean;
  onRun: () => void;
}) {
  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Product</SectionLabel>
        <Toggle
          value={state.product}
          onChange={(v) => setState({ ...state, product: v })}
          options={[
            { value: "spi", label: "SPI" },
            { value: "spei", label: "SPEI" },
            { value: "vegetation", label: "Vegetation" },
          ]}
        />
      </div>
      {(state.product === "spi" || state.product === "spei") && (
        <div>
          <SectionLabel>Accumulation scale</SectionLabel>
          <Toggle
            value={state.scale_months}
            onChange={(v) => setState({ ...state, scale_months: v })}
            options={[
              { value: 1, label: "1 mo" },
              { value: 3, label: "3 mo" },
              { value: 6, label: "6 mo" },
              { value: 12, label: "12 mo" },
            ]}
          />
        </div>
      )}
      <p className="note-box text-[11px] leading-relaxed">
        {state.product === "spi"
          ? "Standardized Precipitation Index (SPI). Negative = drier than normal."
          : state.product === "spei"
            ? "SPEI — like SPI but on the water balance (precipitation − evapotranspiration), so it also captures heat-driven drought."
            : "Vegetation health from satellite greenness + land-surface temperature. Low = crop or vegetation stress."}
      </p>
      <RunButton loading={loading} onClick={onRun} label="Analyze" />
      {loading && <EeProgressHint />}
    </div>
  );
}

// ---------------- Infra ----------------
export function InfraControls({
  state,
  setState,
  loading,
  onRun,
}: {
  state: InfraControlState;
  setState: (s: InfraControlState) => void;
  loading: boolean;
  onRun: () => void;
}) {
  const isCriticality = state.product === "criticality";
  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Product</SectionLabel>
        <Toggle
          value={state.product}
          onChange={(v) => setState({ ...state, product: v })}
          options={[
            { value: "exposure", label: "Exposure" },
            { value: "criticality", label: "Criticality" },
          ]}
        />
      </div>

      {!isCriticality && (
        <div>
          <SectionLabel>Hazard</SectionLabel>
          <Toggle
            value={state.hazard}
            onChange={(v) => setState({ ...state, hazard: v })}
            options={[
              { value: "flood", label: "Flood" },
              { value: "drought", label: "Drought" },
            ]}
          />
        </div>
      )}

      <p className="note-box text-[11px] leading-relaxed">
        {isCriticality
          ? "Network-criticality scoring — finds the roads whose failure would most fragment the network."
          : "Overlays the hazard on population and built-up land to show who and what is exposed."}
      </p>
      <RunButton
        loading={loading}
        onClick={onRun}
        label={isCriticality ? "Rank roads" : "Analyze exposure"}
      />
      {loading && <EeProgressHint />}
    </div>
  );
}

// ---------------- WeatherCast ----------------
export function WeatherControls({
  state,
  setState,
  loading,
  onRun,
}: {
  state: WeatherControlState;
  setState: (s: WeatherControlState) => void;
  loading: boolean;
  onRun: () => void;
}) {
  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Forecast days</SectionLabel>
        <Toggle
          value={state.days}
          onChange={(v) => setState({ ...state, days: v })}
          options={[
            { value: 3, label: "3 days" },
            { value: 7, label: "7 days" },
            { value: 10, label: "10 days" },
            { value: 14, label: "14 days" },
          ]}
        />
      </div>
      <p className="note-box text-[11px] leading-relaxed">
        Live rainfall forecast over your area — daily precipitation, heavy-rain
        days and a flood watch for the days ahead.
      </p>
      <RunButton loading={loading} onClick={onRun} label="Forecast" />
    </div>
  );
}

// ---------------- GroundwaterAI ----------------
export function GroundwaterControls({
  loading,
  onRun,
}: {
  loading: boolean;
  onRun: () => void;
}) {
  return (
    <div className="space-y-5">
      <p className="note-box text-[11px] leading-relaxed">
        Groundwater storage &amp; depletion, from satellite gravimetry.
      </p>
      <RunButton loading={loading} onClick={onRun} label="Analyze" />
      {loading && <EeProgressHint />}
    </div>
  );
}

// ---------------- LandslideAI ----------------
export function LandslideControls({
  state,
  setState,
  loading,
  onRun,
}: {
  state: LandslideControlState;
  setState: (s: LandslideControlState) => void;
  loading: boolean;
  onRun: () => void;
}) {
  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Classifier model</SectionLabel>
        <select
          value={state.model}
          onChange={(e) => setState({ ...state, model: e.target.value as MlModel })}
          className="w-full appearance-none rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink shadow-xs transition-colors focus:border-brand-cyan/60 focus:outline-none focus:ring-2 focus:ring-brand-cyan/30"
        >
          {ML_MODELS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.label}
            </option>
          ))}
        </select>
        <p className="note-box mt-3 text-[11px] leading-relaxed">
          Trains on a national landslide inventory vs slope, rainfall &amp;
          terrain — reports F1 / ROC-AUC and what drives the risk.
        </p>
      </div>
      <RunButton loading={loading} onClick={onRun} label="Run model" />
      {loading && <EeProgressHint />}
    </div>
  );
}

// ---------------- ResilienceOR ----------------
export function ResilienceControls({
  state,
  setState,
  loading,
  onRun,
}: {
  state: ResilienceControlState;
  setState: (s: ResilienceControlState) => void;
  loading: boolean;
  onRun: () => void;
}) {
  const runLabels: Record<ResilienceTool, string> = {
    shelters: "Optimize",
    evacuation: "Find route",
    mitigation: "Optimize",
    ahp: "Loaded",
  };

  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Optimization model</SectionLabel>
        <Toggle
          value={state.tool}
          onChange={(v) => setState({ ...state, tool: v })}
          options={[
            { value: "shelters", label: "Shelters" },
            { value: "evacuation", label: "Evac route" },
            { value: "mitigation", label: "Mitigation" },
            { value: "ahp", label: "AHP" },
          ]}
        />
      </div>

      {state.tool === "shelters" && (
        <>
          <div className="space-y-3">
            <Slider
              label="Number of shelters"
              value={state.num_shelters}
              onChange={(v) =>
                setState({ ...state, num_shelters: Math.round(v) })
              }
              min={1}
              max={20}
              step={1}
            />
            <Slider
              label="Coverage radius (km)"
              value={state.radius_km}
              onChange={(v) => setState({ ...state, radius_km: v })}
              min={1}
              max={20}
              step={0.5}
            />
          </div>
          <p className="note-box text-[11px] leading-relaxed">
            Places shelters to cover the most people within the radius.
          </p>
          <RunButton
            loading={loading}
            onClick={onRun}
            label={runLabels.shelters}
          />
        </>
      )}

      {state.tool === "evacuation" && (
        <>
          <p className="note-box text-[11px] leading-relaxed">
            Finds the fastest route from an at-risk area to safe ground, flagging
            any flood-prone stretches.
          </p>
          <RunButton
            loading={loading}
            onClick={onRun}
            label={runLabels.evacuation}
          />
        </>
      )}

      {state.tool === "mitigation" && (
        <>
          <div>
            <SectionLabel>Budget (₹ crore)</SectionLabel>
            <input
              type="number"
              min={0}
              step={10}
              value={state.budget}
              onChange={(e) =>
                setState({
                  ...state,
                  budget: Math.max(0, parseFloat(e.target.value) || 0),
                })
              }
              className="w-full rounded-xl border border-line bg-white px-3 py-2.5 text-sm text-ink tabular-nums shadow-xs transition-colors focus:border-brand-cyan/60 focus:outline-none focus:ring-2 focus:ring-brand-cyan/30"
            />
          </div>
          <p className="note-box text-[11px] leading-relaxed">
            Picks the mix of interventions that cuts the most risk for your
            budget.
          </p>
          <RunButton
            loading={loading}
            onClick={onRun}
            label={runLabels.mitigation}
          />
        </>
      )}

      {state.tool === "ahp" && (
        <p className="note-box text-[11px] leading-relaxed">
          Recommended, consistency-checked weights for the 11 flood factors —
          shown in the results panel.
        </p>
      )}
    </div>
  );
}
