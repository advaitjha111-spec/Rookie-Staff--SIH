export type AnomalyValue = boolean | "not_applicable" | "undetermined";

export interface EvidenceResult {
  ingestion: { hash_sha256: string; timestamp: string };
  metadata: { subject: string; from: string; to: string; date: string };
  iocs: {
    urls: Array<{ url: string; display_text: string; domain: string; flags: string[] }>;
    attachments: Array<{ filename: string; extension: string; flags: string[] }>;
  };
  forensics: {
    origin_ip: string | null;
    geo_info: { country: string; region: string; city: string; asn: string; isp: string; is_hosting: boolean; latitude?: number | null; longitude?: number | null; };
    threat_intel: { is_tor: boolean; is_spamhaus: boolean };
    hops_before_origin: number;
    trace_confidence: number;
    anomalies: Record<"envelope_mismatch" | "reply_to_hijack" | "message_id_forgery" | "time_skew", AnomalyValue>;
    typosquat: { lookalike: { brand: string; similarity: number } | null; impersonation: { claimed_brand: string; sender_domain: string } | null };
    threat_score: number;
    live_hunt: { domain_age_days: number | null; mx_records: string[]; txt_records: string[] } | null;
  };
  ai_analysis: {
    fraud_taxonomy: string;
    bec_subtype: string;
    infrastructure_attribution: string;
    urgency_cues: string[];
    threat_actor_claimed: string | null;
    requested_action: string | null;
    technical_justification: string;
  } | null;
  scrubbed_body_snippet: string;
  graph_alerts?: { previous_malicious_campaigns: number; ip: string | null };
}

export interface CaseSummary {
  case_id: string;
  timestamp: string;
  origin_ip: string | null;
  threat_score: number;
  fraud_taxonomy: string;
}
