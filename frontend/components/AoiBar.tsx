"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { MapPin, Pencil, Check, X, ChevronDown, Search } from "lucide-react";
import {
  LOCATIONS,
  loadStatePresets,
  type LocationPreset,
  type StatePreset,
} from "@/lib/presets";

export function AoiBar({
  activeId,
  drawMode,
  bbox,
  activeStateName,
  onSelectLocation,
  onSelectState,
  onToggleDraw,
}: {
  activeId: string | null;
  drawMode: boolean;
  bbox: [number, number, number, number];
  activeStateName: string | null;
  onSelectLocation: (loc: LocationPreset) => void;
  onSelectState: (state: StatePreset) => void;
  onToggleDraw: () => void;
}) {
  const [states, setStates] = useState<StatePreset[]>([]);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const boxRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let alive = true;
    loadStatePresets()
      .then((s) => alive && setStates(s))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  // Close the dropdown on outside click.
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 30);
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return states;
    return states.filter((s) => s.name.toLowerCase().includes(q));
  }, [states, query]);

  function pickState(s: StatePreset) {
    onSelectState(s);
    setOpen(false);
    setQuery("");
  }

  return (
    <div className="pointer-events-none absolute inset-x-0 top-3 z-[1000] flex justify-center px-3">
      <div className="pointer-events-auto flex max-w-[calc(100%-1rem)] flex-col gap-2 rounded-2xl border border-line bg-space-900/85 p-2 shadow-panel backdrop-blur-xl sm:flex-row sm:items-center">
        <div className="flex items-center gap-1.5 px-1.5">
          <MapPin size={14} className="text-brand-cyan" />
          <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            AOI
          </span>
        </div>

        {/* searchable state selector */}
        <div ref={boxRef} className="relative">
          <button
            onClick={() => setOpen((o) => !o)}
            className={`chip min-w-[140px] justify-between ${
              activeStateName && !drawMode ? "chip-active" : ""
            }`}
            title="Choose any of India's 32 states/UTs"
          >
            <span className="truncate">
              {activeStateName ?? "All states…"}
            </span>
            <ChevronDown
              size={13}
              className={`shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
            />
          </button>

          {open && (
            <div className="absolute left-0 top-full z-[1100] mt-2 w-64 overflow-hidden rounded-xl border border-line bg-space-900/95 shadow-panel backdrop-blur-xl">
              <div className="flex items-center gap-2 border-b border-line px-3 py-2">
                <Search size={13} className="shrink-0 text-slate-500" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search states…"
                  className="w-full bg-transparent text-xs text-white placeholder:text-slate-600 focus:outline-none"
                />
                {query && (
                  <button
                    onClick={() => setQuery("")}
                    className="text-slate-500 hover:text-slate-300"
                  >
                    <X size={13} />
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto py-1">
                {filtered.length === 0 && (
                  <div className="px-3 py-3 text-center text-[11px] text-slate-600">
                    No matching state
                  </div>
                )}
                {filtered.map((s) => {
                  const isActive = activeStateName === s.name;
                  return (
                    <button
                      key={s.name}
                      onClick={() => pickState(s)}
                      className={`flex w-full items-center justify-between px-3 py-1.5 text-left text-xs transition-colors ${
                        isActive
                          ? "bg-brand-cyan/10 text-white"
                          : "text-slate-300 hover:bg-space-850 hover:text-white"
                      }`}
                    >
                      <span className="truncate">{s.name}</span>
                      {isActive && (
                        <Check size={12} className="shrink-0 text-brand-cyan" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <span className="hidden h-5 w-px bg-line sm:block" />

        <div className="flex flex-wrap items-center gap-1.5">
          {LOCATIONS.map((loc) => (
            <button
              key={loc.id}
              onClick={() => onSelectLocation(loc)}
              title={`${loc.name}, ${loc.region}`}
              className={`chip ${
                activeId === loc.id && !drawMode ? "chip-active" : ""
              }`}
            >
              {loc.name}
            </button>
          ))}

          <button
            onClick={onToggleDraw}
            className={`chip ${drawMode ? "chip-active" : ""}`}
            title="Click two corners on the map to draw a bounding box"
          >
            {drawMode ? <X size={12} /> : <Pencil size={12} />}
            {drawMode ? "Drawing…" : "Draw bbox"}
          </button>
        </div>
      </div>

      {drawMode && (
        <div className="pointer-events-none absolute top-full mt-2 flex items-center gap-1.5 rounded-full border border-brand-cyan/40 bg-space-900/90 px-3 py-1.5 text-[11px] text-brand-cyan shadow-panel backdrop-blur">
          <Check size={12} /> Click two opposite corners on the map
        </div>
      )}
    </div>
  );
}
