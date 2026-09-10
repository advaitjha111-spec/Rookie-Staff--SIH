"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { Globe2 } from "lucide-react";
import type { EvidenceResult } from "@/types/forensics";
import { DashboardShell } from "@/components/layout/DashboardShell";

import { motion } from "framer-motion";
const HopMap = dynamic(() => import("./HopMap"), { ssr: false, loading: () => <div className="visual-loading">Loading Leaflet map…</div> });
const CampaignGraph = dynamic(() => import("./ThreatVisuals").then((module) => module.CampaignGraph), { ssr: false, loading: () => <div className="visual-loading">Loading campaign graph…</div> });

export function IntelligenceWorkspace() { const [data, setData] = useState<EvidenceResult | null>(null); useEffect(() => { const raw = sessionStorage.getItem("pratikriya-active-case"); if (raw) try { setData(JSON.parse(raw)); } catch { /* render empty state */ } }, []); return <DashboardShell title="Threat intelligence"><div className="intelligence-page"><div className="intel-intro"><p className="eyebrow">Evidence-linked infrastructure</p><h2>Investigate the signals the backend actually returned.</h2></div>{!data ? <motion.div initial={{opacity:0, y:20}} animate={{opacity:1, y:0}} className="intel-empty panel"><Globe2 size={36} /><h3>No active threat dataset</h3><p>Process evidence first. This workspace deliberately does not generate or scrape threat intelligence.</p></motion.div> : <><motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="intelligence-grid"><HopMap data={data} /><CampaignGraph data={data} /></motion.div><motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="indicator-panel panel"><div><p className="eyebrow">Threat indicators</p><h3>{data.forensics.origin_ip ?? "Origin undetermined"}</h3></div><dl><div><dt>TOR exit</dt><dd>{data.forensics.threat_intel.is_tor ? "Matched" : "Not matched"}</dd></div><div><dt>Spamhaus DROP</dt><dd>{data.forensics.threat_intel.is_spamhaus ? "Matched" : "Not matched"}</dd></div><div><dt>Hosting signal</dt><dd>{data.forensics.geo_info.is_hosting ? "Hosting ASN" : "No hosting signal"}</dd></div><div><dt>Campaign alert</dt><dd>{data.graph_alerts ? `${data.graph_alerts.previous_malicious_campaigns} linked cases` : "No alert returned"}</dd></div></dl></motion.section></>}</div></DashboardShell>; }
