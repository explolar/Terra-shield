import React from "react";

export function LogoMark({
  size = 32,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="ts-grad" x1="0" y1="0" x2="48" y2="48">
          <stop stopColor="#10b981" />
          <stop offset="1" stopColor="#22d3ee" />
        </linearGradient>
      </defs>
      {/* shield */}
      <path
        d="M24 3 L41 9 V24 C41 34 33 41 24 45 C15 41 7 34 7 24 V9 Z"
        fill="url(#ts-grad)"
        fillOpacity="0.14"
        stroke="url(#ts-grad)"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {/* globe meridians */}
      <circle cx="24" cy="23" r="9.5" stroke="url(#ts-grad)" strokeWidth="1.7" />
      <ellipse
        cx="24"
        cy="23"
        rx="4"
        ry="9.5"
        stroke="url(#ts-grad)"
        strokeWidth="1.4"
      />
      <path
        d="M14.7 20.2 H33.3 M14.7 25.8 H33.3"
        stroke="url(#ts-grad)"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function Wordmark({ size = 32 }: { size?: number }) {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <LogoMark size={size} />
      <div className="leading-none">
        <span className="text-[17px] font-bold tracking-tight text-white">
          Terra
        </span>
        <span className="text-[17px] font-bold tracking-tight gradient-text">
          Shield
        </span>
        <span className="ml-1.5 align-top text-[10px] font-semibold uppercase tracking-[0.18em] text-brand-cyan/70">
          AI
        </span>
      </div>
    </div>
  );
}
