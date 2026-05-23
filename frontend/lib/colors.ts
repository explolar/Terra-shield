// Centralized color / choropleth helpers.
import type { LegendItem } from "./types";

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace("#", "");
  const full =
    h.length === 3
      ? h
          .split("")
          .map((c) => c + c)
          .join("")
      : h;
  const num = parseInt(full, 16);
  return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
}

function rgbToHex(r: number, g: number, b: number): string {
  const to = (n: number) => clamp(Math.round(n), 0, 255).toString(16).padStart(2, "0");
  return `#${to(r)}${to(g)}${to(b)}`;
}

/**
 * Interpolate a hex color from an ordered list of colors given t in [0, 1].
 */
export function rampColor(colors: string[], t: number): string {
  if (colors.length === 0) return "#888888";
  if (colors.length === 1) return colors[0];
  const x = clamp(t, 0, 1) * (colors.length - 1);
  const i = Math.floor(x);
  const f = x - i;
  if (i >= colors.length - 1) return colors[colors.length - 1];
  const [r1, g1, b1] = hexToRgb(colors[i]);
  const [r2, g2, b2] = hexToRgb(colors[i + 1]);
  return rgbToHex(r1 + (r2 - r1) * f, g1 + (g2 - g1) * f, b1 + (b2 - b1) * f);
}

/**
 * Compute the [min, max] range for a value given a legend.
 * Falls back to a sensible default per detected scheme.
 */
export function legendRange(
  legend: LegendItem[],
  fallback: [number, number] = [0, 1],
): [number, number] {
  const mins = legend.map((l) => l.min).filter((v): v is number => typeof v === "number");
  const maxs = legend.map((l) => l.max).filter((v): v is number => typeof v === "number");
  if (mins.length && maxs.length) {
    return [Math.min(...mins), Math.max(...maxs)];
  }
  return fallback;
}

/**
 * Map a numeric value to a hex color by interpolating across the legend colors
 * within a [min, max] range.
 */
export function valueToColor(
  value: number,
  legend: LegendItem[],
  range?: [number, number],
): string {
  const colors = legend.map((l) => l.color);
  if (colors.length === 0) return "#22d3ee";
  const [lo, hi] = range ?? legendRange(legend);
  const span = hi - lo || 1;
  const t = (value - lo) / span;
  return rampColor(colors, t);
}

/**
 * Determine the value range and key for a layer's grid choropleth based on the
 * product. Returns the property key + a range used to color cells.
 */
export function productValueConfig(product: string): {
  key: string;
  range: [number, number];
} {
  switch (product) {
    case "susceptibility":
      return { key: "susceptibility", range: [0, 1] };
    case "sar_extent":
      return { key: "flooded", range: [0, 1] };
    case "spi":
      return { key: "spi", range: [-2.5, 2.5] };
    case "vegetation":
      return { key: "vci", range: [0, 1] };
    case "exposure":
      return { key: "exposure", range: [0, 1] };
    case "projection":
    case "anomaly":
      return { key: "delta", range: [0, 1] }; // overridden dynamically
    default:
      return { key: "value", range: [0, 1] };
  }
}

// Brand palette tokens (kept in one place for reuse in non-Tailwind contexts).
export const BRAND = {
  emerald: "#10b981",
  cyan: "#06b6d4",
  surface: "#ffffff",
  surfaceSubtle: "#f8fafc",
  border: "#e2e8f0",
  ink: "#0f172a",
  inkMuted: "#475569",
};

// ---- GroundwaterAI: diverging GRACE storage-anomaly palette ----
// Negative (depleted) = red -> brown, near zero = pale, positive (gain) = blue.
// Anchored around 0 so the pale midpoint always lands on a zero anomaly.
const GW_MID = "#f5f5f5"; // near-zero anomaly (pale)
// Each ramp runs pale (near 0) -> saturated (large magnitude).
const GW_NEG_RAMP = [GW_MID, "#f6e8c3", "#dfc27d", "#bf812d", "#8c510a"]; // depleted -> red/brown
const GW_POS_RAMP = [GW_MID, "#c7eae5", "#80cdc1", "#35978f", "#01665e"]; // gain -> teal/blue

/**
 * Map a GRACE storage anomaly (cm) to a diverging color, anchored at 0.
 * `span` is the symmetric half-range used to normalize magnitude (default 16cm,
 * matching the ~ -16..+13 demo grid). Depleted (negative) = red -> brown,
 * near zero = pale, gain (positive) = teal -> blue.
 */
export function anomalyColor(value: number, span = 16): string {
  if (!Number.isFinite(value)) return GW_MID;
  const t = clamp(Math.abs(value) / (span || 1), 0, 1);
  return rampColor(value < 0 ? GW_NEG_RAMP : GW_POS_RAMP, t);
}

// Hazard ramp used in legends (greens -> yellows -> reds).
export const HAZARD_RAMP = [
  "#1a9850",
  "#91cf60",
  "#d9ef8b",
  "#fee08b",
  "#fc8d59",
  "#d73027",
  "#7f0000",
];
