// Typed API client for the TerraShield backend.
import type {
  AOI,
  Basemap,
  ClimateScenarios,
  ClimateHorizon,
  ClimateScenario,
  ClimateVariable,
  CopilotResponse,
  CopilotTool,
  DatasetEntry,
  EarthdataStatus,
  FloodWeights,
  Hazard,
  LayerResponse,
  RainfallScenario,
  SpiScale,
  ShelterRequest,
  ShelterResponse,
  EvacuationRequest,
  EvacuationResponse,
  MitigationRequest,
  MitigationResponse,
  AhpResponse,
  MultiYearResponse,
  MlRiskResponse,
  MlModel,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  detail?: string;
  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });
  } catch (e) {
    throw new ApiError(
      "Cannot reach the TerraShield backend. Is it running at " + API_BASE + "?",
      0,
    );
  }

  if (!res.ok) {
    let detail: string | undefined;
    try {
      const body = await res.json();
      detail =
        typeof body?.detail === "string"
          ? body.detail
          : body?.error || JSON.stringify(body);
    } catch {
      detail = res.statusText;
    }
    throw new ApiError(`Request failed (${res.status})`, res.status, detail);
  }

  return (await res.json()) as T;
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

// ---- EarthData Engine ----
export const getStatus = () => request<EarthdataStatus>("/earthdata/status");
export const getDatasets = () =>
  request<{ datasets: DatasetEntry[] }>("/earthdata/datasets");
export const getBasemaps = () =>
  request<{ basemaps: Basemap[] }>("/earthdata/basemaps");

// ---- FloodAI ----
export const floodSusceptibility = (body: {
  aoi: AOI;
  weights?: Partial<FloodWeights>;
  rainfall_scenario: RainfallScenario;
  ahp_matrix?: number[][];
}) => post<LayerResponse>("/flood/susceptibility", body);

export const floodSarExtent = (body: { aoi: AOI }) =>
  post<LayerResponse>("/flood/sar-extent", body);

export const floodRoadRisk = (body: { aoi: AOI; depth_threshold?: number }) =>
  post<LayerResponse>("/flood/road-risk", body);

// Multi-year flood-frequency trend (live can take ~30-60s).
export const floodMultiyear = (aoi: AOI, years?: number) =>
  post<MultiYearResponse>(
    "/flood/multiyear",
    years != null ? { aoi, years } : { aoi },
  );

// ML flood-risk classifier (live training can take ~30-50s).
export const floodMlRisk = (aoi: AOI, model: MlModel) =>
  post<MlRiskResponse>("/flood/ml-risk", { aoi, model });

// ---- ClimateLens ----
export const getClimateScenarios = () =>
  request<ClimateScenarios>("/climate/scenarios");

export const climateProjection = (body: {
  aoi: AOI;
  scenario: ClimateScenario;
  variable: ClimateVariable;
  horizon: ClimateHorizon;
  model: string;
}) => post<LayerResponse>("/climate/projection", body);

// ---- DroughtAI ----
export const droughtSpi = (body: { aoi: AOI; scale_months: SpiScale }) =>
  post<LayerResponse>("/drought/spi", body);

export const droughtVegetation = (body: { aoi: AOI }) =>
  post<LayerResponse>("/drought/vegetation", body);

// ---- InfraRisk ----
export const infraExposure = (body: { aoi: AOI; hazard: Hazard }) =>
  post<LayerResponse>("/infra/exposure", body);

// ---- GeoCopilot ----
export const getCopilotTools = () =>
  request<{ tools: CopilotTool[] }>("/copilot/tools");

export const copilotAsk = (body: { question: string; aoi?: AOI }) =>
  post<CopilotResponse>("/copilot/ask", body);

// ---- ResilienceOR (operations research) ----
export const optimizeShelters = (body: ShelterRequest) =>
  post<ShelterResponse>("/optimize/shelters", body);

export const optimizeEvacuation = (body: EvacuationRequest) =>
  post<EvacuationResponse>("/optimize/evacuation", body);

export const optimizeMitigation = (body: MitigationRequest) =>
  post<MitigationResponse>("/optimize/mitigation", body);

export const getAhpDefault = () =>
  request<AhpResponse>("/optimize/ahp/default");
