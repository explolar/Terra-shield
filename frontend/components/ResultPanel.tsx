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
  TrendingUp,
  TrendingDown,
  Minus,
  Brain,
  Trophy,
  Users,
  Sprout,
  Building2,
  Eye,
  Thermometer,
  Network,
  CloudRain,
  Wind,
  Waves,
  Gauge,
  Mountain,
} from "lucide-react";
import type {
  FloodFactor,
  FloodWatch,
  LayerResponse,
  ModuleId,
  MultiYearResponse,
  MlRiskResponse,
  TrendDirection,
  ClimateExtremesResponse,
  InfraCriticalityResponse,
  WeatherForecastResponse,
  GroundwaterResponse,
} from "@/lib/types";
import { FLOOD_FACTORS, FLOOD_FACTOR_LABELS } from "@/lib/types";
import {
  SourceBadge,
  StatGrid,
  Legend,
  LegendBar,
  SectionLabel,
  Spinner,
} from "@/components/ui";
import {
  ClimateTimeseries,
  FloodClassChart,
  SpiGauge,
  PercentMeter,
  MultiYearChart,
  MlFeatureImportanceChart,
  ExtremesChart,
  WeatherPrecipChart,
  WeatherTempChart,
  GroundwaterTrendChart,
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
        <span className="text-xs font-semibold text-ink">Factor weights</span>
        {ahp && typeof ahp.consistency_ratio === "number" && (
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
        AHP-weighted, consistency-checked · 11 factors
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
        Per-factor layers show in live mode.
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
          Reliability
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

// ---- SAR severity toggle + extra exposure stat cards (live) ----
const TREND_STYLE: Record<
  TrendDirection,
  { badge: string; Icon: typeof TrendingUp }
> = {
  increasing: { badge: "bg-rose-500/10 text-rose-700", Icon: TrendingUp },
  decreasing: { badge: "bg-emerald-500/10 text-emerald-700", Icon: TrendingDown },
  stable: { badge: "bg-slate-500/10 text-slate-600", Icon: Minus },
};

function fmtUsd(v: number): string {
  if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(2)}M`;
  if (v >= 1_000) return `$${(v / 1_000).toFixed(1)}k`;
  return `$${v.toLocaleString()}`;
}

function ExposureCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Users;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
      <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
        <Icon size={12} /> {label}
      </div>
      <div className="mt-1 text-lg font-semibold tabular-nums text-ink">
        {value}
      </div>
      {sub && <div className="mt-0.5 text-[11px] text-ink-muted">{sub}</div>}
    </div>
  );
}

// Severity overlay toggle + the richer SAR exposure stat cards (live only).
function SarExtras({
  layer,
  severityOn,
  onToggleSeverity,
}: {
  layer: LayerResponse;
  severityOn?: boolean;
  onToggleSeverity?: () => void;
}) {
  const s = layer.stats ?? {};
  const hasSeverity = !!layer.severity_url;
  const pop = s.population_exposed;
  const cropHa = s.cropland_flooded_ha;
  const cropUsd = s.crop_loss_usd;
  const builtHa = s.builtup_flooded_ha;
  const hasExtra =
    typeof pop === "number" ||
    typeof cropHa === "number" ||
    typeof builtHa === "number";

  if (!hasSeverity && !hasExtra) return null;

  return (
    <div className="space-y-4">
      {hasSeverity && (
        <button
          onClick={onToggleSeverity}
          aria-pressed={!!severityOn}
          className={`flex w-full items-center gap-2 rounded-xl border px-3.5 py-3 text-left transition ${
            severityOn
              ? "border-brand-cyan/50 bg-brand-cyan/10"
              : "border-line bg-surface-subtle hover:border-brand-cyan/40"
          }`}
        >
          <Eye
            size={15}
            className={severityOn ? "text-cyan-700" : "text-ink-subtle"}
          />
          <div className="min-w-0 flex-1">
            <div className="text-xs font-semibold text-ink">
              {severityOn ? "Severity overlay on" : "Show severity"}
            </div>
            <div className="text-[10px] text-ink-subtle">
              3-class flood depth · low → high
            </div>
          </div>
          <span className="flex shrink-0 items-center gap-1">
            {["#ffffb2", "#fd8d3c", "#bd0026"].map((c) => (
              <span
                key={c}
                className="h-3 w-3 rounded-sm ring-1 ring-slate-900/10"
                style={{ backgroundColor: c }}
              />
            ))}
          </span>
        </button>
      )}

      {hasExtra && (
        <div className="grid grid-cols-2 gap-2.5">
          {typeof pop === "number" && (
            <ExposureCard
              icon={Users}
              label="Population exposed"
              value={pop.toLocaleString()}
            />
          )}
          {typeof cropHa === "number" && (
            <ExposureCard
              icon={Sprout}
              label="Cropland flooded"
              value={`${cropHa.toLocaleString()} ha`}
              sub={
                typeof cropUsd === "number"
                  ? `${fmtUsd(cropUsd)} crop loss`
                  : undefined
              }
            />
          )}
          {typeof builtHa === "number" && (
            <ExposureCard
              icon={Building2}
              label="Built-up flooded"
              value={`${builtHa.toLocaleString()} ha`}
            />
          )}
        </div>
      )}
    </div>
  );
}

// ---- Multi-year flood-frequency panel (no map tile) ----
export function MultiYearPanel({
  data,
  loading,
  error,
}: {
  data: MultiYearResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (error)
    return (
      <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-sm text-rose-700">
        {error}
      </div>
    );
  if (loading) return <Spinner label="Computing flood trend…" />;
  if (!data) return null;

  const { series, stats } = data;
  const ts = TREND_STYLE[stats.trend] ?? TREND_STYLE.stable;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">
          Multi-year flood trend
        </span>
        <SourceBadge source={data.source} />
      </div>

      {/* trend badge + peak callout */}
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold ${ts.badge}`}
        >
          <ts.Icon size={13} />
          {stats.trend} · {stats.trend_km2_per_year} km²/yr
        </span>
      </div>

      <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
        <SectionLabel>
          <span className="inline-flex items-center gap-1.5">
            <BarChart3 size={12} /> Annual flooded area (km²)
          </span>
        </SectionLabel>
        <MultiYearChart series={series} />
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <Droplets size={12} /> Peak flooding
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {stats.peak_km2.toLocaleString()}
            </span>
            <span className="text-[11px] text-ink-muted">km²</span>
          </div>
          <div className="mt-0.5 text-[11px] text-ink-muted">
            in {stats.peak_year}
          </div>
        </div>
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="text-[11px] text-ink-subtle">AOI area</div>
          <div className="mt-1 text-lg font-semibold tabular-nums text-ink">
            {stats.area_km2.toLocaleString()} km²
          </div>
        </div>
      </div>

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
        <Info size={12} className="mt-0.5 shrink-0" />
        {data.source === "demo"
          ? "Demo data — the same area always returns the same trend."
          : "Computed live from satellite surface-water history."}
      </p>
    </div>
  );
}

// ---- ML flood-risk classifier panel (no map tile) ----
export function MlRiskPanel({
  data,
  loading,
  error,
}: {
  data: MlRiskResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (error)
    return (
      <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-sm text-rose-700">
        {error}
      </div>
    );
  if (loading)
    return (
      <div className="space-y-2">
        <Spinner label="Training model…" />
        <p className="text-center text-[11px] text-ink-subtle">
          Computing on Earth Engine — large areas can take 20–40s.
        </p>
      </div>
    );
  if (!data) return null;

  const m = data.metrics;
  const topLabel =
    FLOOD_FACTOR_LABELS[data.top_factor as FloodFactor] ??
    data.top_factor.replace(/_/g, " ");

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink">
          <Brain size={15} className="text-brand-cyan" /> Flood-risk model
        </span>
        <SourceBadge source={data.source} />
      </div>

      {/* metric stat cards */}
      <div className="grid grid-cols-2 gap-2.5">
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">CV accuracy</div>
          <div className="mt-1 gradient-text text-lg font-semibold tabular-nums">
            {(m.cv_accuracy * 100).toFixed(1)}%
          </div>
          <div className="mt-0.5 text-[10px] text-ink-muted">
            ± {(m.cv_accuracy_std * 100).toFixed(1)}%
          </div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">CV AUC</div>
          <div className="mt-1 gradient-text text-lg font-semibold tabular-nums">
            {m.cv_auc.toFixed(3)}
          </div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">Samples</div>
          <div className="mt-1 text-base font-semibold tabular-nums text-ink">
            {m.n_samples.toLocaleString()}
          </div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">Positive rate</div>
          <div className="mt-1 text-base font-semibold tabular-nums text-ink">
            {(m.positive_rate * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* top factor highlight */}
      <div className="flex items-center gap-2 rounded-xl border border-emerald-300 bg-emerald-50 p-3">
        <Trophy size={15} className="shrink-0 text-emerald-600" />
        <div className="text-xs text-emerald-700">
          Most predictive factor:{" "}
          <span className="font-bold">{topLabel}</span>
        </div>
      </div>

      {/* feature importance bars */}
      <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
        <SectionLabel>
          <span className="inline-flex items-center gap-1.5">
            <BarChart3 size={12} /> What drives the risk
          </span>
        </SectionLabel>
        <MlFeatureImportanceChart
          data={data.feature_importance}
          topFactor={data.top_factor}
        />
        <p className="mt-2.5 text-[10px] leading-relaxed text-ink-subtle">
          Feature importance from the trained model.
        </p>
      </div>

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
        <Info size={12} className="mt-0.5 shrink-0" />
        {data.explainability}
      </p>
    </div>
  );
}

// ---- LandslideAI panel: ML susceptibility metrics + feature importance ----
export function LandslidePanel({
  layer,
  loading,
  error,
}: {
  layer: LayerResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (error)
    return (
      <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-sm text-rose-700">
        {error}
      </div>
    );
  if (loading)
    return (
      <div className="space-y-2">
        <Spinner label="Training susceptibility model…" />
        <p className="text-center text-[11px] text-ink-subtle">
          Sampling inventory + terrain on Earth Engine — can take 20–40s.
        </p>
      </div>
    );
  if (!layer) return null;

  const m = layer.metrics;
  const num = (v?: number | null) => (typeof v === "number" ? v.toFixed(3) : "—");
  const pct = (v?: number | null) =>
    typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—";
  const fi = layer.feature_importance ?? [];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink">
          <Mountain size={15} className="text-orange-600" /> Landslide model
        </span>
        <SourceBadge source={layer.source} />
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">F1 score</div>
          <div className="mt-1 gradient-text text-lg font-semibold tabular-nums">{num(m?.f1)}</div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">ROC-AUC</div>
          <div className="mt-1 gradient-text text-lg font-semibold tabular-nums">{num(m?.roc_auc)}</div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">Precision</div>
          <div className="mt-1 text-base font-semibold tabular-nums text-ink">{num(m?.precision)}</div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">Recall</div>
          <div className="mt-1 text-base font-semibold tabular-nums text-ink">{num(m?.recall)}</div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">Accuracy</div>
          <div className="mt-1 text-base font-semibold tabular-nums text-ink">{pct(m?.accuracy)}</div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-ink-subtle">Samples</div>
          <div className="mt-1 text-base font-semibold tabular-nums text-ink">
            {m?.n_samples ? m.n_samples.toLocaleString() : "—"}
          </div>
        </div>
      </div>

      {fi.length > 0 && (
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <SectionLabel>
            <span className="inline-flex items-center gap-1.5">
              <BarChart3 size={12} /> What drives susceptibility
            </span>
          </SectionLabel>
          <MlFeatureImportanceChart data={fi} topFactor={layer.top_factor} />
        </div>
      )}

      {layer.legend?.length > 0 && (
        <div>
          <SectionLabel>Susceptibility</SectionLabel>
          <Legend legend={layer.legend} />
        </div>
      )}

      {layer.inventory && (
        <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
          <Info size={12} className="mt-0.5 shrink-0" />
          Trained on: {layer.inventory}
        </p>
      )}

      {layer.live_error && (
        <p className="rounded-lg border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-[10px] leading-relaxed text-amber-700">
          Live run fell back to demo: {layer.live_error}
        </p>
      )}
    </div>
  );
}

// ---- ClimateLens extremes panel (ETCCDI indices; no map tile) ----
// Heat / precipitation indices where an increase is adverse → positive delta
// is shown in red; a decrease in cyan. CDD (consecutive dry days) increasing is
// also adverse, so all four ETCCDI indices treat positive delta as "worse".
function ExtremeIndexCard({ idx }: { idx: ClimateExtremesResponse["indices"][number] }) {
  const up = idx.delta >= 0;
  const chip = up
    ? "bg-rose-500/10 text-rose-700"
    : "bg-cyan-500/10 text-cyan-700";
  const sign = idx.delta > 0 ? "+" : "";
  const pctSign = idx.pct_change > 0 ? "+" : "";
  return (
    <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-xs font-semibold text-ink">{idx.label}</div>
          <div className="mt-1 text-[11px] text-ink-muted">
            <span className="font-medium text-ink-subtle">{idx.baseline}</span>
            <span className="mx-1 text-ink-faint">→</span>
            <span className="font-semibold text-ink">{idx.projected}</span>{" "}
            {idx.unit}
          </div>
        </div>
        <span
          className={`shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums ${chip}`}
        >
          {sign}
          {idx.delta} ({pctSign}
          {idx.pct_change}%)
        </span>
      </div>
    </div>
  );
}

export function ExtremesPanel({
  data,
  loading,
  error,
}: {
  data: ClimateExtremesResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (error)
    return (
      <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-sm text-rose-700">
        {error}
      </div>
    );
  if (loading) return <Spinner label="Computing extremes…" />;
  if (!data) return null;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink">
          <Thermometer size={15} className="text-brand-cyan" /> Climate extremes
        </span>
        <SourceBadge source={data.source} />
      </div>

      <div className="flex flex-wrap items-center gap-2 text-[11px] text-ink-subtle">
        <span className="rounded-full bg-surface-muted px-2 py-0.5 font-medium text-ink-muted">
          {data.scenario.toUpperCase()}
        </span>
        <span className="rounded-full bg-surface-muted px-2 py-0.5 font-medium text-ink-muted">
          {data.horizon}
        </span>
        <span className="rounded-full bg-surface-muted px-2 py-0.5 font-medium text-ink-muted">
          {data.model}
        </span>
      </div>

      {/* one card per index */}
      <div className="space-y-2.5">
        {data.indices.map((idx) => (
          <ExtremeIndexCard key={idx.key} idx={idx} />
        ))}
      </div>

      {/* grouped baseline vs projected bar chart */}
      {data.indices.length > 0 && (
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <SectionLabel>
            <span className="inline-flex items-center gap-1.5">
              <BarChart3 size={12} /> Baseline vs projected
            </span>
          </SectionLabel>
          <ExtremesChart indices={data.indices} />
        </div>
      )}

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
        <Info size={12} className="mt-0.5 shrink-0" />
        {data.reference}
      </p>
    </div>
  );
}

// ---- InfraRisk road-criticality panel (LineString grid rendered on the map) ----
const TIER_COLORS: Record<string, string> = {
  critical: "#b91c1c",
  important: "#f59e0b",
  normal: "#64748b",
};

export function CriticalityPanel({
  data,
  loading,
  error,
}: {
  data: InfraCriticalityResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (error)
    return (
      <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-sm text-rose-700">
        {error}
      </div>
    );
  if (loading) return <Spinner label="Ranking roads…" />;
  if (!data) return null;

  const { stats, legend } = data;
  const segs = stats.segments ?? 0;
  const crit = stats.critical_segments ?? 0;
  const critPct = segs > 0 ? Math.round((crit / segs) * 1000) / 10 : 0;
  const legendItems =
    legend && legend.length
      ? legend
      : [
          { label: "Critical", color: TIER_COLORS.critical },
          { label: "Important", color: TIER_COLORS.important },
          { label: "Normal", color: TIER_COLORS.normal },
        ];

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink">
          <Network size={15} className="text-brand-cyan" /> Road criticality
        </span>
        <SourceBadge source={data.source} />
      </div>

      {/* headline stat cards */}
      <div className="grid grid-cols-2 gap-2.5">
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="text-[11px] text-ink-subtle">Critical segments</div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {crit.toLocaleString()}
            </span>
            <span className="text-[11px] text-ink-muted">
              of {segs.toLocaleString()}
            </span>
          </div>
          <div className="mt-0.5 text-[11px] text-ink-muted">
            {critPct}% of network
          </div>
        </div>
        {typeof stats.area_km2 === "number" && (
          <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
            <div className="text-[11px] text-ink-subtle">AOI area</div>
            <div className="mt-1 text-lg font-semibold tabular-nums text-ink">
              {stats.area_km2.toLocaleString()} km²
            </div>
          </div>
        )}
      </div>

      {/* tier legend */}
      <div>
        <SectionLabel>Legend</SectionLabel>
        <Legend legend={legendItems} />
      </div>

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
        <Info size={12} className="mt-0.5 shrink-0" />
        Network-criticality scoring — the roads whose failure would most fragment
        the network.
      </p>
    </div>
  );
}

// ---- WeatherCast: shared flood-watch color coding ----
// "no heavy rain" = emerald, "heavy rain" = amber, "very heavy rain" = red.
const FLOOD_WATCH_STYLE: Record<FloodWatch, string> = {
  "no heavy rain": "border-emerald-500/40 bg-emerald-500/10 text-emerald-700",
  "heavy rain": "border-amber-500/40 bg-amber-500/10 text-amber-700",
  "very heavy rain": "border-rose-500/40 bg-rose-500/10 text-rose-700",
};

const FLOOD_WATCH_DOT: Record<FloodWatch, string> = {
  "no heavy rain": "bg-emerald-500",
  "heavy rain": "bg-amber-500",
  "very heavy rain": "bg-rose-500",
};

export function FloodWatchBadge({
  watch,
  prefix,
  size = "md",
}: {
  watch: FloodWatch;
  prefix?: string;
  size?: "sm" | "md";
}) {
  const style =
    FLOOD_WATCH_STYLE[watch] ?? FLOOD_WATCH_STYLE["no heavy rain"];
  const dot = FLOOD_WATCH_DOT[watch] ?? FLOOD_WATCH_DOT["no heavy rain"];
  const sm = size === "sm";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${style} ${
        sm ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-[11px]"
      }`}
    >
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dot}`} />
      {prefix ? `${prefix} ` : ""}
      {watch}
    </span>
  );
}

// ---- WeatherCast: live short-range forecast panel (no map tile) ----
export function WeatherPanel({
  data,
  loading,
  error,
}: {
  data: WeatherForecastResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (error)
    return (
      <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-sm text-rose-700">
        {error}
      </div>
    );
  if (loading) return <Spinner label="Fetching forecast…" />;
  if (!data) return null;

  const s = data.summary;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink">
          <CloudRain size={15} className="text-brand-cyan" /> {data.days}-day
          forecast
        </span>
        <SourceBadge source={data.source} />
      </div>

      {/* flood-watch badge */}
      <div className="flex flex-wrap items-center gap-2">
        <FloodWatchBadge watch={s.flood_watch} />
        <span className="text-[10px] text-ink-subtle">
          {data.provider} · {data.latitude.toFixed(2)}, {data.longitude.toFixed(2)}
        </span>
      </div>

      {/* summary stat cards */}
      <div className="grid grid-cols-2 gap-2.5">
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <Droplets size={12} /> Total precip
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {s.total_precip_mm.toLocaleString()}
            </span>
            <span className="text-[11px] text-ink-muted">mm</span>
          </div>
        </div>
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <CloudRain size={12} /> Heavy-rain days
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {s.heavy_rain_days}
            </span>
            <span className="text-[11px] text-ink-muted">of {data.days}</span>
          </div>
        </div>
        <div className="col-span-2 rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <Wind size={12} /> Peak precip
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {s.peak_precip_mm.toLocaleString()}
            </span>
            <span className="text-[11px] text-ink-muted">mm</span>
            {s.peak_date && (
              <span className="ml-auto text-[11px] text-ink-muted">
                on {s.peak_date}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* daily precipitation bar chart */}
      <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
        <SectionLabel>
          <span className="inline-flex items-center gap-1.5">
            <BarChart3 size={12} /> Daily precipitation (mm)
          </span>
        </SectionLabel>
        <WeatherPrecipChart daily={data.daily} />
      </div>

      {/* temperature range line chart (optional) */}
      {data.daily.some(
        (d) => d.tmax_c !== null || d.tmin_c !== null,
      ) && (
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <SectionLabel>
            <span className="inline-flex items-center gap-1.5">
              <Thermometer size={12} /> Temperature range (°C)
            </span>
          </SectionLabel>
          <WeatherTempChart daily={data.daily} />
        </div>
      )}

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
        <Info size={12} className="mt-0.5 shrink-0" />
        Live forecast from {data.provider}. The flood watch reflects the wettest
        days ahead.
      </p>
    </div>
  );
}

// ---- GroundwaterAI: GRACE terrestrial water storage panel ----
// Stress badge colors keyed by stress_class (depletion = reds, stable = amber,
// recharging = green). Falls back to a neutral slate for unknown classes.
const GW_STRESS_STYLE: Record<string, { bg: string; text: string }> = {
  "Severe depletion": { bg: "#67000d", text: "#ffffff" },
  "High depletion": { bg: "#cb181d", text: "#ffffff" },
  "Moderate depletion": { bg: "#fb6a4a", text: "#3b0a02" },
  Stable: { bg: "#fee08b", text: "#5b4500" },
  Recharging: { bg: "#1a9850", text: "#ffffff" },
};

function GwStressBadge({ stressClass }: { stressClass: string }) {
  const style = GW_STRESS_STYLE[stressClass] ?? {
    bg: "#64748b",
    text: "#ffffff",
  };
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold ring-1 ring-slate-900/10"
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      <Waves size={12} />
      {stressClass}
    </span>
  );
}

export function GroundwaterPanel({
  data,
  loading,
  error,
}: {
  data: GroundwaterResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (error)
    return (
      <div className="rounded-xl border border-rose-300 bg-rose-50 p-3.5 text-sm text-rose-700">
        {error}
      </div>
    );
  if (loading) return <Spinner label="Analyzing water storage…" />;
  if (!data) return null;

  const { stats, series, legend } = data;
  const trend = stats.depletion_trend_cm_yr;
  const trendUp = trend >= 0;
  const recharge = stats.recharge_proxy_mm_yr;
  const hasSeries = series.length > 0;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ink">
          <Droplets size={15} className="text-indigo-600" /> Water storage
        </span>
        <SourceBadge source={data.source} />
      </div>

      {/* stress badge */}
      <div className="flex flex-wrap items-center gap-2">
        <GwStressBadge stressClass={stats.stress_class} />
      </div>

      {/* stat cards */}
      <div className="grid grid-cols-2 gap-2.5">
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <Droplets size={12} /> Storage anomaly
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="gradient-text text-2xl font-bold tabular-nums">
              {stats.mean_anomaly_cm > 0 ? "+" : ""}
              {stats.mean_anomaly_cm}
            </span>
            <span className="text-[11px] text-ink-muted">cm</span>
          </div>
        </div>
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            {trendUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}{" "}
            Depletion trend
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span
              className="text-2xl font-bold tabular-nums"
              style={{ color: trendUp ? "#1a9850" : "#cb181d" }}
            >
              {trendUp ? "+" : ""}
              {trend}
            </span>
            <span className="text-[11px] text-ink-muted">cm/yr</span>
          </div>
        </div>
        <div className="col-span-2 rounded-xl border border-line bg-surface-subtle p-3.5">
          <div className="flex items-center gap-1.5 text-[11px] text-ink-subtle">
            <Gauge size={12} /> Recharge proxy
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-lg font-semibold tabular-nums text-ink">
              {typeof recharge === "number" ? recharge.toLocaleString() : "—"}
            </span>
            {typeof recharge === "number" && (
              <span className="text-[11px] text-ink-muted">mm/yr</span>
            )}
            {typeof stats.area_km2 === "number" && (
              <span className="ml-auto text-[11px] text-ink-muted">
                {stats.area_km2.toLocaleString()} km²
              </span>
            )}
          </div>
        </div>
      </div>

      {/* trend line chart (demo) or a note (live) */}
      {hasSeries ? (
        <div className="rounded-xl border border-line bg-surface-subtle p-3.5">
          <SectionLabel>
            <span className="inline-flex items-center gap-1.5">
              <BarChart3 size={12} /> Storage anomaly trend (cm)
            </span>
          </SectionLabel>
          <GroundwaterTrendChart series={series} />
        </div>
      ) : (
        <p className="note-box flex items-start gap-1.5 text-[11px] leading-relaxed">
          <Info size={12} className="mt-0.5 shrink-0" />
          Yearly history shows in demo mode.
        </p>
      )}

      {/* categorical stress-class legend (describes the trend) */}
      {legend && legend.length > 0 && (
        <div>
          <SectionLabel>Stress classes</SectionLabel>
          <Legend legend={legend} />
        </div>
      )}

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-subtle">
        <Info size={12} className="mt-0.5 shrink-0" />
        {data.source === "demo"
          ? "Demo data — the same area always returns the same trend."
          : "Computed live from satellite gravimetry."}
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
  severityOn,
  onToggleSeverity,
  floodWatch,
}: {
  moduleId: ModuleId;
  layer: LayerResponse;
  activeFactors?: FloodFactor[];
  onToggleFactor?: (f: FloodFactor) => void;
  // SAR severity overlay toggle
  severityOn?: boolean;
  onToggleSeverity?: () => void;
  // FloodAI susceptibility: optional live 7-day flood nowcast (fire-and-forget).
  floodWatch?: FloodWatch | null;
}) {
  const isRamp = layer.legend.some(
    (l) => !l.label || l.label.trim() === "",
  );
  const ct = chartTitle(moduleId, layer);
  const hasChart = !!ct;
  const isFloodSusc =
    moduleId === "flood" && layer.product === "susceptibility";
  const isSar = moduleId === "flood" && layer.product === "sar_extent";

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

      {/* FloodAI: live 7-day flood nowcast chip (fire-and-forget; hidden on fail) */}
      {isFloodSusc && floodWatch && (
        <div className="flex flex-wrap items-center gap-2">
          <FloodWatchBadge
            watch={floodWatch}
            prefix="Flood nowcast:"
            size="sm"
          />
        </div>
      )}

      {/* FloodAI: prominent mean-class + high-risk-area headline */}
      {isFloodSusc && <FloodHeadline layer={layer} />}

      <StatGrid stats={layer.stats} />

      {/* SAR: severity overlay toggle + richer exposure stat cards (live) */}
      {isSar && (
        <SarExtras
          layer={layer}
          severityOn={severityOn}
          onToggleSeverity={onToggleSeverity}
        />
      )}

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
          ? "Demo data — the same area always returns the same result."
          : "Computed live from satellite data over your area."}
      </p>
    </div>
  );
}
