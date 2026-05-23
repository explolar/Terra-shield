"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell,
  ReferenceLine,
} from "recharts";
import type {
  LayerResponse,
  MultiYearPoint,
  MlFeatureImportance,
} from "@/lib/types";
import { FLOOD_FACTOR_LABELS, type FloodFactor } from "@/lib/types";
import { HAZARD_RAMP, rampColor } from "@/lib/colors";

const axisStyle = { fill: "#64748b", fontSize: 11 };
const gridStroke = "#e2e8f0";

function ChartTooltip({ active, payload, label, unit }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-panel">
      <div className="font-semibold text-ink">{label}</div>
      <div className="text-ink-muted">
        {payload[0].value}
        {unit ? ` ${unit}` : ""}
      </div>
    </div>
  );
}

export function ClimateTimeseries({ layer }: { layer: LayerResponse }) {
  const data = layer.timeseries ?? [];
  if (!data.length) {
    return (
      <p className="text-xs text-ink-subtle">
        Time series available on the demo path; live projections return the map
        delta only.
      </p>
    );
  }
  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 6, right: 8, left: -16, bottom: 0 }}>
          <defs>
            <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#22d3ee" />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
          <XAxis
            dataKey="year"
            tick={axisStyle}
            tickLine={false}
            axisLine={{ stroke: gridStroke }}
            interval="preserveStartEnd"
            minTickGap={28}
          />
          <YAxis
            tick={axisStyle}
            tickLine={false}
            axisLine={false}
            width={44}
            domain={["auto", "auto"]}
          />
          <Tooltip content={<ChartTooltip unit={layer.unit} />} />
          {typeof layer.baseline === "number" && (
            <ReferenceLine
              y={layer.baseline}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              label={{ value: "baseline", fill: "#64748b", fontSize: 10, position: "insideTopLeft" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="value"
            stroke="url(#lineGrad)"
            strokeWidth={2.4}
            dot={false}
            activeDot={{ r: 4, fill: "#22d3ee" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function FloodClassChart({ layer }: { layer: LayerResponse }) {
  const classPct = layer.stats?.class_pct as Record<string, number> | undefined;
  if (!classPct) {
    return (
      <p className="text-xs text-ink-subtle">
        Class distribution available on the demo path.
      </p>
    );
  }
  const labels = Object.keys(classPct);
  const data = labels.map((label, i) => ({
    name: label.replace("Very ", "V."),
    full: label,
    value: classPct[label],
    color: rampColor(HAZARD_RAMP, labels.length > 1 ? i / (labels.length - 1) : 0),
  }));
  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
          <XAxis
            dataKey="name"
            tick={axisStyle}
            tickLine={false}
            axisLine={{ stroke: gridStroke }}
          />
          <YAxis
            tick={axisStyle}
            tickLine={false}
            axisLine={false}
            width={40}
            unit="%"
          />
          <Tooltip
            cursor={{ fill: "rgba(148,163,184,0.12)" }}
            content={({ active, payload }: any) =>
              active && payload?.length ? (
                <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-panel">
                  <div className="font-semibold text-ink">
                    {payload[0].payload.full}
                  </div>
                  <div className="text-ink-muted">
                    {payload[0].value}% of area
                  </div>
                </div>
              ) : null
            }
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// A horizontal SPI gauge from -2.5 to +2.5.
export function SpiGauge({ layer }: { layer: LayerResponse }) {
  const spi = layer.stats?.mean_spi as number | undefined;
  if (typeof spi !== "number") return null;
  const min = -2.5;
  const max = 2.5;
  const pct = ((spi - min) / (max - min)) * 100;
  const clamped = Math.max(0, Math.min(100, pct));
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="text-xs text-ink-subtle">SPI scale</span>
        <span className="gradient-text text-2xl font-bold">{spi.toFixed(2)}</span>
      </div>
      <div className="relative h-3 w-full rounded-full ring-1 ring-slate-900/10"
        style={{
          background:
            "linear-gradient(90deg,#730000,#e60000,#ffaa00,#fcd37f,#f1f5f9,#a6d96a,#1a9641)",
        }}
      >
        <div
          className="absolute top-1/2 h-5 w-1.5 -translate-y-1/2 -translate-x-1/2 rounded-full border border-slate-300 bg-white shadow-[0_1px_4px_rgba(15,23,42,0.4)]"
          style={{ left: `${clamped}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-ink-subtle">
        <span>-2.5 dry</span>
        <span>0</span>
        <span>+2.5 wet</span>
      </div>
    </div>
  );
}

// A simple radial-style VCI / generic 0-1 meter.
export function PercentMeter({
  value,
  label,
  color = "#22d3ee",
}: {
  value: number; // 0..1
  label: string;
  color?: string;
}) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <span className="text-xs text-ink-subtle">{label}</span>
        <span className="text-lg font-semibold text-ink">
          {value.toFixed(2)}
        </span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-surface-muted ring-1 ring-slate-900/5">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ---- FloodAI multi-year: area-filled flood-frequency trend ----
export function MultiYearChart({ series }: { series: MultiYearPoint[] }) {
  if (!series.length) {
    return (
      <p className="text-xs text-ink-subtle">No multi-year series available.</p>
    );
  }
  return (
    <div className="h-52 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={series} margin={{ top: 6, right: 8, left: -14, bottom: 0 }}>
          <defs>
            <linearGradient id="multiyearArea" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="multiyearLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
          <XAxis
            dataKey="year"
            tick={axisStyle}
            tickLine={false}
            axisLine={{ stroke: gridStroke }}
            interval="preserveStartEnd"
            minTickGap={24}
          />
          <YAxis
            tick={axisStyle}
            tickLine={false}
            axisLine={false}
            width={46}
            domain={["auto", "auto"]}
          />
          <Tooltip
            cursor={{ stroke: "#94a3b8", strokeWidth: 1 }}
            content={({ active, payload, label }: any) =>
              active && payload?.length ? (
                <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-panel">
                  <div className="font-semibold text-ink">{label}</div>
                  <div className="text-ink-muted">
                    {payload[0].value} km² flooded
                  </div>
                </div>
              ) : null
            }
          />
          <Area
            type="monotone"
            dataKey="flooded_km2"
            stroke="url(#multiyearLine)"
            strokeWidth={2.4}
            fill="url(#multiyearArea)"
            dot={{ r: 2.5, fill: "#06b6d4", strokeWidth: 0 }}
            activeDot={{ r: 4, fill: "#06b6d4" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---- FloodAI ML-risk: horizontal SHAP feature-importance bars ----
export function MlFeatureImportanceChart({
  data,
  topFactor,
}: {
  data: MlFeatureImportance[];
  topFactor?: string;
}) {
  if (!data.length) {
    return (
      <p className="text-xs text-ink-subtle">
        No feature importance available.
      </p>
    );
  }
  // Sort descending and resolve human labels from FLOOD_FACTOR_LABELS.
  const rows = [...data]
    .sort((a, b) => b.importance - a.importance)
    .map((d) => ({
      ...d,
      label:
        FLOOD_FACTOR_LABELS[d.factor as FloodFactor] ??
        d.factor.replace(/_/g, " "),
      isTop: d.factor === topFactor,
    }));
  // Height scales with the number of factors (the 11 flood factors).
  const height = Math.max(180, rows.length * 26 + 16);
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 4, right: 12, left: 4, bottom: 4 }}
          barCategoryGap={4}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} horizontal={false} />
          <XAxis
            type="number"
            tick={axisStyle}
            tickLine={false}
            axisLine={{ stroke: gridStroke }}
          />
          <YAxis
            type="category"
            dataKey="label"
            tick={{ ...axisStyle, fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={104}
          />
          <Tooltip
            cursor={{ fill: "rgba(148,163,184,0.12)" }}
            content={({ active, payload }: any) =>
              active && payload?.length ? (
                <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-panel">
                  <div className="font-semibold text-ink">
                    {payload[0].payload.label}
                  </div>
                  <div className="text-ink-muted">
                    importance {Number(payload[0].value).toFixed(3)}
                  </div>
                </div>
              ) : null
            }
          />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {rows.map((d, i) => (
              <Cell key={i} fill={d.isTop ? "#10b981" : "#7dd3fc"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
