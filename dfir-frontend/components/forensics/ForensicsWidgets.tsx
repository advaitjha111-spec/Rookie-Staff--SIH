"use client";

import { useRef, useState } from "react";
import { AlertTriangle, Check, CircleHelp, FileUp, LoaderCircle, Upload, X } from "lucide-react";
import type { EvidenceResult, AnomalyValue } from "@/types/forensics";

export function EvidenceDropzone({ onUpload, onDemo, busy }: { onUpload: (file: File) => void; onDemo?: () => void; busy: boolean }) {
  const input = useRef<HTMLInputElement>(null); const [dragging, setDragging] = useState(false); const [error, setError] = useState<string | null>(null);
  const accept = (file?: File) => { if (!file) return; if (!/\.(eml|msg)$/i.test(file.name)) { setError("Only original .eml or .msg evidence files are accepted by the backend."); return; } setError(null); onUpload(file); };
  
  const loadDemo = async () => {
    if (onDemo) {
      onDemo();
    } else {
      try {
        const res = await fetch("/demo.eml");
        if (!res.ok) throw new Error("Demo file not found");
        const blob = await res.blob();
        const file = new File([blob], "malicious-test-case.eml", { type: "message/rfc822" });
        accept(file);
      } catch (err: any) {
        setError(err.message || "Failed to load demo file");
      }
    }
  };

  return <section className={dragging ? "dropzone dragging" : "dropzone"} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={(e) => { e.preventDefault(); setDragging(false); accept(e.dataTransfer.files[0]); }}><input ref={input} type="file" accept=".eml,.msg,message/rfc822" hidden onChange={(e) => accept(e.target.files?.[0])} /><div className="upload-mark">{busy ? <LoaderCircle className="spin" /> : <FileUp />}</div><p className="eyebrow">Evidence intake</p><h2>{busy ? "Processing original evidence" : "Upload evidence"}</h2><p>{busy ? "The backend is parsing, hashing and analysing the submitted file." : "Drag and drop a forensic email file, or select it from this device."}</p><button disabled={busy} className="btn-primary" onClick={() => input.current?.click()}>{busy ? "Processing…" : <><Upload size={17} /> Select evidence</>}</button><button disabled={busy} className="btn-secondary" style={{marginTop: "8px"}} onClick={loadDemo}>{busy ? "Processing…" : "Load Demo"}</button><small className="mono">SUPPORTED: .EML / .MSG · HASHED ON INGESTION</small>{error && <p role="alert" className="form-error"><AlertTriangle size={15} /> {error}</p>}</section>;
}

export function ProcessingPipeline({ stage }: { stage: "idle" | "ingesting" | "complete" | "error" }) { const labels = ["INGEST", "HASH", "PARSE", "ANALYZE", "VERIFY"]; return <div className="pipeline" aria-label="Forensic processing pipeline">{labels.map((label, index) => <div key={label} className={stage === "complete" ? "pipeline-step complete" : stage === "ingesting" && index === 0 ? "pipeline-step active" : stage === "error" && index === 0 ? "pipeline-step error" : "pipeline-step"}><span>{stage === "complete" ? <Check size={14} /> : index + 1}</span>{label}</div>)}</div>; }

export function ThreatGauge({ score }: { score: number }) { const high = score > 70; const radius = 82; const circumference = 2 * Math.PI * radius; const offset = circumference - (Math.max(0, Math.min(100, score)) / 100) * circumference; return <section className={high ? "threat-gauge high" : "threat-gauge"}><svg viewBox="0 0 200 200" aria-label={`Threat score ${score} out of 100`} role="img"><circle cx="100" cy="100" r={radius} fill="none" stroke="var(--line)" strokeWidth="8" /><circle cx="100" cy="100" r={radius} fill="none" stroke={high ? "var(--critical)" : "var(--cyan)"} strokeWidth="8" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} transform="rotate(-90 100 100)" /></svg><div><strong>{score}</strong><span>/100</span><p>{high ? "HIGH RISK" : score > 30 ? "MEDIUM RISK" : "LOW RISK"}</p></div></section>; }

const anomalyLabel: Record<string, string> = { envelope_mismatch: "Envelope mismatch", reply_to_hijack: "Reply-To hijack", message_id_forgery: "Message-ID forgery", time_skew: "Time-skew anomaly" };
function AnomalyIcon({ value }: { value: AnomalyValue }) { if (value === true) return <X />; if (value === false) return <Check />; if (value === "not_applicable") return <CircleHelp />; return <AlertTriangle />; }
export function AnomalyChecklist({ anomalies }: { anomalies: EvidenceResult["forensics"]["anomalies"] }) { return <section className="anomaly-list"><p className="eyebrow">Routing anomaly checks</p>{Object.entries(anomalies).map(([key, value]) => <div key={key} className={`anomaly ${value === true ? "bad" : value === false ? "good" : "unknown"}`}><AnomalyIcon value={value} /><span>{anomalyLabel[key]}</span><strong>{value === true ? "Triggered" : value === false ? "Clear" : value === "not_applicable" ? "N/A" : "Undetermined"}</strong></div>)}</section>; }

export function ForensicSummary({ data }: { data: EvidenceResult }) { const ai = data.ai_analysis; return <section className="forensic-summary"><p className="eyebrow">Forensic summary</p><dl><div><dt>Evidence</dt><dd className="mono">{data.ingestion.hash_sha256}</dd></div><div><dt>Origin</dt><dd>{data.forensics.origin_ip ?? "Origin Undetermined — Likely Compromised Legitimate Infrastructure."}</dd></div><div><dt>Classification</dt><dd>{ai?.fraud_taxonomy ?? "Analysis unavailable"}</dd></div><div><dt>Assessment</dt><dd>{ai?.technical_justification ?? "The local analysis engine did not return a classification."}</dd></div></dl></section>; }

export function Terminal({ stage, error }: { stage: string; error?: string | null }) { const lines = stage === "complete" ? ["[INGEST] Evidence received", "[HASH] SHA-256 calculated", "[PARSE] Evidence structure detected", "[ANALYZE] Forensic analysis complete", "[VERIFY] Indicators available for review"] : stage === "error" ? ["[ERROR] Backend processing did not complete", error ?? "Unknown error"] : stage === "ingesting" ? ["[INGEST] Evidence received", "[HASH] Calculating SHA-256", "[PARSE] Awaiting backend response"] : ["[READY] Select original evidence to begin an investigation."]; return <section className="terminal" aria-live="polite">{lines.map((line) => <p key={line}>{line}</p>)}</section>; }
