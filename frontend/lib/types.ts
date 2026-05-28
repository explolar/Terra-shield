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
  validation?: string;
  applicable_pct?: number;
  mean_confidence?: number;
}

// AHP consistency summary returned by /flood/susceptibility (Saaty, 1980).
export interface AhpSummary {
  consistency_ratio: number;
  consistent: boolean;
  lambda_max: number;
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
  ahp?: AhpSummary;
  // LIVE ONLY: one XYZ tile URL per factor for per-factor map overlays.
  factor_urls?: Partial<Record<FloodFactor, string>>;

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

  // flood/sar-extent extras (live): a second XYZ tile with a 3-class
  // severity palette baked in, overlaid above the binary flood extent.
  severity_url?: string | null;

  // landslide/susceptibility (ML) extras
  metrics?: LandslideMetrics;
  feature_importance?: MlFeatureImportance[];
  top_factor?: string;
  inventory?: string;
  live_error?: string; // why a live run fell back to demo (diagnostic)
}

// Richer stats returned by /flood/sar-extent (live mode). All optional —
// demo mode returns the basic flood-extent stats only.
export interface SarStats {
  flooded_area_km2?: number;
  flooded_pct?: number;
  population_exposed?: number;
  cropland_flooded_ha?: number;
  crop_loss_usd?: number;
  builtup_flooded_ha?: number;
  threshold_db?: number;
  [key: string]: any;
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

// The 11 paper-grade AHP flood-susceptibility factors (Saaty, 1980).
export type FloodFactor =
  | "distance_to_river"
  | "hand"
  | "rainfall"
  | "slope"
  | "elevation"
  | "drainage_density"
  | "twi"
  | "lulc"
  | "soil"
  | "ndvi"
  | "curvature";

// Ordered list of the 11 factor keys (canonical order).
export const FLOOD_FACTORS: FloodFactor[] = [
  "distance_to_river",
  "hand",
  "rainfall",
  "slope",
  "elevation",
  "drainage_density",
  "twi",
  "lulc",
  "soil",
  "ndvi",
  "curvature",
];

// Human-readable labels for each factor.
export const FLOOD_FACTOR_LABELS: Record<FloodFactor, string> = {
  distance_to_river: "Distance to River",
  hand: "HAND",
  rainfall: "Rainfall",
  slope: "Slope",
  elevation: "Elevation",
  drainage_density: "Drainage Density",
  twi: "TWI",
  lulc: "LULC",
  soil: "Soil Texture",
  ndvi: "NDVI",
  curvature: "Curvature",
};

export type FloodWeights = Record<FloodFactor, number>;

export interface SusceptibilityRequest {
  aoi: AOI;
  weights?: Partial<FloodWeights>;
  rainfall_scenario: RainfallScenario;
  ahp_matrix?: number[][];
}

// ---- FloodAI: multi-year flood-frequency trend ----
// POST /flood/multiyear -> { aoi, years? }
export interface MultiYearPoint {
  year: number;
  flooded_km2: number;
}

export type TrendDirection = "increasing" | "decreasing" | "stable";

export interface MultiYearStats {
  trend_km2_per_year: number;
  trend: TrendDirection;
  peak_year: number;
  peak_km2: number;
  area_km2: number;
}

export interface MultiYearResponse {
  product: "multiyear";
  source: Source;
  series: MultiYearPoint[];
  stats: MultiYearStats;
}

// ---- FloodAI: ML flood-risk classifier ----
// POST /flood/ml-risk -> { aoi, model }
export type MlModel = "gbm" | "xgboost" | "random_forest";

export const ML_MODELS: { value: MlModel; label: string }[] = [
  { value: "gbm", label: "GBM" },
  { value: "xgboost", label: "XGBoost" },
  { value: "random_forest", label: "Random Forest" },
];

export interface MlMetrics {
  cv_accuracy: number;
  cv_accuracy_std: number;
  cv_auc: number;
  n_samples: number;
  positive_rate: number;
}

export interface MlFeatureImportance {
  factor: string;
  importance: number;
}

export interface MlRiskResponse {
  product: "ml_risk";
  source: Source;
  model: MlModel;
  metrics: MlMetrics;
  feature_importance: MlFeatureImportance[];
  top_factor: string;
  explainability: string;
  validation: string;
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

// ---- ClimateLens: ETCCDI climate-extremes indices ----
// POST /climate/extremes -> { aoi, scenario, horizon, model? }
export interface ClimateExtremeIndex {
  key: string; // Rx1day | R95p | CDD | hot_days
  label: string;
  unit: string;
  baseline: number;
  projected: number;
  delta: number;
  pct_change: number;
}

export interface ClimateExtremesResponse {
  product: "extremes";
  source: Source;
  scenario: ClimateScenario;
  horizon: ClimateHorizon;
  model: string;
  reference: string;
  indices: ClimateExtremeIndex[];
}

export type SpiScale = 1 | 3 | 6 | 12;

export type Hazard = "flood" | "drought";

// ---- InfraRisk: road-network criticality (edge betweenness centrality) ----
// POST /infra/criticality -> { aoi }
export type CriticalityTier = "critical" | "important" | "normal";

export interface InfraCriticalityStats {
  segments: number;
  critical_segments: number;
  method: string;
  area_km2: number;
  [key: string]: any;
}

export interface InfraCriticalityResponse {
  product: "road_criticality";
  source: Source;
  grid: LineFeatureCollection;
  legend: LegendItem[];
  stats: InfraCriticalityStats;
}

export type ModuleId =
  | "flood"
  | "climate"
  | "drought"
  | "infra"
  | "resilience"
  | "copilot"
  | "weather"
  | "groundwater"
  | "landslide";

export interface LandslideMetrics {
  f1: number | null;
  precision: number | null;
  recall: number | null;
  roc_auc: number | null;
  accuracy: number | null;
  n_samples: number;
  positive_rate: number;
}

// ---- WeatherCast: live short-range forecast (Open-Meteo) ----
// POST /weather/forecast -> { aoi, days }
export type FloodWatch = "no heavy rain" | "heavy rain" | "very heavy rain";

export interface WeatherDaily {
  date: string;
  precip_mm: number | null;
  precip_prob: number | null;
  tmax_c: number | null;
  tmin_c: number | null;
  wind_kmh: number | null;
}

export interface WeatherSummary {
  total_precip_mm: number;
  heavy_rain_days: number;
  peak_precip_mm: number;
  peak_date: string;
  flood_watch: FloodWatch;
}

export interface WeatherForecastResponse {
  module: "weather";
  product: "forecast";
  source: Source;
  provider: string;
  latitude: number;
  longitude: number;
  days: number;
  daily: WeatherDaily[];
  summary: WeatherSummary;
}

// ---- GroundwaterAI: NASA GRACE terrestrial water storage ----
// POST /groundwater/storage -> { aoi }
export type GroundwaterStressClass =
  | "Severe depletion"
  | "High depletion"
  | "Moderate depletion"
  | "Stable"
  | "Recharging";

export interface GroundwaterSeriesPoint {
  year: number;
  anomaly_cm: number;
}

export interface GroundwaterStats {
  mean_anomaly_cm: number;
  depletion_trend_cm_yr: number;
  stress_class: GroundwaterStressClass | string;
  recharge_proxy_mm_yr: number | null;
  area_km2: number;
  dataset?: string;
}

export interface GroundwaterResponse {
  module: "groundwater";
  product: "storage";
  source: Source;
  // LIVE: GRACE anomaly XYZ tile. DEMO: null.
  tile_url: string | null;
  // DEMO: polygon cells with properties.anomaly_cm. LIVE: null.
  grid: GeoJSONFeatureCollection | null;
  // Categorical stress classes describing the trend (shown as a small legend).
  legend: LegendItem[];
  // DEMO: ~20-year series. LIVE: [].
  series: GroundwaterSeriesPoint[];
  stats: GroundwaterStats;
}

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
  source?: string;
  exposed_population?: number;
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
  labels?: Record<string, string> | string[];
  weights: Record<string, number>;
  consistency_ratio: number;
  consistent: boolean;
  lambda_max: number;
  n_factors?: number;
}
