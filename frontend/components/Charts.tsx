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
  Legend as RechartsLegend,
} from "recharts";
import type {
  LayerResponse,
  MultiYearPoint,
  MlFeatureImportance,
  ClimateExtremeIndex,
  WeatherDaily,
  GroundwaterSeriesPoint,
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

// ---- WeatherCast: short date label (e.g. "Mon 12") from an ISO date ----
function shortDate(iso: string): string {
  const d = new Date(iso + "T00:00:00");
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { weekday: "short", day: "numeric" });
}

// ---- WeatherCast: daily precipitation bar chart (precip_mm + probability) ----
export function WeatherPrecipChart({ daily }: { daily: WeatherDaily[] }) {
  if (!daily.length) {
    return (
      <p className="text-xs text-ink-subtle">No forecast data available.</p>
    );
  }
  const data = daily.map((d) => ({
    name: shortDate(d.date),
    full: d.date,
    precip: d.precip_mm ?? 0,
    prob: d.precip_prob,
  }));
  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
          <defs>
            <linearGradient id="weatherPrecip" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0ea5e9" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.55} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
          <XAxis
            dataKey="name"
            tick={axisStyle}
            tickLine={false}
            axisLine={{ stroke: gridStroke }}
            interval="preserveStartEnd"
            minTickGap={8}
          />
          <YAxis
            tick={axisStyle}
            tickLine={false}
            axisLine={false}
            width={40}
            unit="mm"
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
                    {payload[0].value} mm precip
                  </div>
                  {typeof payload[0].payload.prob === "number" && (
                    <div className="text-ink-muted">
                      {payload[0].payload.prob}% probability
                    </div>
                  )}
                </div>
              ) : null
            }
          />
          <Bar dataKey="precip" fill="url(#weatherPrecip)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---- WeatherCast: daily temperature range (tmax / tmin) line chart ----
export function WeatherTempChart({ daily }: { daily: WeatherDaily[] }) {
  const data = daily
    .filter((d) => d.tmax_c !== null || d.tmin_c !== null)
    .map((d) => ({
      name: shortDate(d.date),
      full: d.date,
      tmax: d.tmax_c,
      tmin: d.tmin_c,
    }));
  if (!data.length) return null;
  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 6, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
          <XAxis
            dataKey="name"
            tick={axisStyle}
            tickLine={false}
            axisLine={{ stroke: gridStroke }}
            interval="preserveStartEnd"
            minTickGap={8}
          />
          <YAxis
            tick={axisStyle}
            tickLine={false}
            axisLine={false}
            width={40}
            unit="°"
            domain={["auto", "auto"]}
          />
          <Tooltip
            cursor={{ stroke: "#94a3b8", strokeWidth: 1 }}
            content={({ active, payload }: any) =>
              active && payload?.length ? (
                <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-panel">
                  <div className="font-semibold text-ink">
                    {payload[0].payload.full}
                  </div>
                  {payload.map((p: any) => (
                    <div key={p.dataKey} className="text-ink-muted">
                      {p.dataKey === "tmax" ? "Max" : "Min"}: {p.value}°C
                    </div>
                  ))}
                </div>
              ) : null
            }
          />
          <RechartsLegend
            wrapperStyle={{ fontSize: 11 }}
            iconType="circle"
            iconSize={8}
          />
          <Line
            type="monotone"
            dataKey="tmax"
            name="Max"
            stroke="#f97316"
            strokeWidth={2.2}
            dot={false}
            activeDot={{ r: 4, fill: "#f97316" }}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="tmin"
            name="Min"
            stroke="#0ea5e9"
            strokeWidth={2.2}
            dot={false}
            activeDot={{ r: 4, fill: "#0ea5e9" }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---- GroundwaterAI: GRACE storage-anomaly trend (cm), anchored at 0 ----
export function GroundwaterTrendChart({
  series,
}: {
  series: GroundwaterSeriesPoint[];
}) {
  if (!series.length) {
    return (
      <p className="text-xs text-ink-subtle">
        Per-year series available in demo mode.
      </p>
    );
  }
  return (
    <div className="h-52 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={series}
          margin={{ top: 6, right: 8, left: -14, bottom: 0 }}
        >
          <defs>
            <linearGradient id="gwLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#0ea5e9" />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={gridStroke}
            vertical={false}
          />
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
            unit="cm"
          />
          <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
          <Tooltip
            cursor={{ stroke: "#94a3b8", strokeWidth: 1 }}
            content={({ active, payload, label }: any) =>
              active && payload?.length ? (
                <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-panel">
                  <div className="font-semibold text-ink">{label}</div>
                  <div className="text-ink-muted">
                    {Number(payload[0].value) > 0 ? "+" : ""}
                    {payload[0].value} cm anomaly
                  </div>
                </div>
              ) : null
            }
          />
          <Line
            type="monotone"
            dataKey="anomaly_cm"
            stroke="url(#gwLine)"
            strokeWidth={2.4}
            dot={{ r: 2.5, fill: "#6366f1", strokeWidth: 0 }}
            activeDot={{ r: 4, fill: "#6366f1" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---- ClimateLens extremes: grouped horizontal baseline vs projected bars ----
export function ExtremesChart({ indices }: { indices: ClimateExtremeIndex[] }) {
  if (!indices.length) {
    return (
      <p className="text-xs text-ink-subtle">No extremes indices available.</p>
    );
  }
  const rows = indices.map((d) => ({
    label: d.label,
    unit: d.unit,
    baseline: d.baseline,
    projected: d.projected,
  }));
  // Height scales with the number of indices (one grouped pair per index).
  const height = Math.max(180, rows.length * 46 + 28);
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 4, right: 14, left: 4, bottom: 4 }}
          barCategoryGap={10}
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
            width={70}
          />
          <Tooltip
            cursor={{ fill: "rgba(148,163,184,0.12)" }}
            content={({ active, payload }: any) =>
              active && payload?.length ? (
                <div className="rounded-lg border border-line bg-white px-3 py-2 text-xs shadow-panel">
                  <div className="font-semibold text-ink">
                    {payload[0].payload.label}
                  </div>
                  {payload.map((p: any) => (
                    <div key={p.dataKey} className="text-ink-muted">
                      {p.dataKey === "baseline" ? "Baseline" : "Projected"}:{" "}
                      {p.value} {payload[0].payload.unit}
                    </div>
                  ))}
                </div>
              ) : null
            }
          />
          <RechartsLegend
            wrapperStyle={{ fontSize: 11 }}
            iconType="circle"
            iconSize={8}
          />
          <Bar
            dataKey="baseline"
            name="Baseline"
            fill="#94a3b8"
            radius={[0, 3, 3, 0]}
            barSize={9}
          />
          <Bar
            dataKey="projected"
            name="Projected"
            fill="#ef4444"
            radius={[0, 3, 3, 0]}
            barSize={9}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
