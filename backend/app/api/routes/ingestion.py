from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from app.services.ingestion import parse_eml
from app.services.forensics import (
    find_true_origin, check_anomaly_rules, trace_confidence, 
    typosquat_check, calculate_threat_score, check_spf_authorization,
    check_ip_threat_intel, extract_domain
)
from app.services.ai_engine import scrub_pii, analyze_email_with_llm
from app.utils.geoip import get_geo_info
from app.models.database import save_case
from app.services.graph import neo4j_service
from app.services.live_hunt import run_live_hunt
from app.core.websocket_manager import manager
import asyncio

router = APIRouter()

@router.post("/upload")
async def upload_email(file: UploadFile = File(...), live_hunt: bool = Form(False)):
    if not file.filename.endswith(('.eml', '.msg')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .eml and .msg allowed.")
    
    try:
        raw_bytes = await file.read()
        
        # 1. Ingestion
        ingest_data = parse_eml(raw_bytes)
        
        # 2. Forensics
        received_headers = ingest_data["headers"]["received"]
        origin_info = find_true_origin(received_headers)
        origin_ip = origin_info.get("origin_ip")
        
        anomalies = check_anomaly_rules(ingest_data["headers"], origin_info)
        confidence = trace_confidence(origin_ip, anomalies.get("time_skew", False), False)
        typo_results = typosquat_check(ingest_data["metadata"]["from"])
        
        # Threat intel and Geo IP
        geo_info = get_geo_info(origin_ip)
        threat_intel = check_ip_threat_intel(origin_ip)
        
        vpn_tor_hosting = threat_intel["is_tor"] or threat_intel["is_spamhaus"] or geo_info["is_hosting"]
        
        # For offline, we don't do SPF checks accurately, but passing default false
        unauth_infra = False  
        
        # 3. Live Hunt Mode
        domain_age_under_30 = False
        live_hunt_data = None
        if live_hunt and ingest_data["metadata"]["from"]:
            sender_domain = extract_domain(ingest_data["metadata"]["from"])
            if sender_domain:
                live_hunt_data = run_live_hunt(sender_domain)
                age = live_hunt_data.get("domain_age_days")
                if age is not None and age < 30:
                    domain_age_under_30 = True

        # 4. AI Classification
        scrubbed_body = scrub_pii(ingest_data["body_text"])
        ai_result = None
        try:
            ai_result = analyze_email_with_llm(scrubbed_body)
        except Exception as e:
            print(f"AI Engine failed: {e}")
            pass
            
        ai_taxonomy = ai_result.fraud_taxonomy if ai_result else "suspicious"
        
        # 4. Threat Score
        score = calculate_threat_score(
            anomalies=anomalies,
            unauthorized_infra=unauth_infra,
            typosquat=typo_results,
            vpn_tor_hosting=vpn_tor_hosting,
            domain_age_under_30=domain_age_under_30,
            fraud_taxonomy=ai_taxonomy
        )
        
        response_data = {
            "ingestion": ingest_data["ingestion"],
            "metadata": ingest_data["metadata"],
            "iocs": ingest_data["iocs"],
            "forensics": {
                "origin_ip": origin_ip,
                "geo_info": geo_info,
                "threat_intel": threat_intel,
                "hops_before_origin": origin_info["hops_before_origin"],
                "trace_confidence": confidence,
                "anomalies": anomalies,
                "typosquat": typo_results,
                "threat_score": score,
                "live_hunt": live_hunt_data
            },
            "ai_analysis": ai_result.model_dump() if ai_result else None,
            "scrubbed_body_snippet": scrubbed_body[:200] + "..." if scrubbed_body else ""
        }
        
        # Save to SQLite
        try:
            save_case(response_data)
        except Exception as db_e:
            print(f"Error saving to SQLite: {db_e}")
            
        # Save to Neo4j
        try:
            campaign_info = neo4j_service.add_case_to_graph(response_data)
            if campaign_info and campaign_info.get("previous_malicious_campaigns", 0) > 0:
                response_data["graph_alerts"] = campaign_info
        except Exception as neo_e:
            print(f"Error saving to Neo4j: {neo_e}")
            
        # Trigger WebSocket Alert
        bec_subtype = ai_result.bec_subtype if ai_result else "none"
        if score >= 70 or bec_subtype != "none":
            alert_msg = {
                "type": "high_risk_alert",
                "case_id": response_data["ingestion"]["hash_sha256"],
                "threat_score": score,
                "fraud_taxonomy": ai_taxonomy,
                "bec_subtype": bec_subtype,
                "subject": response_data["metadata"]["subject"]
            }
            # Use asyncio.create_task so we don't block
            asyncio.create_task(manager.broadcast(alert_msg))
            
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
