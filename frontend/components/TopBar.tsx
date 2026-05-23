"use client";

import Link from "next/link";
import { ArrowLeft, Globe2, Loader2 } from "lucide-react";
import { Wordmark } from "@/components/Logo";
import type { EarthdataStatus } from "@/lib/types";

export function TopBar({
  status,
  statusLoading,
}: {
  status: EarthdataStatus | null;
  statusLoading: boolean;
}) {
  return (
    <header className="z-30 flex h-14 shrink-0 items-center justify-between gap-2 border-b border-line bg-white/90 px-3 backdrop-blur-xl sm:px-4">
      <div className="flex min-w-0 items-center gap-4">
        <Link href="/" aria-label="TerraShield home">
          <Wordmark size={26} />
        </Link>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <EngineBadge status={status} loading={statusLoading} />
        <Link
          href="/"
          className="inline-flex min-h-[36px] items-center gap-1.5 rounded-lg border border-line bg-white px-3 py-1.5 text-xs text-ink-muted shadow-xs transition hover:border-brand-cyan/50 hover:text-ink"
        >
          <ArrowLeft size={13} /> <span className="hidden sm:inline">Home</span>
        </Link>
      </div>
    </header>
  );
}

function EngineBadge({
  status,
  loading,
}: {
  status: EarthdataStatus | null;
  loading: boolean;
}) {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface-subtle px-3 py-1.5 text-xs text-ink-muted">
        <Loader2 size={12} className="animate-spin" />
        <span className="hidden sm:inline">EarthData Engine</span>
      </span>
    );
  }

  const offline = !status;
  const live = status?.mode === "live";
  const color = offline
    ? "border-rose-300 bg-rose-50 text-rose-700"
    : live
      ? "border-emerald-300 bg-emerald-50 text-emerald-700"
      : "border-amber-300 bg-amber-50 text-amber-700";
  const dot = offline ? "bg-rose-500" : live ? "bg-emerald-500" : "bg-amber-500";
  const label = offline
    ? "Backend offline"
    : live
      ? "EarthData · Live"
      : "EarthData · Demo";
  const shortLabel = offline ? "Offline" : live ? "Live" : "Demo";

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1.5 text-xs font-medium sm:px-3 ${color}`}
      title={
        offline
          ? "Cannot reach the backend API."
          : status?.error || `Mode: ${status?.mode}`
      }
    >
      <Globe2 size={12} className="hidden sm:inline" />
      <span
        className={`h-1.5 w-1.5 rounded-full ${dot} ${
          !offline && live ? "animate-pulse-ring" : ""
        }`}
      />
      <span className="hidden sm:inline">{label}</span>
      <span className="sm:hidden">{shortLabel}</span>
    </span>
  );
}
