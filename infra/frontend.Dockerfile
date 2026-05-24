# TerraShield AI — Next.js frontend image (standalone output)
FROM node:20-slim AS deps
WORKDIR /app
COPY frontend/package*.json ./
# npm install (not ci) so the Linux build resolves platform-specific optional deps
# (e.g. @emnapi/*) that a Windows-generated lockfile omits — ci would hard-fail on them.
RUN npm install --no-audit --no-fund

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./
# NEXT_PUBLIC_* are inlined at build time — pass the backend URL as a build arg:
#   --build-arg NEXT_PUBLIC_API_BASE=https://backend-url/api/v1
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
# Works with `output: 'standalone'` in next.config.mjs; falls back to full copy.
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
