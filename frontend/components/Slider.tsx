"use client";

export function Slider({
  label,
  value,
  onChange,
  min = 0,
  max = 1,
  step = 0.05,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs capitalize text-slate-400">{label}</span>
        <span className="text-xs font-medium tabular-nums text-slate-300">
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
          background: `linear-gradient(90deg, #22d3ee ${pct}%, #1e293b ${pct}%)`,
        }}
      />
    </div>
  );
}
