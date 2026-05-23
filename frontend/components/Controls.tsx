"use client";

import { Play, RotateCcw } from "lucide-react";
import { Slider } from "@/components/Slider";
import { Toggle, SectionLabel } from "@/components/ui";
import type {
  ClimateHorizon,
  ClimateScenario,
  ClimateVariable,
  FloodWeights,
  Hazard,
  RainfallScenario,
  SpiScale,
} from "@/lib/types";

export const DEFAULT_WEIGHTS: FloodWeights = {
  elevation: 0.25,
  slope: 0.2,
  twi: 0.2,
  drainage: 0.15,
  rainfall: 0.1,
  landuse: 0.1,
};

export interface FloodControlState {
  weights: FloodWeights;
  rainfall_scenario: RainfallScenario;
  product: "susceptibility" | "sar" | "road";
}

export interface ClimateControlState {
  scenario: ClimateScenario;
  variable: ClimateVariable;
  horizon: ClimateHorizon;
}

export interface DroughtControlState {
  product: "spi" | "vegetation";
  scale_months: SpiScale;
}

export interface InfraControlState {
  hazard: Hazard;
}

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
  label = "Run analysis",
}: {
  loading: boolean;
  onClick: () => void;
  label?: string;
}) {
  return (
    <button onClick={onClick} disabled={loading} className="btn-primary w-full">
      <Play size={15} className={loading ? "animate-pulse" : ""} />
      {loading ? "Computing…" : label}
    </button>
  );
}

// ---------------- Flood ----------------
export function FloodControls({
  state,
  setState,
  loading,
  onRun,
}: {
  state: FloodControlState;
  setState: (s: FloodControlState) => void;
  loading: boolean;
  onRun: () => void;
}) {
  const setWeight = (k: keyof FloodWeights, v: number) =>
    setState({ ...state, weights: { ...state.weights, [k]: v } });

  return (
    <div className="space-y-5">
      <div>
        <SectionLabel>Product</SectionLabel>
        <Toggle
          value={state.product}
          onChange={(v) => setState({ ...state, product: v })}
          options={[
            { value: "susceptibility", label: "Susceptibility" },
            { value: "sar", label: "SAR extent" },
            { value: "road", label: "Road risk" },
          ]}
        />
      </div>

      {state.product === "susceptibility" && (
        <>
          <div>
            <div className="mb-2 flex items-center justify-between">
              <SectionLabel>Factor weights (AHP)</SectionLabel>
              <button
                onClick={() =>
                  setState({ ...state, weights: { ...DEFAULT_WEIGHTS } })
                }
                className="inline-flex items-center gap-1 text-[11px] text-ink-subtle transition hover:text-brand-cyan"
              >
                <RotateCcw size={11} /> Reset
              </button>
            </div>
            <div className="space-y-3">
              {(
                Object.keys(state.weights) as (keyof FloodWeights)[]
              ).map((k) => (
                <Slider
                  key={k}
                  label={k}
                  value={state.weights[k]}
                  onChange={(v) => setWeight(k, v)}
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
          Sentinel-1 SAR open-water detection compares pre- and post-event
          backscatter to map inundation extent.
        </p>
      )}

      {state.product === "road" && (
        <p className="note-box text-xs leading-relaxed">
          Flags road segments crossing high-susceptibility cells as likely
          impassable. Red = disrupted, blue = passable.
        </p>
      )}

      <RunButton loading={loading} onClick={onRun} />
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
  return (
    <div className="space-y-5">
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
        NASA NEX-GDDP-CMIP6 ensemble, 0.25° downscaled, baseline 1995–2014.
      </p>
      <RunButton loading={loading} onClick={onRun} label="Run projection" />
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
            { value: "vegetation", label: "Vegetation (VCI)" },
          ]}
        />
      </div>
      {state.product === "spi" && (
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
          ? "Standardized Precipitation Index from CHIRPS (McKee et al., 1993). Negative = drier than normal."
          : "NDVI-based Vegetation Condition Index from MODIS. Low values = crop / vegetation stress."}
      </p>
      <RunButton loading={loading} onClick={onRun} />
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
  return (
    <div className="space-y-5">
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
      <p className="note-box text-[11px] leading-relaxed">
        Overlays the hazard footprint on WorldPop population and ESA WorldCover
        built-up land to quantify exposure.
      </p>
      <RunButton loading={loading} onClick={onRun} label="Compute exposure" />
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
    shelters: "Optimize siting",
    evacuation: "Find evacuation route",
    mitigation: "Optimize plan",
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
            Maximal Covering Location Problem — place k shelters to cover the most
            demand within the radius.
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
            Computes the shortest-path evacuation corridor across the road
            network from an at-risk source to safe ground, flagging segments that
            cross flood-prone terrain.
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
            Select the set of interventions that maximizes total risk reduction
            without exceeding the budget.
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
          The Analytic Hierarchy Process derives defensible weights for the six
          flood-susceptibility factors from a pairwise-comparison matrix, with a
          consistency check. The default weights are shown in the results panel.
        </p>
      )}
    </div>
  );
}
