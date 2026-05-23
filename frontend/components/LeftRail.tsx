"use client";

import { DASHBOARD_MODULES } from "@/components/modules";
import type { ModuleId } from "@/lib/types";

export function LeftRail({
  active,
  onSelect,
}: {
  active: ModuleId;
  onSelect: (id: ModuleId) => void;
}) {
  return (
    <nav className="z-20 flex w-[88px] shrink-0 flex-col items-center gap-1.5 border-r border-line bg-space-900/90 py-4 backdrop-blur-xl">
      {DASHBOARD_MODULES.map((m) => {
        const isActive = active === m.id;
        return (
          <button
            key={m.id}
            onClick={() => onSelect(m.id)}
            title={m.name}
            className={`group relative flex w-[72px] flex-col items-center gap-1.5 rounded-xl px-2 py-3 transition-all duration-200 ${
              isActive
                ? "bg-space-800 text-white"
                : "text-slate-500 hover:bg-space-850 hover:text-slate-200"
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
  );
}
