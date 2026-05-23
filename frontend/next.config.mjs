/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit a self-contained server bundle for a small production Docker image.
  output: "standalone",
  eslint: {
    // Builds should not be blocked by lint warnings during demos.
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
