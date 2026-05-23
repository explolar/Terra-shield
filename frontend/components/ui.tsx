"use client";

import React from "react";
import { Loader2 } from "lucide-react";
import type { LegendItem, Source } from "@/lib/types";

export function SourceBadge({ source }: { source: Source }) {
  const live = source === "live";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${
        live
          ? "border border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
          : "border border-amber-500/40 bg-amber-500/10 text-amber-300"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          live ? "animate-pulse-ring bg-emerald-400" : "bg-amber-400"
        }`}
      />
      {live ? "Live data" : "Demo data"}
    </span>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-8 text-sm text-slate-400">
      <Loader2 size={16} className="animate-spin text-brand-cyan" />
      {label ?? "Computing…"}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-sm text-rose-200">
      {message}
    </div>
  );
}

export function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="mb-2.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
      {children}
    </h4>
  );
}

const STAT_LABELS: Record<string, string> = {
  mean: "Mean index",
  max: "Max index",
  high_risk_pct: "High-risk area",
  high_risk_area_km2: "High-risk area",
  area_km2: "Total area",
  flooded_area_km2: "Flooded area",
  flooded_pct: "Flooded share",
  roads_total: "Road segments",
  roads_disrupted: "Disrupted",
  disrupted_pct: "Disrupted share",
  network_km: "Network length",
  mean_spi: "Mean SPI",
  class: "Drought class",
  drought_area_pct: "Area in drought",
  mean_vci: "Mean VCI",
  stressed_area_pct: "Stressed area",
  population_total: "Total population",
  population_exposed: "Exposed population",
  population_exposed_pct: "Exposed share",
  builtup_km2: "Built-up area",
  builtup_exposed_km2: "Exposed built-up",
};

const PCT_KEYS = new Set([
  "high_risk_pct",
  "flooded_pct",
  "disrupted_pct",
  "drought_area_pct",
  "stressed_area_pct",
  "population_exposed_pct",
]);
const KM2_KEYS = new Set([
  "area_km2",
  "flooded_area_km2",
  "high_risk_area_km2",
  "network_km",
  "builtup_km2",
  "builtup_exposed_km2",
]);

function formatStat(key: string, value: any): string {
  if (typeof value === "number") {
    if (PCT_KEYS.has(key)) return `${value}%`;
    if (key === "network_km") return `${value} km`;
    if (KM2_KEYS.has(key)) return `${value.toLocaleString()} km²`;
    if (key.startsWith("population")) return value.toLocaleString();
    return value.toLocaleString();
  }
  return String(value);
}

const PRIMARY_KEYS = [
  "mean",
  "high_risk_pct",
  "high_risk_area_km2",
  "flooded_pct",
  "disrupted_pct",
  "mean_spi",
  "class",
  "drought_area_pct",
  "mean_vci",
  "stressed_area_pct",
  "population_exposed",
  "population_exposed_pct",
];

export function StatGrid({ stats }: { stats: Record<string, any> }) {
  const entries = Object.entries(stats).filter(
    ([k, v]) => v !== null && v !== undefined && typeof v !== "object",
  );
  // Order: primary metrics first, then the rest.
  entries.sort((a, b) => {
    const ai = PRIMARY_KEYS.indexOf(a[0]);
    const bi = PRIMARY_KEYS.indexOf(b[0]);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  return (
    <div className="grid grid-cols-2 gap-2.5">
      {entries.map(([key, value]) => {
        const primary = PRIMARY_KEYS.indexOf(key) >= 0 && PRIMARY_KEYS.indexOf(key) < 3;
        return (
          <div key={key} className="stat-card">
            <div className="text-[11px] text-slate-500">
              {STAT_LABELS[key] ?? key.replace(/_/g, " ")}
            </div>
            <div
              className={`mt-1 font-semibold ${
                primary ? "gradient-text text-lg" : "text-base text-white"
              }`}
            >
              {formatStat(key, value)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function Legend({ legend }: { legend: LegendItem[] }) {
  const items = legend.filter((l) => l.label && l.label.trim() !== "");
  if (items.length === 0) return null;
  return (
    <div className="space-y-1.5">
      {items.map((l, i) => (
        <div key={`${l.label}-${i}`} className="flex items-center gap-2.5">
          <span
            className="h-3 w-3 shrink-0 rounded-sm ring-1 ring-white/10"
            style={{ backgroundColor: l.color }}
          />
          <span className="text-xs text-slate-300">{l.label}</span>
        </div>
      ))}
    </div>
  );
}

export function LegendBar({ legend }: { legend: LegendItem[] }) {
  // Continuous gradient bar from legend colors (for ramp-style legends).
  const colors = legend.map((l) => l.color);
  if (colors.length < 2) return null;
  return (
    <div
      className="h-2.5 w-full rounded-full ring-1 ring-white/10"
      style={{
        background: `linear-gradient(90deg, ${colors.join(", ")})`,
      }}
    />
  );
}

export function Toggle<T extends string | number>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="flex rounded-xl border border-line bg-space-850 p-1">
      {options.map((opt) => (
        <button
          key={String(opt.value)}
          onClick={() => onChange(opt.value)}
          className={`flex-1 rounded-lg px-2 py-1.5 text-xs font-medium transition-all duration-200 ${
            value === opt.value
              ? "bg-brand-gradient text-space-950 shadow"
              : "text-slate-400 hover:text-white"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
