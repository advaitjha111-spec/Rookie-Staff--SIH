"use client";

import { useEffect, useRef, useState } from "react";
import createGlobe, { type COBEOptions } from "cobe";

type GlobeMarker = { location: [number, number]; size: number; color?: [number, number, number]; id?: string };
type GlobeArc = { from: [number, number]; to: [number, number]; color?: [number, number, number] };

const CYAN: [number, number, number] = [0, 217 / 255, 1];
const BASE: [number, number, number] = [0.08, 0.18, 0.22];
const GLOW: [number, number, number] = [0, 0.8, 1];

const VERCEL_LOCATIONS: Record<string, [number, number]> = {
  sfo1: [37.7749, -122.4194],
  iad1: [38.9072, -77.0369],
  arn1: [59.3293, 18.0686],
  dub1: [53.3498, -6.2603],
  hnd1: [35.6762, 139.6503],
  syd1: [-33.8688, 151.2093],
  gru1: [-23.5505, -46.6333],
};

const DEFAULT_MARKERS: GlobeMarker[] = Object.entries(VERCEL_LOCATIONS).map(([id, location]) => ({
  location,
  size: 0.04,
  id,
}));

const DEFAULT_ARCS: GlobeArc[] = [
  { from: VERCEL_LOCATIONS.hnd1, to: VERCEL_LOCATIONS.sfo1 },
  { from: VERCEL_LOCATIONS.sfo1, to: VERCEL_LOCATIONS.iad1 },
  { from: VERCEL_LOCATIONS.iad1, to: VERCEL_LOCATIONS.dub1 },
  { from: VERCEL_LOCATIONS.dub1, to: VERCEL_LOCATIONS.arn1 },
  { from: VERCEL_LOCATIONS.iad1, to: VERCEL_LOCATIONS.gru1 },
  { from: VERCEL_LOCATIONS.hnd1, to: VERCEL_LOCATIONS.syd1 },
];

export function CobeGlobe({ className, style, markers = DEFAULT_MARKERS, arcs = DEFAULT_ARCS }: { className?: string; style?: React.CSSProperties; markers?: GlobeMarker[]; arcs?: GlobeArc[] }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let globe: ReturnType<typeof createGlobe> | undefined;
    let frame = 0;
    let phi = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const size = () => canvas.parentElement?.clientWidth || canvas.clientWidth || 1000;
    try {
      const initial = size();
      let cssSize = initial;
      const options: COBEOptions = {
        devicePixelRatio: dpr, width: cssSize, height: cssSize, phi: 0, theta: 0.18,
        dark: 1, diffuse: 1.15, scale: 0.8, mapSamples: 16000, mapBrightness: 2.5,
        baseColor: BASE, markerColor: CYAN, glowColor: GLOW, markers, 
        arcs: arcs, arcColor: CYAN, arcWidth: 1.5, arcHeight: 0.5, markerElevation: 0.1,
        offset: [0, 0],
      };
      globe = createGlobe(canvas, options);
      const render = () => {
        phi += 0.005;
        globe?.update({ phi, width: cssSize, height: cssSize });
        frame = requestAnimationFrame(render);
      };
      frame = requestAnimationFrame(render);
      const resize = () => { 
        cssSize = size(); 
        canvas.style.width = `${cssSize}px`; 
        canvas.style.height = `${cssSize}px`; 
      };
      resize(); window.addEventListener("resize", resize, { passive: true });
      return () => { cancelAnimationFrame(frame); window.removeEventListener("resize", resize); globe?.destroy(); };
    } catch { setFailed(true); return () => cancelAnimationFrame(frame); }
  }, [markers, arcs]);
  if (failed) return <div className="globe-fallback" role="img" aria-label="Global telemetry visualization unavailable"><span>Telemetry visualization unavailable</span></div>;
  return (
    <div className={className} style={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", aspectRatio: "1/1", ...style }}>
      <canvas ref={canvasRef} aria-label="PRATIKRIYA global threat telemetry globe" role="img" style={{ display: "block", width: "100%", height: "100%", opacity: 1 }} />
    </div>
  );
}
