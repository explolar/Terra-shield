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
  onSelectCity,
  onToggleDraw,
}: {
  activeId: string | null;
  drawMode: boolean;
  bbox: [number, number, number, number];
  activeStateName: string | null;
  onSelectLocation: (loc: LocationPreset) => void;
  onSelectState: (state: StatePreset) => void;
  onSelectCity: (name: string, bbox: [number, number, number, number]) => void;
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
      <div className="pointer-events-auto flex w-full max-w-[calc(100%-0.5rem)] flex-col gap-2 rounded-2xl border border-line bg-white/90 p-2 shadow-panel backdrop-blur-xl sm:w-auto sm:flex-row sm:flex-wrap sm:items-center">
        <div className="flex items-center gap-1.5 px-1.5">
          <MapPin size={14} className="text-brand-cyan" />
          <span className="text-[11px] font-semibold uppercase tracking-wide text-ink-subtle">
            AOI
          </span>
        </div>

        {/* searchable state selector */}
        <div ref={boxRef} className="relative">
          <button
            onClick={() => setOpen((o) => !o)}
            className={`chip w-full min-w-[140px] justify-between sm:w-auto ${
              activeStateName && !drawMode ? "chip-active" : ""
            }`}
            title="Choose any of India's 32 states/UTs"
          >
            <span className="truncate">{activeStateName ?? "All states…"}</span>
            <ChevronDown
              size={13}
              className={`shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
            />
          </button>

          {open && (
            <div className="absolute left-0 top-full z-[1100] mt-2 w-[min(16rem,calc(100vw-3rem))] overflow-hidden rounded-xl border border-line bg-white shadow-float">
              <div className="flex items-center gap-2 border-b border-line px-3 py-2">
                <Search size={13} className="shrink-0 text-ink-faint" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search states…"
                  className="w-full bg-transparent text-xs text-ink placeholder:text-ink-faint focus:outline-none"
                />
                {query && (
                  <button
                    onClick={() => setQuery("")}
                    className="text-ink-faint hover:text-ink-muted"
                    aria-label="Clear search"
                  >
                    <X size={13} />
                  </button>
                )}
              </div>
              <div className="max-h-[min(16rem,40vh)] overflow-y-auto py-1">
                {filtered.length === 0 && (
                  <div className="px-3 py-3 text-center text-[11px] text-ink-faint">
                    No matching state
                  </div>
                )}
                {filtered.map((s) => {
                  const isActive = activeStateName === s.name;
                  return (
                    <button
                      key={s.name}
                      onClick={() => pickState(s)}
                      className={`flex w-full items-center justify-between px-3 py-2 text-left text-xs transition-colors ${
                        isActive
                          ? "bg-brand-cyan/10 text-cyan-700"
                          : "text-ink-muted hover:bg-surface-subtle hover:text-ink"
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

        {/* free-text city search (Open-Meteo geocoding, keyless) */}
        <CitySearch onSelectCity={onSelectCity} />

        <span className="hidden h-5 w-px bg-line sm:block" />

        {/* preset cities — horizontally scrollable on mobile to avoid overflow */}
        <div className="-mx-1 flex items-center gap-1.5 overflow-x-auto px-1 pb-0.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 sm:pb-0">
          {LOCATIONS.map((loc) => (
            <button
              key={loc.id}
              onClick={() => onSelectLocation(loc)}
              title={`${loc.name}, ${loc.region}`}
              className={`chip shrink-0 ${
                activeId === loc.id && !drawMode ? "chip-active" : ""
              }`}
            >
              {loc.name}
            </button>
          ))}

          <button
            onClick={onToggleDraw}
            className={`chip shrink-0 ${drawMode ? "chip-active" : ""}`}
            title="Click two corners on the map to draw a bounding box"
          >
            {drawMode ? <X size={12} /> : <Pencil size={12} />}
            {drawMode ? "Drawing…" : "Draw bbox"}
          </button>
        </div>
      </div>

      {drawMode && (
        <div className="pointer-events-none absolute top-full mt-2 flex items-center gap-1.5 rounded-full border border-brand-cyan/50 bg-white/95 px-3 py-1.5 text-[11px] font-medium text-cyan-700 shadow-panel backdrop-blur">
          <Check size={12} /> Click two opposite corners on the map
        </div>
      )}
    </div>
  );
}

// ~0.4° box around the geocoded point — matches the scale of the city presets.
const CITY_HALF = 0.2;

interface GeoResult {
  name: string;
  latitude: number;
  longitude: number;
  country?: string;
  admin1?: string;
}

// Free-text city search via Open-Meteo's keyless, CORS-enabled geocoding API.
function CitySearch({
  onSelectCity,
}: {
  onSelectCity: (name: string, bbox: [number, number, number, number]) => void;
}) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<GeoResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  // Debounced lookup as the user types (min 2 chars).
  useEffect(() => {
    const term = q.trim();
    if (term.length < 2) {
      setResults([]);
      return;
    }
    let alive = true;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const r = await fetch(
          `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
            term,
          )}&count=6&language=en&format=json`,
        );
        const data = await r.json();
        if (alive) {
          setResults(data.results ?? []);
          setOpen(true);
        }
      } catch {
        if (alive) setResults([]);
      } finally {
        if (alive) setLoading(false);
      }
    }, 300);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [q]);

  function pick(r: GeoResult) {
    const b: [number, number, number, number] = [
      r.longitude - CITY_HALF,
      r.latitude - CITY_HALF,
      r.longitude + CITY_HALF,
      r.latitude + CITY_HALF,
    ];
    onSelectCity(r.admin1 ? `${r.name}, ${r.admin1}` : r.name, b);
    setOpen(false);
    setQ("");
  }

  return (
    <div ref={ref} className="relative">
      <div className="chip flex min-w-[150px] items-center gap-1.5">
        <Search size={13} className="shrink-0 text-ink-faint" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder="Search any city…"
          className="w-full bg-transparent text-xs text-ink placeholder:text-ink-faint focus:outline-none"
        />
        {q && (
          <button
            onClick={() => {
              setQ("");
              setResults([]);
            }}
            className="text-ink-faint hover:text-ink-muted"
            aria-label="Clear city search"
          >
            <X size={13} />
          </button>
        )}
      </div>

      {open && q.trim().length >= 2 && (
        <div className="absolute left-0 top-full z-[1100] mt-2 w-[min(18rem,calc(100vw-3rem))] overflow-hidden rounded-xl border border-line bg-white shadow-float">
          <div className="max-h-[min(16rem,40vh)] overflow-y-auto py-1">
            {loading && (
              <div className="px-3 py-3 text-center text-[11px] text-ink-faint">
                Searching…
              </div>
            )}
            {!loading && results.length === 0 && (
              <div className="px-3 py-3 text-center text-[11px] text-ink-faint">
                No city found
              </div>
            )}
            {results.map((r, i) => (
              <button
                key={`${r.name}-${i}`}
                onClick={() => pick(r)}
                className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-xs text-ink-muted transition-colors hover:bg-surface-subtle hover:text-ink"
              >
                <span className="truncate">{r.name}</span>
                <span className="shrink-0 text-[10px] text-ink-faint">
                  {[r.admin1, r.country].filter(Boolean).join(", ")}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
