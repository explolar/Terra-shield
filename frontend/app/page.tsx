"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Satellite,
  Cpu,
  Map as MapIcon,
  ShieldCheck,
  Sparkles,
  Github,
} from "lucide-react";
import { LogoMark, Wordmark } from "@/components/Logo";
import { MODULES } from "@/components/modules";

const fadeUp = {
  hidden: { opacity: 0, y: 22 },
  show: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, delay: i * 0.07, ease: [0.16, 1, 0.3, 1] },
  }),
};

const PIPELINE = [
  {
    icon: MapIcon,
    title: "Define an AOI",
    body: "Pick a city or draw a bounding box anywhere on Earth.",
  },
  {
    icon: Satellite,
    title: "Fuse Earth observation",
    body: "SRTM, Sentinel, CHIRPS, MODIS, WorldCover & WorldPop, unified.",
  },
  {
    icon: Cpu,
    title: "Run physical + AI models",
    body: "Flood, climate, drought, groundwater and exposure engines compute in seconds.",
  },
  {
    icon: ShieldCheck,
    title: "Decide with confidence",
    body: "Reliability-scored layers your team can act on.",
  },
];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-x-hidden bg-surface-subtle">
      {/* ambient background */}
      <div className="pointer-events-none absolute inset-0 bg-radial-glow" />
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[420px] w-[680px] -translate-x-1/2 rounded-full bg-brand-emerald/10 blur-[140px]" />
      <div className="pointer-events-none absolute top-1/3 right-0 h-[360px] w-[360px] rounded-full bg-brand-cyan/10 blur-[130px]" />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.5]"
        style={{
          backgroundImage:
            "linear-gradient(#e2e8f0 1px, transparent 1px), linear-gradient(90deg, #e2e8f0 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage:
            "radial-gradient(ellipse 80% 55% at 50% 0%, black, transparent)",
          WebkitMaskImage:
            "radial-gradient(ellipse 80% 55% at 50% 0%, black, transparent)",
        }}
      />

      {/* nav */}
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-4 sm:px-6 sm:py-5">
        <Wordmark />
        <nav className="hidden items-center gap-7 text-sm text-ink-muted md:flex">
          <a href="#modules" className="transition hover:text-ink">
            Modules
          </a>
          <a href="#how" className="transition hover:text-ink">
            How it works
          </a>
          <a href="#architecture" className="transition hover:text-ink">
            Architecture
          </a>
        </nav>
        <Link href="/app" className="btn-primary px-4 sm:px-5">
          <span className="hidden sm:inline">Launch Platform</span>
          <span className="sm:hidden">Launch</span>
          <ArrowRight size={16} />
        </Link>
      </header>

      {/* hero */}
      <section className="relative z-10 mx-auto max-w-5xl px-4 pb-16 pt-12 text-center sm:px-6 sm:pt-20 lg:pt-24">
        <motion.div
          initial="hidden"
          animate="show"
          variants={fadeUp}
          className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-white/80 px-4 py-1.5 text-xs font-medium text-ink-muted shadow-xs backdrop-blur"
        >
          <Sparkles size={13} className="text-brand-cyan" />
          <span className="hidden sm:inline">
            Earth observation, climate models &amp; AI — in one workspace
          </span>
          <span className="sm:hidden">EO · climate · AI, unified</span>
        </motion.div>

        <motion.h1
          initial="hidden"
          animate="show"
          custom={1}
          variants={fadeUp}
          className="text-balance text-3xl font-bold leading-[1.08] tracking-tight text-ink sm:text-5xl lg:text-6xl"
        >
          The AI Operating System for
          <br className="hidden sm:block" />{" "}
          <span className="gradient-text">Climate Risk &amp; Resilience</span>
        </motion.h1>

        <motion.p
          initial="hidden"
          animate="show"
          custom={2}
          variants={fadeUp}
          className="mx-auto mt-5 max-w-2xl text-pretty text-sm leading-relaxed text-ink-muted sm:mt-6 sm:text-base lg:text-lg"
        >
          TerraShield turns petabytes of satellite and climate data into
          decision-ready intelligence — flood, drought, climate and
          infrastructure risk for any place on the planet, in seconds.
        </motion.p>

        <motion.div
          initial="hidden"
          animate="show"
          custom={3}
          variants={fadeUp}
          className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link
            href="/app"
            className="btn-primary w-full px-6 py-3 text-base sm:w-auto"
          >
            Launch Platform
            <ArrowRight size={18} />
          </Link>
          <a
            href="#modules"
            className="btn-ghost w-full px-6 py-3 text-base sm:w-auto"
          >
            Explore modules
          </a>
        </motion.div>

        {/* hero stat strip */}
        <motion.div
          initial="hidden"
          animate="show"
          custom={4}
          variants={fadeUp}
          className="mx-auto mt-12 grid max-w-3xl grid-cols-2 gap-3 sm:mt-16 sm:grid-cols-4 sm:gap-4"
        >
          {[
            ["7", "Risk modules"],
            ["12+", "EO datasets"],
            ["SSP5-8.5", "Climate horizons"],
            ["< 5s", "Per analysis"],
          ].map(([n, l]) => (
            <div key={l} className="panel p-4">
              <div className="gradient-text text-xl font-bold sm:text-2xl">
                {n}
              </div>
              <div className="mt-1 text-xs text-ink-subtle">{l}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* modules */}
      <section
        id="modules"
        className="relative z-10 mx-auto max-w-7xl px-4 py-14 sm:px-6 sm:py-16"
      >
        <SectionHeader
          eyebrow="Platform"
          title="Nine engines, one workspace"
          subtitle="Each module is a production-grade model that runs over your area and returns clear, mappable results."
        />
        <div className="mt-10 grid gap-4 sm:mt-12 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3">
          {MODULES.map((m, i) => (
            <motion.div
              key={m.id}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-60px" }}
              custom={i}
              variants={fadeUp}
              className="group relative overflow-hidden rounded-2xl border border-line bg-white p-5 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-brand-cyan/40 hover:shadow-panel sm:p-6"
            >
              <div
                className={`pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-gradient-to-br ${m.gradient} opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100`}
              />
              <div className="relative">
                <div
                  className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl border border-line bg-surface-subtle ${m.accent} transition-transform duration-300 group-hover:scale-110`}
                >
                  <m.icon size={22} />
                </div>
                <h3 className="text-lg font-semibold text-ink">{m.name}</h3>
                <p className="mt-0.5 text-xs font-medium uppercase tracking-wide text-brand-cyan">
                  {m.tagline}
                </p>
                <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                  {m.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* how it works */}
      <section
        id="how"
        className="relative z-10 mx-auto max-w-7xl px-4 py-14 sm:px-6 sm:py-16"
      >
        <SectionHeader
          eyebrow="How it works"
          title="From raw pixels to resilience decisions"
          subtitle="A single pipeline takes any area of interest from satellite data to an actionable, mappable answer."
        />
        <div className="mt-10 grid gap-4 sm:mt-12 sm:grid-cols-2 sm:gap-5 lg:grid-cols-4">
          {PIPELINE.map((step, i) => (
            <motion.div
              key={step.title}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-60px" }}
              custom={i}
              variants={fadeUp}
              className="panel relative p-5 sm:p-6"
            >
              <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-gradient text-white">
                <step.icon size={18} />
              </div>
              <div className="absolute right-5 top-5 text-xs font-bold text-slate-300">
                0{i + 1}
              </div>
              <h4 className="text-sm font-semibold text-ink">{step.title}</h4>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">
                {step.body}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* architecture strip */}
      <section
        id="architecture"
        className="relative z-10 mx-auto max-w-7xl px-4 py-14 sm:px-6 sm:py-16"
      >
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          variants={fadeUp}
          className="overflow-hidden rounded-3xl border border-line bg-white p-6 shadow-panel sm:p-10 lg:p-12"
        >
          <div className="grid items-center gap-8 lg:grid-cols-2 lg:gap-10">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-cyan">
                Architecture
              </p>
              <h3 className="mt-3 text-2xl font-bold text-ink sm:text-3xl">
                Built for production, not just a demo
              </h3>
              <p className="mt-4 text-sm leading-relaxed text-ink-muted">
                A typed Next.js frontend talks to a FastAPI backend powered by
                Google Earth Engine. Every layer is tagged live or demo and
                falls back gracefully — so the platform is always trustworthy.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                {[
                  "Next.js 14",
                  "FastAPI",
                  "Earth Engine",
                  "Leaflet",
                  "CMIP6",
                  "Sentinel-1",
                ].map((t) => (
                  <span
                    key={t}
                    className="rounded-full border border-line bg-surface-subtle px-3 py-1 text-xs text-ink-muted"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-3">
              {[
                ["Frontend", "Next.js · Leaflet · Recharts", "border-brand-cyan/40"],
                ["API", "FastAPI · typed schemas · rate-limited", "border-brand-emerald/40"],
                ["Geo-engine", "Earth Engine · deterministic demo fallback", "border-violet-400/50"],
                ["Data", "SRTM · Sentinel · CHIRPS · CMIP6 · WorldPop", "border-amber-400/50"],
              ].map(([layer, desc, border]) => (
                <div
                  key={layer}
                  className={`flex items-center justify-between gap-3 rounded-xl border ${border} bg-surface-subtle px-4 py-3.5 sm:px-5`}
                >
                  <span className="text-sm font-semibold text-ink">{layer}</span>
                  <span className="text-right text-xs text-ink-muted">
                    {desc}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>

      {/* CTA */}
      <section className="relative z-10 mx-auto max-w-4xl px-4 py-16 text-center sm:px-6 sm:py-20">
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true }}
          variants={fadeUp}
        >
          <LogoMark size={48} className="mx-auto mb-6" />
          <h2 className="text-2xl font-bold tracking-tight text-ink sm:text-4xl">
            See your region&apos;s climate risk now
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-sm text-ink-muted sm:text-base">
            No setup required. Launch the platform and run a flood, drought or
            climate analysis over any city in seconds.
          </p>
          <Link
            href="/app"
            className="btn-primary mx-auto mt-8 w-full max-w-xs px-7 py-3 text-base sm:w-auto"
          >
            Launch Platform
            <ArrowRight size={18} />
          </Link>
        </motion.div>
      </section>

      {/* footer */}
      <footer className="relative z-10 border-t border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-ink-subtle sm:flex-row sm:px-6">
          <div className="flex items-center gap-2.5 text-center sm:text-left">
            <LogoMark size={22} />
            <span>
              © {new Date().getFullYear()} TerraShield AI — Climate intelligence
              for everyone.
            </span>
          </div>
          <div className="flex items-center gap-5">
            <a href="#modules" className="transition hover:text-ink">
              Modules
            </a>
            <a href="#architecture" className="transition hover:text-ink">
              Architecture
            </a>
            <a
              href="https://github.com"
              className="inline-flex items-center gap-1.5 transition hover:text-ink"
            >
              <Github size={15} /> Source
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}

function SectionHeader({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
}) {
  return (
    <motion.div
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-60px" }}
      variants={fadeUp}
      className="mx-auto max-w-2xl text-center"
    >
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-cyan">
        {eyebrow}
      </p>
      <h2 className="mt-3 text-2xl font-bold tracking-tight text-ink sm:text-4xl">
        {title}
      </h2>
      <p className="mt-4 text-sm leading-relaxed text-ink-muted sm:text-base">
        {subtitle}
      </p>
    </motion.div>
  );
}
