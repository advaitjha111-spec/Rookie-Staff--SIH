import os
import json
from pprint import pprint
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath('backend'))

from app.services.ingestion import parse_eml
from app.services.forensics import find_true_origin, trace_confidence, check_anomaly_rules, typosquat_check, check_spf_authorization, calculate_threat_score
from app.services.ai_engine import scrub_pii, analyze_email_with_llm

def create_fixtures():
    os.makedirs("test_data", exist_ok=True)
    
    # 1. Legit Email
    legit = """Return-Path: <john.doe@gmail.com>
Received: from mail-oi1-f193.google.com (mail-oi1-f193.google.com [209.85.167.193])
        by mx.target.com with ESMTPS id 12345
        for <analyst@target.com>; Mon, 01 Jan 2024 10:00:00 +0000
Received: by mail-oi1-f193.google.com with SMTP id 67890
        for <analyst@target.com>; Mon, 01 Jan 2024 09:59:58 +0000
Message-ID: <abc123xyz@mail.gmail.com>
Date: Mon, 01 Jan 2024 09:59:50 +0000
From: "John Doe" <john.doe@gmail.com>
To: analyst@target.com
Subject: Team Lunch Details
Content-Type: text/plain; charset="UTF-8"

Hi Team,

Just a reminder that our lunch is at 12 PM today at the usual place.
My number is 9876543210 if you need to reach me.

Best,
John
"""
    with open("test_data/legit.eml", "wb") as f:
        f.write(legit.encode('utf-8'))

    # 2. Obvious Phishing
    phishing = """Return-Path: <bounces@evil-hacker-domain.xyz>
Received: from evil.com (evil.com [185.20.30.40])
        by mx.target.com with ESMTPS id 54321
        for <user@target.com>; Mon, 01 Jan 2024 11:00:00 +0000
Message-ID: <forged_id@paypal.com>
Date: Mon, 01 Jan 2024 10:59:50 +0000
From: "PayPal Security" <support@paypal-secure-update.com>
To: user@target.com
Subject: URGENT: Your account has been suspended!
Content-Type: text/html; charset="UTF-8"

<html>
<body>
<p>Dear Customer,</p>
<p>We detected unusual activity on your account. Your account has been suspended.</p>
<p>Please click here immediately to restore access:</p>
<p><a href="http://bit.ly/malicious-link">https://paypal.com/secure-login</a></p>
<p>Failure to act within 24 hours will result in permanent deletion.</p>
</body>
</html>
"""
    with open("test_data/phishing.eml", "wb") as f:
        f.write(phishing.encode('utf-8'))

    # 3. Spoofed BEC
    bec = """Return-Path: <ceo.personal@yahoo.com>
Received: from unknown-relay.net (unknown.net [103.45.67.89])
        by mx.target.com with ESMTPS id 99999
        for <finance@target.com>; Mon, 01 Jan 2024 12:00:00 +0000
Message-ID: <random-id@yahoo.com>
Reply-To: ceo.urgent@protonmail.com
Date: Mon, 01 Jan 2024 12:00:00 +0000
From: "CEO Name" <ceo.personal@yahoo.com>
To: finance@target.com
Subject: Urgent wire transfer needed
Content-Type: text/plain; charset="UTF-8"

Hi,

I am in a meeting and cannot take calls. I need you to process an urgent wire transfer to a new vendor right away to secure a contract.
Please send $50,000 to Account number: 123456789012345 at Global Bank.

Let me know when it is done.

Regards,
CEO
"""
    with open("test_data/spoofed_bec.eml", "wb") as f:
        f.write(bec.encode('utf-8'))

def run_pipeline(filepath: str):
    print(f"\n{'='*50}\nTesting {filepath}\n{'='*50}")
    with open(filepath, "rb") as f:
        raw_bytes = f.read()

    # 1. Ingestion
    ingest_data = parse_eml(raw_bytes)
    print("Ingested! Hash:", ingest_data["ingestion"]["hash_sha256"])
    
    # 2. Forensics - Hop Trace
    received_headers = ingest_data["headers"]["received"]
    origin_info = find_true_origin(received_headers)
    origin_ip = origin_info.get("origin_ip")
    print(f"Origin IP: {origin_ip} (Hops before: {origin_info['hops_before_origin']})")
    
    # 3. Anomaly Rules
    anomalies = check_anomaly_rules(ingest_data["headers"], origin_info)
    print("Anomalies:", anomalies)
    
    # Trace Confidence
    confidence = trace_confidence(origin_ip, anomalies.get("time_skew", False), False)
    print("Trace Confidence:", confidence)
    
    # 4. Typosquat Check
    typo_results = typosquat_check(ingest_data["metadata"]["from"])
    print("Typosquat/Impersonation:", typo_results)
    
    # 5. AI Engine
    # Scrub PII
    scrubbed = scrub_pii(ingest_data["body_text"])
    print("\nScrubbed Body snippet:", repr(scrubbed[:100]))
    
    # AI Classification (Will fail if Ollama isn't running, but we'll try)
    print("\nRunning AI Classification...")
    try:
        ai_result = analyze_email_with_llm(scrubbed)
        print("AI Result Taxonomy:", ai_result.fraud_taxonomy)
        print("AI Result Subtype:", ai_result.bec_subtype)
        print("AI Infrastructure:", ai_result.infrastructure_attribution)
        print("AI Justification:", ai_result.technical_justification)
    except Exception as e:
        print("AI Engine Error (Is Ollama running?):", str(e))
        ai_result = None

    # Threat Score
    ai_taxonomy = ai_result.fraud_taxonomy if ai_result else "legitimate"
    score = calculate_threat_score(
        anomalies=anomalies,
        unauthorized_infra=False, # default for Airgapped
        typosquat=typo_results,
        vpn_tor_hosting=False, # missing mock data for this script
        domain_age_under_30=False,
        fraud_taxonomy=ai_taxonomy
    )
    print("\nFinal Threat Score:", score)

if __name__ == "__main__":
    create_fixtures()
    for file in ["test_data/legit.eml", "test_data/phishing.eml", "test_data/spoofed_bec.eml"]:
        run_pipeline(file)
