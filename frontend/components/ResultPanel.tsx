"use client";

import { ShieldCheck, BarChart3, Info } from "lucide-react";
import type { LayerResponse, ModuleId } from "@/lib/types";
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

function ReliabilityCard({ layer }: { layer: LayerResponse }) {
  const r = layer.reliability;
  if (!r) return null;
  return (
    <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/[0.06] p-3.5">
      <div className="mb-2 flex items-center gap-2">
        <ShieldCheck size={15} className="text-emerald-300" />
        <span className="text-xs font-semibold text-emerald-200">
          Reliability
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-slate-500">Applicable area</div>
          <div className="mt-0.5 font-semibold text-white">
            {r.applicable_pct}%
          </div>
        </div>
        <div>
          <div className="text-slate-500">Mean confidence</div>
          <div className="mt-0.5 font-semibold text-white">
            {r.mean_confidence}
          </div>
        </div>
      </div>
      <p className="mt-2.5 text-[11px] leading-relaxed text-slate-500">
        {r.method}. Validated via {r.validation}.
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
}: {
  moduleId: ModuleId;
  layer: LayerResponse;
}) {
  const isRamp = layer.legend.some(
    (l) => !l.label || l.label.trim() === "",
  );
  const ct = chartTitle(moduleId, layer);
  const hasChart = !!ct;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-white">Results</span>
        <SourceBadge source={layer.source} />
      </div>

      {/* climate headline */}
      {moduleId === "climate" && typeof layer.delta === "number" && (
        <div className="rounded-xl border border-line bg-space-850 p-4">
          <div className="text-xs text-slate-500">
            {layer.variable_label} · {layer.scenario?.toUpperCase()} ·{" "}
            {layer.horizon}
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="gradient-text text-3xl font-bold">
              {layer.delta > 0 ? "+" : ""}
              {layer.delta}
            </span>
            <span className="text-sm text-slate-400">{layer.unit}</span>
            <span
              className={`ml-auto text-sm font-semibold ${
                (layer.pct_change ?? 0) >= 0 ? "text-rose-300" : "text-cyan-300"
              }`}
            >
              {(layer.pct_change ?? 0) >= 0 ? "+" : ""}
              {layer.pct_change}%
            </span>
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {layer.baseline} → {layer.projected} {layer.unit} vs baseline
          </div>
        </div>
      )}

      <StatGrid stats={layer.stats} />

      {moduleId === "flood" && <ReliabilityCard layer={layer} />}

      {hasChart && (
        <div className="rounded-xl border border-line bg-space-850 p-3.5">
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
              <div className="flex justify-between text-[10px] text-slate-500">
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

      <p className="flex items-start gap-1.5 text-[11px] leading-relaxed text-slate-600">
        <Info size={12} className="mt-0.5 shrink-0" />
        {layer.source === "demo"
          ? "Deterministic demo surface (no Earth Engine credentials configured). The same AOI always returns the same result."
          : "Computed live from Google Earth Engine over your area of interest."}
      </p>
    </div>
  );
}
