"use client";

export function Slider({
  label,
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.05,
  exact = false,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
  // When true, render the label verbatim (no auto-capitalization).
  exact?: boolean;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span
          className={`text-xs text-ink-muted ${exact ? "" : "capitalize"}`}
        >
          {label}
        </span>
        <span className="text-xs font-semibold tabular-nums text-ink">
          {value.toFixed(2)}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="ts-range w-full"
        style={{
          background: `linear-gradient(90deg, #06b6d4 ${pct}%, #e2e8f0 ${pct}%)`,
        }}
      />
    </div>
  );
}
