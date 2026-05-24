"use client";

import { DASHBOARD_MODULES } from "@/components/modules";
import type { ModuleId } from "@/lib/types";

/**
 * Module navigation.
 * - Desktop (lg+): a vertical icon rail on the left edge.
 * - Mobile / tablet (< lg): a fixed bottom navigation bar with icon + label.
 *
 * Both layouts are rendered from the same module list to stay in sync; only
 * one is visible at a given breakpoint.
 */
export function LeftRail({
  active,
  onSelect,
}: {
  active: ModuleId;
  onSelect: (id: ModuleId) => void;
}) {
  return (
    <>
      {/* Desktop / tablet vertical rail (md+) */}
      <nav className="z-20 hidden w-[84px] shrink-0 flex-col items-center gap-1.5 overflow-y-auto border-r border-line bg-white py-4 md:flex">
        {DASHBOARD_MODULES.map((m) => {
          const isActive = active === m.id;
          return (
            <button
              key={m.id}
              onClick={() => onSelect(m.id)}
              title={m.name}
              aria-pressed={isActive}
              className={`group relative flex w-[72px] flex-col items-center gap-1.5 rounded-xl px-2 py-3 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cyan/40 ${
                isActive
                  ? "bg-surface-muted text-ink"
                  : "text-ink-muted hover:bg-surface-subtle hover:text-ink"
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 h-7 w-[3px] -translate-y-1/2 rounded-r-full bg-brand-gradient" />
              )}
              <span
                className={`inline-flex h-9 w-9 items-center justify-center rounded-lg border transition-colors ${
                  isActive
                    ? "border-brand-cyan/40 bg-brand-cyan/10 " + m.accent
                    : "border-transparent group-hover:border-line"
                }`}
              >
                <m.icon size={18} />
              </span>
              <span className="text-[10px] font-medium leading-none">
                {m.short}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Mobile bottom navigation (< md) — horizontally scrollable for all modules.
          z-[1100] keeps it above Leaflet's map panes/controls (which reach ~z-1000). */}
      <nav className="pb-safe fixed inset-x-0 bottom-0 z-[1100] flex items-stretch overflow-x-auto border-t border-line bg-white px-1 shadow-[0_-4px_16px_-8px_rgba(15,23,42,0.18)] md:hidden">
        {DASHBOARD_MODULES.map((m) => {
          const isActive = active === m.id;
          return (
            <button
              key={m.id}
              onClick={() => onSelect(m.id)}
              aria-label={m.name}
              aria-pressed={isActive}
              className={`relative flex min-h-[58px] min-w-[66px] shrink-0 flex-1 flex-col items-center justify-center gap-1 px-1 py-2 text-[10px] font-semibold transition-colors ${
                isActive ? m.accent : "text-slate-600"
              }`}
            >
              {isActive && (
                <span className="absolute inset-x-3 top-0 h-[3px] rounded-b-full bg-brand-gradient" />
              )}
              <m.icon size={20} />
              <span className="leading-none">{m.short}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}
