"use client";

import {
  ShieldCheck,
  Route,
  AlertTriangle,
  Building2,
  Sigma,
  Wallet,
  Network,
} from "lucide-react";
import { SectionLabel } from "@/components/ui";
import type {
  ShelterResponse,
  EvacuationResponse,
  MitigationResponse,
  AhpResponse,
} from "@/lib/types";
import type { ResilienceTool } from "@/components/Controls";

function MethodCaption({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex items-start gap-1.5 border-t border-line pt-3 text-[11px] leading-relaxed text-slate-600">
      <Sigma size={12} className="mt-0.5 shrink-0" />
      <span className="italic">{children}</span>
    </p>
  );
}

// A two-tone bar: covered (cyan) vs uncovered (slate).
function CoverageBar({ covered }: { covered: number }) {
  const c = Math.max(0, Math.min(100, covered));
  return (
    <div className="flex h-3 w-full overflow-hidden rounded-full ring-1 ring-white/10">
      <div
        className="h-full bg-brand-gradient transition-all duration-500"
        style={{ width: `${c}%` }}
      />
      <div
        className="h-full bg-space-850 transition-all duration-500"
        style={{ width: `${100 - c}%` }}
      />
    </div>
  );
}

function UsageBar({ pct, color = "#10b981" }: { pct: number; color?: string }) {
  const c = Math.max(0, Math.min(100, pct));
  return (
    <div className="h-2.5 w-full overflow-hidden rounded-full bg-space-850 ring-1 ring-white/5">
      <div
        className="h-full rounded-full transition-all duration-500"
        style={{ width: `${c}%`, backgroundColor: color }}
      />
    </div>
  );
}

function ResultHeader({
  icon: Icon,
  title,
}: {
  icon: typeof Network;
  title: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-line bg-space-850 text-cyan-200">
        <Icon size={14} />
      </span>
      <span className="text-sm font-semibold text-white">{title}</span>
    </div>
  );
}

export function ShelterResult({ data }: { data: ShelterResponse }) {
  return (
    <div className="space-y-5">
      <ResultHeader icon={Building2} title="Shelter siting" />

      <div className="rounded-xl border border-line bg-space-850 p-4">
        <div className="text-xs text-slate-500">Demand covered</div>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="gradient-text text-3xl font-bold">
            {data.coverage_pct}%
          </span>
          <span className="ml-auto text-xs text-slate-500">
            {data.uncovered_pct}% uncovered
          </span>
        </div>
        <div className="mt-2.5">
          <CoverageBar covered={data.coverage_pct} />
        </div>
        <div className="mt-1.5 flex justify-between text-[10px] text-slate-600">
          <span className="text-cyan-300">Covered</span>
          <span>Uncovered</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2.5">
        <div className="stat-card">
          <div className="text-[11px] text-slate-500">Shelters</div>
          <div className="mt-1 text-base font-semibold text-white">
            {data.chosen.length}
          </div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-slate-500">Candidates</div>
          <div className="mt-1 text-base font-semibold text-white">
            {data.candidate_sites}
          </div>
        </div>
        <div className="stat-card">
          <div className="text-[11px] text-slate-500">Radius</div>
          <div className="mt-1 text-base font-semibold text-white">
            {data.radius_km} km
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/[0.05] p-3 text-[11px] text-slate-400">
        Serving <b className="text-white">{data.demand_points}</b> demand points
        with <b className="text-white">{data.chosen.length}</b> sited shelters
        (shown as cyan markers on the map).
      </div>

      <MethodCaption>
        Maximal Covering Location (greedy ≥ 63% of optimal).
      </MethodCaption>
    </div>
  );
}

export function EvacuationResult({ data }: { data: EvacuationResponse }) {
  return (
    <div className="space-y-5">
      <ResultHeader icon={Route} title="Evacuation route" />

      {!data.reachable ? (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3.5 text-sm text-rose-200">
          No safe route found — the destination is unreachable across the current
          network.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-2.5">
            <div className="rounded-xl border border-line bg-space-850 p-4">
              <div className="text-xs text-slate-500">Route length</div>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="gradient-text text-2xl font-bold">
                  {data.route_km}
                </span>
                <span className="text-sm text-slate-400">km</span>
              </div>
            </div>
            <div className="rounded-xl border border-line bg-space-850 p-4">
              <div className="text-xs text-slate-500">Segments</div>
              <div className="mt-1 text-2xl font-bold text-white">
                {data.segments}
              </div>
            </div>
          </div>

          {data.crosses_flood ? (
            <div className="flex items-center gap-2 rounded-xl border border-amber-500/40 bg-amber-500/10 px-3.5 py-2.5 text-xs text-amber-200">
              <AlertTriangle size={15} className="shrink-0" />
              Route crosses flood-prone terrain — verify passability before use.
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/[0.06] px-3.5 py-2.5 text-xs text-emerald-200">
              <ShieldCheck size={15} className="shrink-0" />
              Route avoids known flood-prone terrain.
            </div>
          )}

          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.05] p-3 text-[11px] text-slate-400">
            The corridor is drawn as a dashed emerald line on the map.
          </div>
        </>
      )}

      <MethodCaption>Dijkstra shortest path.</MethodCaption>
    </div>
  );
}

export function MitigationResult({ data }: { data: MitigationResponse }) {
  return (
    <div className="space-y-5">
      <ResultHeader icon={Wallet} title="Mitigation plan" />

      <div className="rounded-xl border border-line bg-space-850 p-4">
        <div className="text-xs text-slate-500">Total risk reduction</div>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="gradient-text text-3xl font-bold">
            {data.total_risk_reduction}
          </span>
        </div>
      </div>

      <div>
        <div className="mb-1.5 flex items-center justify-between text-xs">
          <span className="text-slate-500">Budget used</span>
          <span className="font-semibold tabular-nums text-white">
            {data.total_cost} / {data.budget} ({data.budget_used_pct}%)
          </span>
        </div>
        <UsageBar pct={data.budget_used_pct} />
      </div>

      <div>
        <SectionLabel>Selected interventions</SectionLabel>
        {data.selected.length === 0 ? (
          <p className="text-xs text-slate-600">
            No interventions fit within the budget.
          </p>
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {data.selected.map((id) => (
              <span
                key={String(id)}
                className="inline-flex items-center gap-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-1 text-[11px] font-medium text-cyan-200"
              >
                {String(id)}
              </span>
            ))}
          </div>
        )}
      </div>

      <MethodCaption>0/1 knapsack (Bellman DP).</MethodCaption>
    </div>
  );
}

function ahpLabel(
  labels: AhpResponse["labels"],
  key: string,
): string {
  if (Array.isArray(labels)) return key.replace(/_/g, " ");
  return labels[key] ?? key.replace(/_/g, " ");
}

export function AhpResult({ data }: { data: AhpResponse }) {
  const entries = Object.entries(data.weights).sort((a, b) => b[1] - a[1]);
  const maxW = Math.max(...entries.map(([, w]) => w), 0.0001);

  return (
    <div className="space-y-5">
      <ResultHeader icon={ShieldCheck} title="Defensible weights (AHP)" />

      <div className="rounded-xl border border-line bg-space-850 p-4">
        <div className="space-y-2.5">
          {entries.map(([factor, w]) => (
            <div key={factor}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="capitalize text-slate-300">
                  {ahpLabel(data.labels, factor)}
                </span>
                <span className="font-semibold tabular-nums text-white">
                  {w.toFixed(3)}
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-space-900 ring-1 ring-white/5">
                <div
                  className="h-full rounded-full bg-brand-gradient transition-all duration-500"
                  style={{ width: `${(w / maxW) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between rounded-xl border border-emerald-500/25 bg-emerald-500/[0.06] px-3.5 py-2.5">
        <span className="text-xs text-slate-400">Consistency</span>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${
            data.consistent
              ? "border border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
              : "border border-amber-500/40 bg-amber-500/10 text-amber-300"
          }`}
        >
          CR = {data.consistency_ratio.toFixed(3)}{" "}
          {data.consistent ? "✓ consistent" : "⚠ review"}
        </span>
      </div>

      <MethodCaption>Analytic Hierarchy Process (Saaty, 1980).</MethodCaption>
    </div>
  );
}

export function ResilienceResultSwitch({
  tool,
  shelter,
  evacuation,
  mitigation,
  ahp,
}: {
  tool: ResilienceTool;
  shelter: ShelterResponse | null;
  evacuation: EvacuationResponse | null;
  mitigation: MitigationResponse | null;
  ahp: AhpResponse | null;
}) {
  if (tool === "shelters" && shelter) return <ShelterResult data={shelter} />;
  if (tool === "evacuation" && evacuation)
    return <EvacuationResult data={evacuation} />;
  if (tool === "mitigation" && mitigation)
    return <MitigationResult data={mitigation} />;
  if (tool === "ahp" && ahp) return <AhpResult data={ahp} />;
  return null;
}
