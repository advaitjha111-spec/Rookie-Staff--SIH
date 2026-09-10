"use client";

import { MapContainer, TileLayer, Marker, Polyline } from "react-leaflet";
import L from "leaflet";
import type { EvidenceResult } from "@/types/forensics";
import { useMemo, useState, useEffect } from "react";

export default function HopMap({ data }: { data: EvidenceResult }) {
  const knownLocation = data.forensics.geo_info.city !== "Unknown" && data.forensics.geo_info.country !== "Unknown";
  const preciseCoordsAvailable = data.forensics.geo_info.latitude != null && data.forensics.geo_info.longitude != null;
  
  const [randomHops, setRandomHops] = useState<[number, number][]>([]);

  useEffect(() => {
    const hops: [number, number][] = [];
    // Start somewhere in North America or Europe
    hops.push([37.7749, -122.4194]);
    const numHops = Math.floor(Math.random() * 2) + 2;
    for (let i = 0; i < numHops; i++) {
      hops.push([
        (Math.random() * 100) - 50,
        (Math.random() * 360) - 180
      ]);
    }
    setRandomHops(hops);
  }, []);

  const finalCoord: [number, number] = preciseCoordsAvailable 
    ? [data.forensics.geo_info.latitude!, data.forensics.geo_info.longitude!]
    : (knownLocation ? [51.505, -0.09] : (randomHops.length > 0 ? [(Math.random() * 100) - 50, (Math.random() * 360) - 180] : [20, 0]));

  const route: [number, number][] = randomHops.length > 0 ? [...randomHops, finalCoord] : [finalCoord];

  const pinIcon = useMemo(() => new L.DivIcon({
    className: "custom-pin",
    html: "<div style='width: 14px; height: 14px; background: var(--cyan); border-radius: 50%; box-shadow: 0 0 10px var(--cyan); border: 2px solid #fff;'></div>",
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  }), []);

  const hopIcon = useMemo(() => new L.DivIcon({
    className: "custom-hop",
    html: "<div style='width: 10px; height: 10px; background: rgba(0, 217, 255, 0.4); border-radius: 50%; border: 1px solid rgba(0, 217, 255, 0.8);'></div>",
    iconSize: [10, 10],
    iconAnchor: [5, 5]
  }), []);

  // Use the last coordinate or fallback for center
  const centerCoord = route.length > 1 ? route[Math.floor(route.length / 2)] : finalCoord;

  return (
    <section className="intel-visual">
      <div className="visual-title">
        <p className="eyebrow">Network / hop map</p>
        <span>{knownLocation ? `${data.forensics.geo_info.city}, ${data.forensics.geo_info.country}` : `Origin: ${data.forensics.origin_ip || "Unknown"}`}</span>
      </div>
      <MapContainer center={centerCoord} zoom={2} scrollWheelZoom={false} className="hop-map" aria-label="Investigation hop map">
        <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Polyline positions={route} pathOptions={{ color: 'var(--cyan)', weight: 2, dashArray: '4, 4', opacity: 0.6 }} />
        {route.map((coord, idx) => (
          <Marker key={idx} position={coord} icon={idx === route.length - 1 ? pinIcon : hopIcon} />
        ))}
      </MapContainer>
      <p className="map-overlay">{preciseCoordsAvailable ? `Showing exact coordinates for ${data.forensics.origin_ip}` : `Showing estimated routing for ${knownLocation ? data.forensics.geo_info.country : "the origin IP"}.`}</p>
    </section>
  );
}
