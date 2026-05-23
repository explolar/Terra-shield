// Preset India AOIs and shared constants.
import type { AOI } from "./types";

export interface LocationPreset {
  id: string;
  name: string;
  region: string;
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
}

export const LOCATIONS: LocationPreset[] = [
  { id: "satara", name: "Satara", region: "Maharashtra", bbox: [73.9, 17.5, 74.3, 17.9] },
  { id: "pune", name: "Pune", region: "Maharashtra", bbox: [73.7, 18.4, 74.0, 18.7] },
  { id: "mumbai", name: "Mumbai", region: "Maharashtra", bbox: [72.75, 18.9, 73.0, 19.3] },
  { id: "chennai", name: "Chennai", region: "Tamil Nadu", bbox: [80.1, 12.9, 80.35, 13.2] },
  { id: "kerala", name: "Kerala", region: "Kerala", bbox: [76.0, 9.5, 77.0, 10.5] },
  { id: "patna", name: "Patna", region: "Bihar", bbox: [85.0, 25.5, 85.3, 25.7] },
  { id: "delhi", name: "Delhi", region: "NCR", bbox: [76.9, 28.4, 77.4, 28.9] },
  { id: "guwahati", name: "Guwahati", region: "Assam", bbox: [91.6, 26.0, 91.9, 26.3] },
];

export const DEFAULT_LOCATION = LOCATIONS[0];

// ---- India state presets (loaded at runtime from /geo) ----
export interface StatePreset {
  name: string;
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  centroid: [number, number]; // [lon, lat]
}

let _statePresetsCache: StatePreset[] | null = null;

// Fetch the 32 India state presets from the static geo asset (cached).
export async function loadStatePresets(): Promise<StatePreset[]> {
  if (_statePresetsCache) return _statePresetsCache;
  const res = await fetch("/geo/india_states_presets.json");
  if (!res.ok) throw new Error("Failed to load state presets");
  const data = (await res.json()) as StatePreset[];
  _statePresetsCache = data;
  return data;
}

export function bboxToAOI(
  bbox: [number, number, number, number],
): AOI {
  return { type: "bbox", bbox };
}

// [lat, lon] center for Leaflet from a [minLon, minLat, maxLon, maxLat] bbox.
export function bboxCenter(
  bbox: [number, number, number, number],
): [number, number] {
  return [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2];
}

// Leaflet bounds [[south, west], [north, east]].
export function bboxToLeafletBounds(
  bbox: [number, number, number, number],
): [[number, number], [number, number]] {
  return [
    [bbox[1], bbox[0]],
    [bbox[3], bbox[2]],
  ];
}

// Light Carto Positron basemap — clean, professional, reads well with overlays.
export const LIGHT_BASEMAP = {
  url: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
  attribution: "© OpenStreetMap, © CARTO",
};

// Kept for backwards compatibility; default is now the light basemap.
export const DARK_BASEMAP = LIGHT_BASEMAP;

export const COPILOT_EXAMPLES = [
  "How will flood risk in Satara change under SSP585 by 2050?",
  "What is the SAR-detected flood extent over Patna?",
  "Show the 6-month SPI drought conditions for Kerala",
  "How many people are exposed to flooding in Chennai?",
];
