import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "TerraShield AI — Climate Risk & Resilience",
  description:
    "The AI Operating System for Climate Risk & Resilience. Flood, climate, drought and infrastructure intelligence over any area of interest.",
  keywords: [
    "climate risk",
    "flood modelling",
    "geospatial AI",
    "earth observation",
    "resilience",
  ],
};

export const viewport: Viewport = {
  themeColor: "#ffffff",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-surface-subtle text-ink antialiased">
        {children}
      </body>
    </html>
  );
}
