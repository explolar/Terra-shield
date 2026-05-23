"use client";

import { motion } from "framer-motion";
import { moduleMeta } from "@/components/modules";
import {
  ClimateControls,
  DroughtControls,
  FloodControls,
  InfraControls,
  type ClimateControlState,
  type DroughtControlState,
  type FloodControlState,
  type InfraControlState,
} from "@/components/Controls";
import { ResultPanel } from "@/components/ResultPanel";
import { Spinner, ErrorNote } from "@/components/ui";
import type { LayerResponse, ModuleId } from "@/lib/types";

export interface RightPanelProps {
  moduleId: Exclude<ModuleId, "copilot">;
  loading: boolean;
  error: string | null;
  layer: LayerResponse | null;
  // control state
  flood: FloodControlState;
  setFlood: (s: FloodControlState) => void;
  climate: ClimateControlState;
  setClimate: (s: ClimateControlState) => void;
  drought: DroughtControlState;
  setDrought: (s: DroughtControlState) => void;
  infra: InfraControlState;
  setInfra: (s: InfraControlState) => void;
  onRun: () => void;
}

export function RightPanel(props: RightPanelProps) {
  const {
    moduleId,
    loading,
    error,
    layer,
    flood,
    setFlood,
    climate,
    setClimate,
    drought,
    setDrought,
    infra,
    setInfra,
    onRun,
  } = props;
  const meta = moduleMeta(moduleId);

  return (
    <div className="flex h-full flex-col">
      {/* header */}
      <div className="flex items-center gap-3 border-b border-line px-4 py-3.5">
        <span
          className={`inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-space-850 ${meta.accent}`}
        >
          <meta.icon size={18} />
        </span>
        <div>
          <div className="text-sm font-semibold text-white">{meta.name}</div>
          <div className="text-[11px] text-slate-500">{meta.tagline}</div>
        </div>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto px-4 py-4">
        {/* controls */}
        <div>
          {moduleId === "flood" && (
            <FloodControls
              state={flood}
              setState={setFlood}
              loading={loading}
              onRun={onRun}
            />
          )}
          {moduleId === "climate" && (
            <ClimateControls
              state={climate}
              setState={setClimate}
              loading={loading}
              onRun={onRun}
            />
          )}
          {moduleId === "drought" && (
            <DroughtControls
              state={drought}
              setState={setDrought}
              loading={loading}
              onRun={onRun}
            />
          )}
          {moduleId === "infra" && (
            <InfraControls
              state={infra}
              setState={setInfra}
              loading={loading}
              onRun={onRun}
            />
          )}
        </div>

        {/* results */}
        <div className="border-t border-line pt-5">
          {error && <ErrorNote message={error} />}
          {!error && loading && !layer && <Spinner />}
          {!error && layer && (
            <motion.div
              key={`${layer.module}-${layer.product}-${layer.source}`}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <ResultPanel moduleId={moduleId} layer={layer} />
            </motion.div>
          )}
          {!error && !loading && !layer && (
            <p className="text-center text-xs text-slate-600">
              Configure the controls above and run an analysis to see results.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
