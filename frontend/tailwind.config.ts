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
        space: {
          950: "#070b18",
          900: "#0b1120",
          850: "#0d1526",
          800: "#0f172a",
        },
        line: {
          DEFAULT: "#1e293b",
          soft: "#1b2638",
        },
        brand: {
          emerald: "#10b981",
          cyan: "#22d3ee",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(34,211,238,0.18), 0 12px 40px -12px rgba(16,185,129,0.45)",
        panel: "0 8px 30px -12px rgba(0,0,0,0.6)",
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 12px 30px -16px rgba(0,0,0,0.7)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #10b981 0%, #22d3ee 100%)",
        "radial-glow":
          "radial-gradient(60% 60% at 50% 0%, rgba(34,211,238,0.10) 0%, rgba(16,185,129,0.05) 35%, transparent 70%)",
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
          "0%": { boxShadow: "0 0 0 0 rgba(16,185,129,0.5)" },
          "70%": { boxShadow: "0 0 0 8px rgba(16,185,129,0)" },
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
