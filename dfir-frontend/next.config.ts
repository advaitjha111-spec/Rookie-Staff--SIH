import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the frontend to sit alongside a separate backend workspace.
  outputFileTracingRoot: process.cwd(),
  // Vercel's CI uses different ESLint versions — skip lint during build
  // (run `npm run lint` locally to validate).
  eslint: { ignoreDuringBuilds: true },
  // Skip type errors on Vercel (validated locally via `npx tsc --noEmit`).
  typescript: { ignoreBuildErrors: true },
};

export default nextConfig;
