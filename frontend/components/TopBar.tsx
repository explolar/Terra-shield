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
    <header className="z-30 flex h-14 shrink-0 items-center justify-between border-b border-line bg-space-900/90 px-4 backdrop-blur-xl">
      <div className="flex items-center gap-4">
        <Link href="/">
          <Wordmark size={26} />
        </Link>
      </div>

      <div className="flex items-center gap-3">
        <EngineBadge status={status} loading={statusLoading} />
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-xs text-slate-400 transition hover:border-brand-cyan/40 hover:text-white"
        >
          <ArrowLeft size={13} /> Home
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
      <span className="inline-flex items-center gap-2 rounded-full border border-line bg-space-850 px-3 py-1.5 text-xs text-slate-400">
        <Loader2 size={12} className="animate-spin" />
        EarthData Engine
      </span>
    );
  }

  const offline = !status;
  const live = status?.mode === "live";
  const color = offline
    ? "border-rose-500/40 bg-rose-500/10 text-rose-300"
    : live
      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
      : "border-amber-500/40 bg-amber-500/10 text-amber-300";
  const dot = offline ? "bg-rose-400" : live ? "bg-emerald-400" : "bg-amber-400";
  const label = offline
    ? "Backend offline"
    : live
      ? "EarthData · Live"
      : "EarthData · Demo";

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${color}`}
      title={
        offline
          ? "Cannot reach the backend API."
          : status?.error || `Mode: ${status?.mode}`
      }
    >
      <Globe2 size={12} />
      <span className={`h-1.5 w-1.5 rounded-full ${dot} ${!offline && live ? "animate-pulse-ring" : ""}`} />
      {label}
    </span>
  );
}
