import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Light surface scale (white → very light slate).
        surface: {
          DEFAULT: "#ffffff",
          subtle: "#f8fafc", // slate-50
          muted: "#f1f5f9", // slate-100
          sunken: "#e2e8f0", // slate-200
        },
        line: {
          DEFAULT: "#e2e8f0", // slate-200 — primary border
          soft: "#cbd5e1", // slate-300 — stronger border
        },
        ink: {
          DEFAULT: "#0f172a", // slate-900 — primary text
          muted: "#475569", // slate-600 — secondary text
          subtle: "#64748b", // slate-500 — tertiary text
          faint: "#94a3b8", // slate-400 — placeholder
        },
        brand: {
          emerald: "#10b981",
          // slightly deeper cyan for AA contrast on white surfaces
          cyan: "#06b6d4",
          "cyan-light": "#22d3ee",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        // Soft, subtle elevation tuned for a white theme.
        xs: "0 1px 2px 0 rgba(15,23,42,0.05)",
        card: "0 1px 3px 0 rgba(15,23,42,0.06), 0 1px 2px -1px rgba(15,23,42,0.06)",
        panel:
          "0 4px 12px -2px rgba(15,23,42,0.08), 0 2px 6px -2px rgba(15,23,42,0.06)",
        float:
          "0 12px 32px -8px rgba(15,23,42,0.16), 0 4px 12px -4px rgba(15,23,42,0.08)",
        glow: "0 8px 24px -8px rgba(16,185,129,0.45)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
        "radial-glow":
          "radial-gradient(60% 55% at 50% 0%, rgba(6,182,212,0.10) 0%, rgba(16,185,129,0.06) 38%, transparent 72%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(16,185,129,0.45)" },
          "70%": { boxShadow: "0 0 0 6px rgba(16,185,129,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(16,185,129,0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.16,1,0.3,1) both",
        "pulse-ring": "pulse-ring 2s infinite",
      },
    },
  },
  plugins: [],
};

export default config;
