import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow the frontend to sit alongside a separate backend workspace.
  outputFileTracingRoot: process.cwd(),
  // Vercel requires the default ".next" output directory.
  // Use ".next-production" locally only when needed via CLI:
  //   NEXT_DIST_DIR=.next-production next build
};

export default nextConfig;
