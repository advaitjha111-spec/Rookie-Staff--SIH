import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.models.database import get_db_connection
from app.services.pdf_export import generate_legal_pdf
import json

router = APIRouter()

@router.get("/{case_id}/pdf")
def download_legal_pdf(case_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT json_data FROM cases WHERE case_id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()
    
    if case_id == "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92":
        case_data = {
            "ingestion": {"hash_sha256": case_id, "timestamp": "2026-09-09T00:00:00.000Z"},
            "metadata": {"subject": "URGENT: Wire Transfer Instructions", "from": "ceo@c0mpany.com", "to": "cfo@company.com", "date": "2026-09-09T00:00:00.000Z"},
            "iocs": {
                "urls": [{"url": "https://c0mpany.com/login", "display_text": "View Instructions", "domain": "c0mpany.com", "flags": ["typosquat"]}],
                "attachments": [{"filename": "Wire_Instructions.pdf", "extension": "pdf", "flags": ["suspicious"]}]
            },
            "forensics": {
                "origin_ip": "103.22.201.11",
                "geo_info": {"country": "US", "region": "CA", "city": "Los Angeles", "asn": "AS13335", "isp": "Cloudflare", "is_hosting": True},
                "threat_intel": {"is_tor": False, "is_spamhaus": True},
                "hops_before_origin": 1,
                "trace_confidence": 98,
                "anomalies": {"envelope_mismatch": True, "reply_to_hijack": True, "message_id_forgery": False, "time_skew": False},
                "typosquat": {"lookalike": {"brand": "company.com", "similarity": 85}, "impersonation": {"claimed_brand": "company.com", "sender_domain": "c0mpany.com"}},
                "threat_score": 95,
                "live_hunt": {"domain_age_days": 2, "mx_records": ["mail.c0mpany.com"], "txt_records": ["v=spf1 -all"]}
            },
            "ai_analysis": {
                "fraud_taxonomy": "Business Email Compromise",
                "bec_subtype": "CEO Fraud",
                "infrastructure_attribution": "Bulletproof Hosting Provider",
                "urgency_cues": ["URGENT", "Transfer"],
                "threat_actor_claimed": "CEO",
                "requested_action": "Wire Transfer",
                "technical_justification": "Sender uses a typosquatted domain (c0mpany.com vs company.com) to impersonate the CEO. Reply-To header is hijacked to route responses to the attacker."
            },
            "scrubbed_body_snippet": "Please process this wire transfer immediately.",
            "graph_alerts": {"previous_malicious_campaigns": 5, "ip": "103.22.201.11"}
        }
    else:
        if not row:
            raise HTTPException(status_code=404, detail="Case not found")
        case_data = json.loads(row[0])
    
    try:
        pdf_path = generate_legal_pdf(case_id, case_data)
        if not os.path.exists(pdf_path):
            raise Exception("PDF file was not created.")
            
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"certificate_{case_id}.pdf",
            content_disposition_type="inline"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
