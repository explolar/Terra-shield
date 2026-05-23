import {
  Waves,
  Thermometer,
  Sprout,
  Building2,
  Bot,
  Globe2,
  Network,
  CloudRain,
  Droplets,
  type LucideIcon,
} from "lucide-react";
import type { ModuleId } from "@/lib/types";

export interface ModuleMeta {
  id: ModuleId | "earthdata";
  name: string;
  short: string;
  icon: LucideIcon;
  tagline: string;
  description: string;
  accent: string; // tailwind text color for the icon
  gradient: string; // tailwind gradient for cards
}

export const MODULES: ModuleMeta[] = [
  {
    id: "flood",
    name: "FloodAI",
    short: "Flood",
    icon: Waves,
    tagline: "Multi-criteria flood intelligence",
    description:
      "AHP-weighted susceptibility, Sentinel-1 SAR inundation extent and road-access disruption — with reliability scoring.",
    accent: "text-cyan-600",
    gradient: "from-cyan-500/20 to-blue-500/10",
  },
  {
    id: "climate",
    name: "ClimateLens",
    short: "Climate",
    icon: Thermometer,
    tagline: "CMIP6 / SSP future projections",
    description:
      "Downscaled NEX-GDDP-CMIP6 projections of rainfall and temperature under SSP2-4.5 and SSP5-8.5 to the 2080s.",
    accent: "text-rose-600",
    gradient: "from-rose-500/20 to-orange-500/10",
  },
  {
    id: "drought",
    name: "DroughtAI",
    short: "Drought",
    icon: Sprout,
    tagline: "Meteorological & vegetation drought",
    description:
      "Standardized Precipitation Index from CHIRPS and NDVI-based Vegetation Condition Index for crop-stress monitoring.",
    accent: "text-amber-600",
    gradient: "from-amber-500/20 to-yellow-500/10",
  },
  {
    id: "weather",
    name: "WeatherCast",
    short: "Weather",
    icon: CloudRain,
    tagline: "Live short-range rainfall forecast",
    description:
      "Open-Meteo 16-day forecast over your AOI — daily precipitation, heavy-rain days and a flood-watch nowcast for the days ahead.",
    accent: "text-sky-600",
    gradient: "from-sky-500/20 to-cyan-500/10",
  },
  {
    id: "groundwater",
    name: "GroundwaterAI",
    short: "Groundwater",
    icon: Droplets,
    tagline: "GRACE terrestrial water storage",
    description:
      "NASA GRACE / GRACE-FO terrestrial water storage anomalies reveal groundwater depletion and recharge trends at regional / state scale.",
    accent: "text-indigo-600",
    gradient: "from-indigo-500/20 to-blue-500/10",
  },
  {
    id: "infra",
    name: "InfraRisk",
    short: "Infra",
    icon: Building2,
    tagline: "Population & asset exposure",
    description:
      "Overlay hazard footprints on WorldPop population and built-up land cover to quantify who and what is exposed.",
    accent: "text-emerald-600",
    gradient: "from-emerald-500/20 to-teal-500/10",
  },
  {
    id: "resilience",
    name: "ResilienceOR",
    short: "Resilience",
    icon: Network,
    tagline: "Operations research for disaster response",
    description:
      "Optimal shelter siting, shortest-path evacuation routing and budget-constrained mitigation planning — defensible, citable optimization.",
    accent: "text-cyan-700",
    gradient: "from-cyan-500/20 to-emerald-500/10",
  },
  {
    id: "copilot",
    name: "GeoCopilot",
    short: "Copilot",
    icon: Bot,
    tagline: "Ask climate risk in plain English",
    description:
      "A grounded agent that routes natural-language questions to the right model and answers with real, cited numbers.",
    accent: "text-violet-600",
    gradient: "from-violet-500/20 to-fuchsia-500/10",
  },
  {
    id: "earthdata",
    name: "EarthData Engine",
    short: "EarthData",
    icon: Globe2,
    tagline: "Petabyte-scale EO foundation",
    description:
      "A unified gateway to SRTM, Sentinel, CHIRPS, MODIS, WorldCover and WorldPop — live via Earth Engine or deterministic demo.",
    accent: "text-sky-600",
    gradient: "from-sky-500/20 to-indigo-500/10",
  },
];

// The five interactive dashboard modules (excludes the EarthData engine card).
export const DASHBOARD_MODULES = MODULES.filter(
  (m) => m.id !== "earthdata",
) as (ModuleMeta & { id: ModuleId })[];

export function moduleMeta(id: ModuleId | "earthdata"): ModuleMeta {
  return MODULES.find((m) => m.id === id) ?? MODULES[0];
}
