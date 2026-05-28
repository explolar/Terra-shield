"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { moduleMeta } from "@/components/modules";
import {
  ResilienceControls,
  DEFAULT_RESILIENCE,
  type ResilienceControlState,
} from "@/components/Controls";
import { ResilienceResultSwitch } from "@/components/ResilienceResult";
import { ErrorNote, ResultSkeleton, EmptyState } from "@/components/ui";
import { Network } from "lucide-react";
import {
  optimizeShelters,
  optimizeEvacuation,
  optimizeMitigation,
  getAhpDefault,
} from "@/lib/api";
import type {
  AOI,
  ShelterResponse,
  EvacuationResponse,
  MitigationResponse,
  AhpResponse,
  PointFeatureCollection,
  LineFeatureCollection,
} from "@/lib/types";

export function ResiliencePanel({
  aoi,
  onShelters,
  onRoute,
}: {
  aoi: AOI;
  onShelters: (fc: PointFeatureCollection | null) => void;
  onRoute: (fc: LineFeatureCollection | null) => void;
}) {
  const meta = moduleMeta("resilience");

  const [state, setState] = useState<ResilienceControlState>({
    ...DEFAULT_RESILIENCE,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [shelter, setShelter] = useState<ShelterResponse | null>(null);
  const [evacuation, setEvacuation] = useState<EvacuationResponse | null>(null);
  const [mitigation, setMitigation] = useState<MitigationResponse | null>(null);
  const [ahp, setAhp] = useState<AhpResponse | null>(null);

  // Auto-load the AHP defaults when that tool is selected.
  useEffect(() => {
    if (state.tool !== "ahp" || ahp) return;
    let alive = true;
    setLoading(true);
    setError(null);
    getAhpDefault()
      .then((r) => alive && setAhp(r))
      .catch(
        (e) =>
          alive &&
          setError(e?.detail || e?.message || "Failed to load AHP weights."),
      )
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [state.tool, ahp]);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      if (state.tool === "shelters") {
        const res = await optimizeShelters({
          aoi,
          num_shelters: state.num_shelters,
          radius_km: state.radius_km,
        });
        setShelter(res);
        onShelters(res.shelters_geojson ?? null);
      } else if (state.tool === "evacuation") {
        const res = await optimizeEvacuation({ aoi });
        setEvacuation(res);
        onRoute(res.route_geojson ?? null);
      } else if (state.tool === "mitigation") {
        const res = await optimizeMitigation({ budget: state.budget, aoi });
        setMitigation(res);
      } else if (state.tool === "ahp") {
        const res = await getAhpDefault();
        setAhp(res);
      }
    } catch (e: any) {
      setError(
        e?.detail || e?.message || "Optimization failed. Check the backend.",
      );
    } finally {
      setLoading(false);
    }
  }

  // Clear map overlays not relevant to the active tool.
  function setTool(next: ResilienceControlState) {
    if (next.tool !== state.tool) {
      setError(null);
      if (next.tool !== "shelters") onShelters(null);
      if (next.tool !== "evacuation") onRoute(null);
    }
    setState(next);
  }

  const hasResult =
    (state.tool === "shelters" && shelter) ||
    (state.tool === "evacuation" && evacuation) ||
    (state.tool === "mitigation" && mitigation) ||
    (state.tool === "ahp" && ahp);

  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* header */}
      <div className="flex items-center gap-3 border-b border-line px-4 py-3.5">
        <span
          className={`inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line bg-surface-subtle ${meta.accent}`}
        >
          <meta.icon size={18} />
        </span>
        <div>
          <div className="text-sm font-semibold text-ink">{meta.name}</div>
          <div className="text-[11px] text-ink-subtle">{meta.tagline}</div>
        </div>
      </div>

      <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-4 py-4">
        <div>
          <ResilienceControls
            state={state}
            setState={setTool}
            loading={loading}
            onRun={run}
          />
        </div>

        <div className="border-t border-line pt-5">
          {error && <ErrorNote message={error} />}
          {!error && loading && !hasResult && <ResultSkeleton />}
          {!error && hasResult && (
            <motion.div
              key={state.tool}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <ResilienceResultSwitch
                tool={state.tool}
                shelter={shelter}
                evacuation={evacuation}
                mitigation={mitigation}
                ahp={ahp}
              />
            </motion.div>
          )}
          {!error && !loading && !hasResult && (
            <EmptyState
              icon={Network}
              title="No optimization yet"
              message="Pick an optimization model and run it to see results."
            />
          )}
        </div>
      </div>
    </div>
  );
}
