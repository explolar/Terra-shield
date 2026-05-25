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
  Mountain,
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
    tagline: "Flood risk, mapped",
    description:
      "Flood susceptibility, live flood extent from radar, and which roads get cut off — with a reliability score on every result.",
    accent: "text-cyan-600",
    gradient: "from-cyan-500/20 to-blue-500/10",
  },
  {
    id: "climate",
    name: "ClimateLens",
    short: "Climate",
    icon: Thermometer,
    tagline: "Climate futures to 2080",
    description:
      "Downscaled rainfall and temperature projections under moderate and high-emission scenarios, through the 2080s.",
    accent: "text-rose-600",
    gradient: "from-rose-500/20 to-orange-500/10",
  },
  {
    id: "drought",
    name: "DroughtAI",
    short: "Drought",
    icon: Sprout,
    tagline: "Rainfall & vegetation stress",
    description:
      "Track rainfall deficits and vegetation stress to spot drought and crop risk early.",
    accent: "text-amber-600",
    gradient: "from-amber-500/20 to-yellow-500/10",
  },
  {
    id: "weather",
    name: "WeatherCast",
    short: "Weather",
    icon: CloudRain,
    tagline: "Live rainfall forecast",
    description:
      "A live forecast over your area — daily rainfall, heavy-rain days and a flood watch for the days ahead.",
    accent: "text-sky-600",
    gradient: "from-sky-500/20 to-cyan-500/10",
  },
  {
    id: "groundwater",
    name: "GroundwaterAI",
    short: "Groundwater",
    icon: Droplets,
    tagline: "Groundwater depletion",
    description:
      "Groundwater storage and depletion trends from satellite gravimetry — see where the water table is falling.",
    accent: "text-indigo-600",
    gradient: "from-indigo-500/20 to-blue-500/10",
  },
  {
    id: "landslide",
    name: "LandslideAI",
    short: "Landslide",
    icon: Mountain,
    tagline: "ML susceptibility (F1/AUC)",
    description:
      "Machine-learned landslide susceptibility trained on a national inventory — slope, rainfall, terrain and more — with F1, ROC-AUC and feature importance.",
    accent: "text-orange-600",
    gradient: "from-orange-500/20 to-amber-500/10",
  },
  {
    id: "infra",
    name: "InfraRisk",
    short: "Infra",
    icon: Building2,
    tagline: "People & assets at risk",
    description:
      "Overlay any hazard on population and built-up land to see who and what is exposed.",
    accent: "text-emerald-600",
    gradient: "from-emerald-500/20 to-teal-500/10",
  },
  {
    id: "resilience",
    name: "ResilienceOR",
    short: "Resilience",
    icon: Network,
    tagline: "Plan the response",
    description:
      "Optimize shelter placement, evacuation routes and where to spend a mitigation budget for the biggest risk cut.",
    accent: "text-cyan-700",
    gradient: "from-cyan-500/20 to-emerald-500/10",
  },
  {
    id: "copilot",
    name: "GeoCopilot",
    short: "Copilot",
    icon: Bot,
    tagline: "Ask in plain English",
    description:
      "Ask about climate risk in plain English and get answers backed by real numbers from the models.",
    accent: "text-violet-600",
    gradient: "from-violet-500/20 to-fuchsia-500/10",
  },
  {
    id: "earthdata",
    name: "EarthData Engine",
    short: "EarthData",
    icon: Globe2,
    tagline: "All your Earth data, unified",
    description:
      "One gateway to the world's satellite and climate datasets — live, or a deterministic demo when offline.",
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
