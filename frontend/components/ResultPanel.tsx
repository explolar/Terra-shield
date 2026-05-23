"use client";

import { useState } from "react";
import {
  ShieldCheck,
  BarChart3,
  Info,
  Sigma,
  ChevronDown,
  Layers,
  Droplets,
} from "lucide-react";
import type {
  FloodFactor,
  LayerResponse,
  ModuleId,
} from "@/lib/types";
import { FLOOD_FACTORS, FLOOD_FACTOR_LABELS } from "@/lib/types";
import {
  SourceBadge,
  StatGrid,
  Legend,
  LegendBar,
  SectionLabel,
} from "@/components/ui";
import {
  ClimateTimeseries,
  FloodClassChart,
  SpiGauge,
  PercentMeter,
} from "@/components/Charts";

// Susceptibility class labels (1-5) for the mean_class headline.
const CLASS_LABELS: Record<number, string> = {
  1: "Very low",
  2: "Low",
  3: "Moderate",
  4: "High",
  5: "Very high",
};

function classLabel(c: number): string {
  return CLASS_LABELS[Math.round(c)] ?? "—";
}

// ---- AHP consistency card (task 2) ----
function AhpCard({ layer }: { layer: LayerResponse }) {
  const ahp = layer.ahp;
  const weights = layer.weights;
  if (!ahp && !weights) return null;

  // Sort the 11 weights descending for the horizontal bars.
  const entries = weights
    ? FLOOD_FACTORS.filter((k) => typeof weights[k] === "number")
        .map((k) => ({ key: k, value: weights[k] }))
        .sort((a, b) => b.value - a.value)
    : [];
  const maxW = entries.length ? Math.max(...entries.map((e) => e.value)) : 1;

  return (
    <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
      <div className="mb-2.5 flex items-center gap-2">
        <Sigma size={15} className="text-brand-cyan" />
        <span className="text-xs font-semibold text-ink">AHP consistency</span>
        {ahp && (
          <span
            className={`ml-auto inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
              ahp.consistent
                ? "bg-emerald-500/10 text-emerald-700"
                : "bg-rose-500/10 text-rose-700"
            }`}
          >
            CR = {ahp.consistency_ratio.toFixed(3)}{" "}
            {ahp.consistent ? "✓ consistent" : "✗"}
          </span>
        )}
      </div>

      {entries.length > 0 && (
        <div className="space-y-1.5">
          {entries.map((e) => (
            <div key={e.key} className="flex items-center gap-2">
              <span className="w-[88px] shrink-0 truncate text-[10px] text-ink-muted">
                {FLOOD_FACTOR_LABELS[e.key]}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-muted ring-1 ring-slate-900/5">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400"
                  style={{ width: `${(e.value / maxW) * 100}%` }}
                />
              </div>
              <span className="w-[34px] shrink-0 text-right text-[10px] font-semibold tabular-nums text-ink">
                {e.value.toFixed(3)}
              </span>
            </div>
          ))}
        </div>
      )}

      <p className="mt-2.5 text-[10px] leading-relaxed text-ink-subtle">
        Analytic Hierarchy Process (Saaty, 1980), 11 factors
        {ahp ? ` · λmax = ${ahp.lambda_max.toFixed(3)}` : ""}
      </p>
    </div>
  );
}

// ---- Per-factor layer toggles (task 3, live only) ----
function FactorLayers({
  layer,
  activeFactors,
  onToggleFactor,
}: {
  layer: LayerResponse;
  activeFactors?: FloodFactor[];
  onToggleFactor?: (f: FloodFactor) => void;
}) {
  const [open, setOpen] = useState(true);
  const factorUrls = layer.factor_urls;
  const active = activeFactors ?? [];

  // Demo mode (no per-factor tiles): subtle note only.
  if (!factorUrls || Object.keys(factorUrls).length === 0) {
    return (
      <p className="note-box flex items-start gap-1.5 text-[11px] leading-relaxed">
        <Layers size={12} className="mt-0.5 shrink-0" />
        Per-factor layers available in live (Earth Engine) mode.
      </p>
    );
  }

  const available = FLOOD_FACTORS.filter((k) => !!factorUrls[k]);

  return (
    <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2"
      >
        <Layers size={14} className="text-brand-cyan" />
        <span className="text-xs font-semibold text-ink">
          Per-factor layers
        </span>
        {active.length > 0 && (
          <span className="rounded-full bg-brand-cyan/10 px-1.5 py-0.5 text-[10px] font-bold text-cyan-700">
            {active.length} on
          </span>
        )}
        <ChevronDown
          size={15}
          className={`ml-auto text-ink-subtle transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {available.map((k) => {
            const on = active.includes(k);
            return (
              <button
                key={k}
                onClick={() => onToggleFactor?.(k)}
                aria-pressed={on}
                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium transition ${
                  on
                    ? "border-brand-cyan/50 bg-brand-cyan/10 text-cyan-700 shadow-xs"
                    : "border-line bg-white text-ink-subtle hover:border-brand-cyan/40 hover:text-ink"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    on ? "bg-cyan-500" : "bg-slate-300"
                  }`}
                />
                {FLOOD_FACTOR_LABELS[k]}
              </button>
            );
          })}
        </div>
      )}

      <p className="mt-2.5 text-[10px] leading-relaxed text-ink-subtle">
        Toggle individual factor surfaces over the map. Several can be active at
        once.
      </p>
    </div>
  );
}

// ---- Prominent flood headline stats (task 4) ----
function FloodHeadline({ layer }: { layer: LayerResponse }) {
  const meanClass = layer.stats?.mean_class;
  const highRisk = layer.stats?.high_risk_area_km2;
  if (typeof meanClass !== "number" && typeof highRisk !== "number")
    return null;

  return (
    <div className="grid grid-cols-2 gap-2.5">
      {typeof meanClass === "number" && (
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <Droplets size={12} /> Mean class
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {meanClass.toFixed(2)}
            </span>
            <span className="text-[11px] text-ink-muted">/ 5</span>
          </div>
          <div className="mt-0.5 text-[11px] font-medium text-ink-muted">
            {classLabel(meanClass)}
          </div>
        </div>
      )}
      {typeof highRisk === "number" && (
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <ShieldCheck size={12} /> High-risk area
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {highRisk.toLocaleString()}
            </span>
            <span className="text-[11px] text-ink-muted">km²</span>
          </div>
          {typeof layer.stats?.area_km2 === "number" && (
            <div className="mt-0.5 text-[11px] text-ink-muted">
              of {layer.stats.area_km2.toLocaleString()} km²
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ReliabilityCard({ layer }: { layer: LayerResponse }) {
  const r = layer.reliability;
  if (!r) return null;
  const hasApplicable = typeof r.applicable_pct === "number";
  const hasConfidence = typeof r.mean_confidence === "number";
  return (
    <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-3.5">
      <div className="mb-2 flex items-center gap-2">
        <ShieldCheck size={15} className="text-emerald-600" />
        <span className="text-xs font-semibold text-emerald-700">
          Reliability (AOA)
        </span>
      </div>
      {(hasApplicable || hasConfidence) && (
        <div className="grid grid-cols-2 gap-3 text-xs">
          {hasApplicable && (
            <div>
              <div className="text-ink-subtle">Applicable area</div>
              <div className="mt-0.5 font-semibold text-ink">
                {r.applicable_pct}%
              </div>
            </div>
          )}
          {hasConfidence && (
            <div>
              <div className="text-ink-subtle">Mean confidence</div>
              <div className="mt-0.5 font-semibold text-ink">
                {r.mean_confidence}
              </div>
            </div>
          )}
        </div>
      )}
      <p className="mt-2.5 text-[11px] leading-relaxed text-ink-muted">
        {r.method}
        {r.validation ? `. Validated via ${r.validation}.` : "."}
      </p>
    </div>
  );
}

function ModuleChart({
  moduleId,
  layer,
}: {
  moduleId: ModuleId;
  layer: LayerResponse;
}) {
  if (moduleId === "climate") return <ClimateTimeseries layer={layer} />;
  if (moduleId === "flood" && layer.product === "susceptibility")
    return <FloodClassChart layer={layer} />;
  if (moduleId === "drought" && layer.product === "spi")
    return <SpiGauge layer={layer} />;
  if (moduleId === "drought" && layer.product === "vegetation") {
    const vci = layer.stats?.mean_vci;
    return typeof vci === "number" ? (
      <PercentMeter value={vci} label="Vegetation Condition Index" color="#22c55e" />
    ) : null;
  }
  return null;
}

function chartTitle(moduleId: ModuleId, layer: LayerResponse): string | null {
  if (moduleId === "climate")
    return `${layer.variable_label ?? "Projection"} trajectory (${layer.unit ?? ""})`;
  if (moduleId === "flood" && layer.product === "susceptibility")
    return "Susceptibility class distribution";
  if (moduleId === "drought" && layer.product === "spi") return "Mean SPI";
  if (moduleId === "drought" && layer.product === "vegetation")
    return "Vegetation condition";
  return null;
}

export function ResultPanel({
  moduleId,
  layer,
  activeFactors,
  onToggleFactor,
}: {
  moduleId: ModuleId;
  layer: LayerResponse;
  activeFactors?: FloodFactor[];
  onToggleFactor?: (f: FloodFactor) => void;
}) {
  const isRamp = layer.legend.some(
    (l) => !l.label || l.label.trim() === "",
  );
  const ct = chartTitle(moduleId, layer);
  const hasChart = !!ct;
  const isFloodSusc =
    moduleId === "flood" && layer.product === "susceptibility";

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">Results</span>
        <SourceBadge source={layer.source} />
      </div>

      {/* climate headline */}
      {moduleId === "climate" && typeof layer.delta === "number" && (
        <div className="rounded-xl border border-line bg-surface-subtle p-4">
          <div className="text-xs text-ink-subtle">
            {layer.variable_label} · {layer.scenario?.toUpperCase()} ·{" "}
            {layer.horizon}
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="gradient-text text-3xl font-bold">
              {layer.delta > 0 ? "+" : ""}
              {layer.delta}
            </span>
            <span className="text-sm text-ink-muted">{layer.unit}</span>
            <span
              className={`ml-auto text-sm font-semibold ${
                (layer.pct_change ?? 0) >= 0 ? "text-rose-600" : "text-cyan-600"
              }`}
            >
              {(layer.pct_change ?? 0) >= 0 ? "+" : ""}
              {layer.pct_change}%
            </span>
          </div>
          <div className="mt-1 text-xs text-ink-subtle">
            {layer.baseline} → {layer.projected} {layer.unit} vs baseline
          </div>
        </div>
      )}

      {/* FloodAI: prominent mean-class + high-risk-area headline */}
      {isFloodSusc && <FloodHeadline layer={layer} />}

      <StatGrid stats={layer.stats} />

      {moduleId === "flood" && <ReliabilityCard layer={layer} />}

      {/* FloodAI: AHP consistency + 11-factor weight bars */}
      {isFloodSusc && <AhpCard layer={layer} />}

      {/* FloodAI: per-factor map layer toggles (live) / demo note */}
      {isFloodSusc && (
        <FactorLayers
          layer={layer}
          activeFactors={activeFactors}
          onToggleFactor={onToggleFactor}
        />
      )}

      {hasChart && (
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <SectionLabel>
            <span className="inline-flex items-center gap-1.5">
              <BarChart3 size={12} /> {ct}
            </span>
          </SectionLabel>
          <ModuleChart moduleId={moduleId} layer={layer} />
        </div>
      )}

      {layer.legend.length > 0 && (
        <div>
          <SectionLabel>Legend</SectionLabel>
          {isRamp ? (
            <div className="space-y-2">
              <LegendBar legend={layer.legend} />
              <div className="flex justify-between text-[10px] text-ink-subtle">
                {layer.legend
                  .filter((l) => l.label && l.label.trim())
                  .map((l) => (
                    <span key={l.label}>{l.label}</span>
                  ))}
              </div>
            </div>
          ) : (
            <Legend legend={layer.legend} />
          )}
        </div>
      )}

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
        <Info size={12} className="mt-0.5 shrink-0" />
        {layer.source === "demo"
          ? "Deterministic demo surface (no Earth Engine credentials configured). The same AOI always returns the same result."
          : "Computed live from Google Earth Engine over your area of interest."}
      </p>
    </div>
  );
}
