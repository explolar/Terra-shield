// TypeScript types mirroring the TerraShield backend API contract.

export type Source = "live" | "demo";

export interface AOI {
  type: "bbox";
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
}

export interface LegendItem {
  label: string;
  color: string;
  min?: number;
  max?: number;
}

export type GeoJSONFeatureCollection = {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
};

export type GeoJSONFeature = {
  type: "Feature";
  properties: Record<string, any>;
  geometry: {
    type: "Polygon" | "LineString" | "MultiPolygon";
    coordinates: any;
  };
};

export interface Reliability {
  method: string;
  validation: string;
  applicable_pct: number;
  mean_confidence: number;
}

export interface TimeseriesPoint {
  year: number;
  value: number;
}

export interface LayerResponse {
  module: string;
  product: string;
  source: Source;
  tile_url: string | null;
  grid: GeoJSONFeatureCollection | null;
  legend: LegendItem[];
  stats: Record<string, any>;
  aoi: { bbox: number[]; centroid: number[] };

  // flood/susceptibility extras
  reliability?: Reliability;
  weights?: Record<string, number>;
  rainfall_scenario?: string;

  // climate/projection extras
  scenario?: string;
  variable?: string;
  variable_label?: string;
  unit?: string;
  horizon?: string;
  model?: string;
  baseline?: number;
  projected?: number;
  delta?: number;
  pct_change?: number;
  timeseries?: TimeseriesPoint[];

  // drought
  scale_months?: number;

  // infra
  hazard?: string;
}

export interface EarthdataStatus {
  mode: Source;
  project: string | null;
  error: string | null;
  ee_installed: boolean;
}

export interface DatasetEntry {
  id: string;
  name: string;
  module: string[] | string;
  var: string;
  resolution: string;
  license: string;
}

export interface Basemap {
  id: string;
  name: string;
  url: string;
  attribution: string;
}

export interface ClimateScenarios {
  scenarios: string[];
  variables: Record<string, { label: string; unit: string; ramp: string }>;
  horizons: string[];
  baseline: string;
  models: string[];
  dataset: string;
}

export interface CopilotTool {
  name: string;
  module: string;
  description: string;
}

export interface CopilotPlanStep {
  step: string;
  [key: string]: any;
}

export interface CopilotResponse {
  question: string;
  answer: string;
  tool: string;
  module: string;
  plan: CopilotPlanStep[];
  layers: LayerResponse[];
  citations: string[];
  source: Source;
  llm_used: boolean;
  note: string | null;
}

// ---- request bodies ----
export type RainfallScenario = "normal" | "wet" | "extreme";

export interface FloodWeights {
  elevation: number;
  slope: number;
  twi: number;
  drainage: number;
  rainfall: number;
  landuse: number;
}

export interface SusceptibilityRequest {
  aoi: AOI;
  weights?: Partial<FloodWeights>;
  rainfall_scenario: RainfallScenario;
}

export type ClimateScenario = "ssp245" | "ssp585";
export type ClimateVariable = "pr" | "tas" | "tasmax";
export type ClimateHorizon = "2030s" | "2050s" | "2080s";

export interface ProjectionRequest {
  aoi: AOI;
  scenario: ClimateScenario;
  variable: ClimateVariable;
  horizon: ClimateHorizon;
  model: string;
}

export type SpiScale = 1 | 3 | 6 | 12;

export type Hazard = "flood" | "drought";

export type ModuleId =
  | "flood"
  | "climate"
  | "drought"
  | "infra"
  | "resilience"
  | "copilot";

// ---- ResilienceOR (operations research) ----

// A Point FeatureCollection (shelters) and LineString FeatureCollection (routes).
export type PointFeatureCollection = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    properties: Record<string, any>;
    geometry: { type: "Point"; coordinates: [number, number] };
  }[];
};

export type LineFeatureCollection = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    properties: Record<string, any>;
    geometry: { type: "LineString"; coordinates: [number, number][] };
  }[];
};

export interface ShelterRequest {
  aoi: AOI;
  num_shelters: number; // 1..20
  radius_km: number;
}

export interface ShelterResponse {
  chosen: (string | number)[];
  coverage_pct: number;
  uncovered_pct: number;
  candidate_sites: number;
  demand_points: number;
  radius_km: number;
  shelters_geojson: PointFeatureCollection;
  aoi: { bbox: number[]; centroid: number[] };
}

export interface EvacuationRequest {
  aoi: AOI;
}

export interface EvacuationResponse {
  reachable: boolean;
  route_km: number;
  segments: number;
  crosses_flood: boolean;
  route_geojson: LineFeatureCollection;
  source: string;
  aoi: { bbox: number[]; centroid: number[] };
}

export interface MitigationRequest {
  budget: number;
}

export interface MitigationResponse {
  selected: (string | number)[];
  total_cost: number;
  total_risk_reduction: number;
  budget: number;
  budget_used_pct: number;
}

export interface AhpResponse {
  labels: Record<string, string> | string[];
  weights: Record<string, number>;
  consistency_ratio: number;
  consistent: boolean;
  lambda_max: number;
}
