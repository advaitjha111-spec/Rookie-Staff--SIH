"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, ShieldAlert } from "lucide-react";
import { dfirApi } from "@/services/api";
import type { EvidenceResult } from "@/types/forensics";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { AnomalyChecklist, EvidenceDropzone, ForensicSummary, ProcessingPipeline, Terminal, ThreatGauge } from "@/components/forensics/ForensicsWidgets";

type Stage = "idle" | "ingesting" | "complete" | "error";
export function DashboardWorkspace() {
  const [result, setResult] = useState<EvidenceResult | null>(null); const [stage, setStage] = useState<Stage>("idle"); const [liveHunt, setLiveHunt] = useState(false); const [error, setError] = useState<string | null>(null);
  useEffect(() => { const stored = sessionStorage.getItem("pratikriya-active-case"); if (stored) { try { setResult(JSON.parse(stored)); setStage("complete"); } catch { sessionStorage.removeItem("pratikriya-active-case"); } } }, []);
  const upload = async (file: File) => { setError(null); setStage("ingesting"); try { const data = await dfirApi.ingestEvidence(file, liveHunt); setResult(data); sessionStorage.setItem("pratikriya-active-case", JSON.stringify(data)); setStage("complete"); } catch (uploadError) { setError(uploadError instanceof Error ? uploadError.message : "Upload did not complete."); setStage("error"); } };
  const runDemo = () => {
    setError(null);
    setStage("ingesting");
    setTimeout(() => {
      const demoData: EvidenceResult = {
        ingestion: { hash_sha256: "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92", timestamp: new Date().toISOString() },
        metadata: { subject: "URGENT: Wire Transfer Instructions", from: "ceo@c0mpany.com", to: "cfo@company.com", date: new Date().toISOString() },
        iocs: {
          urls: [{ url: "https://c0mpany.com/login", display_text: "View Instructions", domain: "c0mpany.com", flags: ["typosquat"] }],
          attachments: [{ filename: "Wire_Instructions.pdf", extension: "pdf", flags: ["suspicious"] }]
        },
        forensics: {
          origin_ip: "103.22.201.11",
          geo_info: { country: "US", region: "CA", city: "Los Angeles", asn: "AS13335", isp: "Cloudflare", is_hosting: true },
          threat_intel: { is_tor: false, is_spamhaus: true },
          hops_before_origin: 1,
          trace_confidence: 98,
          anomalies: { envelope_mismatch: true, reply_to_hijack: true, message_id_forgery: false, time_skew: false },
          typosquat: { lookalike: { brand: "company.com", similarity: 85 }, impersonation: { claimed_brand: "company.com", sender_domain: "c0mpany.com" } },
          threat_score: 95,
          live_hunt: { domain_age_days: 2, mx_records: ["mail.c0mpany.com"], txt_records: ["v=spf1 -all"] }
        },
        ai_analysis: {
          fraud_taxonomy: "Business Email Compromise",
          bec_subtype: "CEO Fraud",
          infrastructure_attribution: "Bulletproof Hosting Provider",
          urgency_cues: ["URGENT", "Transfer"],
          threat_actor_claimed: "CEO",
          requested_action: "Wire Transfer",
          technical_justification: "Sender uses a typosquatted domain (c0mpany.com vs company.com) to impersonate the CEO. Reply-To header is hijacked to route responses to the attacker."
        },
        scrubbed_body_snippet: "Please process this wire transfer immediately.",
        graph_alerts: { previous_malicious_campaigns: 5, ip: "103.22.201.11" }
      };
      setResult(demoData);
      sessionStorage.setItem("pratikriya-active-case", JSON.stringify(demoData));
      setStage("complete");
    }, 600);
  };
  const reset = () => { setResult(null); setStage("idle"); setError(null); sessionStorage.removeItem("pratikriya-active-case"); };
  return <DashboardShell title={result?.metadata.subject || "Active investigation"}><div className="dashboard-top"><div><p className="eyebrow">Evidence-to-analysis workflow</p><p className="workspace-lede">Submit one original email file for a backend-authoritative forensic assessment.</p></div><div style={{display: "flex", gap: "16px", alignItems: "center"}}><label className="live-hunt"><input type="checkbox" checked={liveHunt} disabled={stage === "ingesting"} onChange={(e) => setLiveHunt(e.target.checked)} /><span>Live Hunt</span><small>{liveHunt ? "WHOIS/DNS opt-in enabled" : "Air-gapped default"}</small></label>{result && <button onClick={reset} className="btn-secondary" style={{padding: "8px 16px", fontSize: "13px"}}>New Upload</button>}</div></div><ProcessingPipeline stage={stage} /><div className="dashboard-main">{!result || stage === "error" ? <EvidenceDropzone onUpload={upload} onDemo={runDemo} busy={stage === "ingesting"} /> : <EvidencePanel result={result} />}</div><Terminal stage={stage} error={error} />{error && <div className="alert-banner" role="alert"><ShieldAlert size={18} />{error}</div>}</DashboardShell>;
}

import { motion } from "framer-motion";

function EvidencePanel({ result }: { result: EvidenceResult }) { const ai = result.ai_analysis; return <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } }} className="results-grid"><motion.section variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="panel evidence-panel"><div className="result-heading"><div><p className="eyebrow">Evidence received</p><h2>{result.metadata.subject || "Untitled evidence"}</h2><p className="mono hash">{result.ingestion.hash_sha256}</p></div><span className="status-badge">{ai?.fraud_taxonomy ?? "ANALYSIS UNAVAILABLE"}</span></div><div className="metadata-grid"><span><small>From</small>{result.metadata.from || "Not present"}</span><span><small>Most likely origin</small><b className="mono">{result.forensics.origin_ip ?? "Undetermined"}</b></span><span><small>Trace confidence</small>{result.forensics.trace_confidence}%</span><span><small>Geo / ASN</small>{result.forensics.geo_info.city}, {result.forensics.geo_info.country} · {result.forensics.geo_info.asn}</span></div>{result.graph_alerts && <div className="alert-banner"><ShieldAlert size={17} />Active repeat campaign: {result.graph_alerts.previous_malicious_campaigns} linked prior cases.</div>}<div className="result-links"><Link href="/dashboard/intelligence">Investigate infrastructure <ExternalLink size={16} /></Link><Link href="/dashboard/certificate">Prepare certificate <ExternalLink size={16} /></Link></div></motion.section><motion.aside variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="panel score-panel"><ThreatGauge score={result.forensics.threat_score} /><p className="classification">{ai?.bec_subtype?.replaceAll("_", " ") ?? "No BEC subtype returned"}</p></motion.aside><motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="panel"><AnomalyChecklist anomalies={result.forensics.anomalies} /></motion.div><motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="panel"><ForensicSummary data={result} /></motion.div><motion.section variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className="panel ioc-panel"><p className="eyebrow">Extracted indicators</p><div>{result.iocs.urls.length === 0 && result.iocs.attachments.length === 0 ? <p className="muted">No URLs or attachments were extracted from this evidence.</p> : <>{result.iocs.urls.map((ioc) => <p className="mono" key={ioc.url}>{ioc.domain || ioc.url} {ioc.flags.length > 0 && <em>{ioc.flags.join(", ")}</em>}</p>)}{result.iocs.attachments.map((attachment) => <p className="mono" key={attachment.filename}>{attachment.filename} {attachment.flags.length > 0 && <em>{attachment.flags.join(", ")}</em>}</p>)}</>}</div></motion.section></motion.div>; }
