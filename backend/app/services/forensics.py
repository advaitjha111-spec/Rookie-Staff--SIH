import os
import ipaddress
import re
from datetime import datetime, timedelta
import email.utils
from Levenshtein import ratio as levenshtein_ratio
import dns.resolver

PROTECTED_BRANDS = [
    "sbi.co.in", "rbi.org.in", "microsoft.com", "google.com",
    "paypal.com", "amazon.com", "icicibank.com", "hdfcbank.com"
]

def parse_received_chain(received_headers: list[str]) -> list[dict]:
    # Very basic parsing, would need a robust parser in reality
    # For this implementation, we extract IP and timestamp
    hops = []
    ip_regex = re.compile(r'\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]')
    
    for header in received_headers:
        # Example format: from [1.2.3.4] by relay.com; Tue, 01 Jan 2024 12:00:00 +0000
        ip_match = ip_regex.search(header)
        ip = ip_match.group(1) if ip_match else None
        
        # Try extracting claimed hostname (rough heuristic)
        hostname = None
        if "from" in header.lower() and "by" in header.lower():
            try:
                from_part = header.lower().split("by")[0]
                # naive split to get hostname before IP
                hostname_match = re.search(r'from\s+([^\s]+)', from_part)
                if hostname_match:
                    hostname = hostname_match.group(1)
            except:
                pass

        # Extract timestamp (last part after semicolon usually)
        timestamp_str = None
        if ";" in header:
            timestamp_str = header.split(";")[-1].strip()
            try:
                # Parse RFC 2822 date
                timestamp = email.utils.parsedate_to_datetime(timestamp_str)
            except:
                timestamp = None
        else:
            timestamp = None
            
        hops.append({
            "ip": ip,
            "claimed_hostname": hostname,
            "timestamp": timestamp,
            "raw": header
        })
    return hops

def is_rfc1918_private(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private
    except ValueError:
        return False

def find_true_origin(received_headers: list[str]) -> dict:
    # received_headers as they appear in the raw file: index 0 = newest hop, last = oldest
    hops = parse_received_chain(received_headers)
    hops_oldest_first = list(reversed(hops))

    origin_ip = None
    hops_walked = 0
    for hop in hops_oldest_first:
        hops_walked += 1
        if hop.get("ip") is None:
            continue
        if is_rfc1918_private(hop["ip"]):
            continue
        origin_ip = hop["ip"]
        break

    return {
        "origin_ip": origin_ip,
        "hops_before_origin": hops_walked,
        "total_hops": len(hops_oldest_first),
        "hops": hops_oldest_first
    }

def trace_confidence(origin_ip: str, time_skew_detected: bool, multiple_public_candidates: bool) -> int:
    if origin_ip is None:
        return 0   # "Undetermined"
    score = 90
    if time_skew_detected:
        score -= 30
    if multiple_public_candidates:
        score -= 20
    return max(10, min(90, score))

def extract_domain(email_address: str) -> str:
    if not email_address:
        return ""
    addr = email.utils.parseaddr(email_address)[1]
    if "@" in addr:
        return addr.split("@")[-1].lower()
    return ""

def get_spf_cidrs(domain: str) -> list[str]:
    # Placeholder for actual DNS lookup (Live Hunt Mode)
    # Since Air-gapped is default, we return empty list if offline
    cidrs = []
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for rdata in answers:
            txt_string = b''.join(rdata.strings).decode()
            if txt_string.startswith("v=spf1"):
                # VERY simplistic parsing
                parts = txt_string.split(" ")
                for part in parts:
                    if part.startswith("ip4:"):
                        cidrs.append(part.split(":", 1)[1])
    except Exception:
        pass
    return cidrs

def check_spf_authorization(origin_ip: str, domain: str, is_live_hunt: bool = False) -> bool:
    if origin_ip is None or not domain or not is_live_hunt:
        return False # Without live hunt, we can't reliably fetch SPF records from DNS. But if it's already in Authentication-Results, use that.
        
    # Check if origin_ip is in SPF cidrs
    cidrs = get_spf_cidrs(domain)
    try:
        ip_obj = ipaddress.ip_address(origin_ip)
        for cidr in cidrs:
            net = ipaddress.ip_network(cidr, strict=False)
            if ip_obj in net:
                return True
    except:
        pass
    # If we made a query and it wasn't there, it's unauthorized (or if no SPF)
    return False

def check_anomaly_rules(headers: dict, origin_info: dict) -> dict:
    from_domain = extract_domain(headers.get("from", ""))
    return_path_domain = extract_domain(headers.get("return_path", ""))
    reply_to_domain = extract_domain(headers.get("reply_to", ""))
    
    # 1. Envelope Mismatch
    envelope_mismatch = return_path_domain != from_domain if return_path_domain else False
    
    # 2. Reply-To Hijack
    reply_to_hijack = "not_applicable"
    if reply_to_domain:
        reply_to_hijack = reply_to_domain != from_domain
        
    # 3. Message-ID Forgery
    message_id_forgery = "undetermined"
    msg_id = headers.get("message_id", "")
    msg_id_domain = extract_domain(msg_id)
    
    if msg_id_domain:
        # compare against HELO of the origin hop
        hops = origin_info.get("hops", [])
        # Find the hop that has the origin IP
        origin_ip = origin_info.get("origin_ip")
        origin_hop_helo = None
        if origin_ip:
            for hop in hops:
                if hop.get("ip") == origin_ip:
                    origin_hop_helo = hop.get("claimed_hostname")
                    break
        
        if origin_hop_helo:
            message_id_forgery = (msg_id_domain.lower() != origin_hop_helo.lower())
    
    # 4. Time-Skew
    time_skew = False
    hops = origin_info.get("hops", [])
    prev_time = None
    for hop in hops:
        curr_time = hop.get("timestamp")
        if curr_time and prev_time:
            # hop timestamp must be >= previous hop timestamp - 5 minutes
            if curr_time < (prev_time - timedelta(minutes=5)):
                time_skew = True
                break
        if curr_time:
            prev_time = curr_time

    return {
        "envelope_mismatch": envelope_mismatch,
        "reply_to_hijack": reply_to_hijack,
        "message_id_forgery": message_id_forgery,
        "time_skew": time_skew
    }

def typosquat_check(from_header: str) -> dict:
    sender_domain = extract_domain(from_header)
    display_name = email.utils.parseaddr(from_header)[0]
    
    lookalike_flag = None
    for brand in PROTECTED_BRANDS:
        # Levenshtein ratio returns 0.0 to 1.0. Multiply by 100
        similarity = levenshtein_ratio(sender_domain, brand) * 100
        if 80 <= similarity < 100:
            lookalike_flag = {"brand": brand, "similarity": similarity}
            break
            
    impersonation_flag = None
    # Very basic check if brand is in display name but domain differs
    for brand in PROTECTED_BRANDS:
        brand_name = brand.split('.')[0] # "microsoft"
        if brand_name.lower() in display_name.lower():
            if sender_domain != brand:
                impersonation_flag = {"claimed_brand": brand, "sender_domain": sender_domain}
                break

    return {
        "lookalike": lookalike_flag,
        "impersonation": impersonation_flag
    }

def load_threat_intel():
    tor_nodes = set()
    spamhaus_cidrs = []
    
    # Base dir for backend is two levels up from this file (app/services/)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    # Load Tor Exit Nodes
    tor_path = os.path.join(base_dir, "tor_exit_nodes.txt")
    if os.path.exists(tor_path):
        with open(tor_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    tor_nodes.add(line)
                    
    # Load Spamhaus DROP
    spamhaus_path = os.path.join(base_dir, "spamhaus_drop.txt")
    if os.path.exists(spamhaus_path):
        with open(spamhaus_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(";"):
                    parts = line.split(";")
                    cidr = parts[0].strip()
                    try:
                        net = ipaddress.ip_network(cidr, strict=False)
                        spamhaus_cidrs.append(net)
                    except ValueError:
                        pass
                        
    return tor_nodes, spamhaus_cidrs

# Global cache for the threat intel
TOR_NODES, SPAMHAUS_CIDRS = load_threat_intel()

def check_ip_threat_intel(ip_str: str) -> dict:
    info = {
        "is_tor": False,
        "is_spamhaus": False
    }
    if not ip_str:
        return info
        
    if ip_str in TOR_NODES:
        info["is_tor"] = True
        
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        for net in SPAMHAUS_CIDRS:
            if ip_obj in net:
                info["is_spamhaus"] = True
                break
    except ValueError:
        pass
        
    return info

def calculate_threat_score(
    anomalies: dict, 
    unauthorized_infra: bool, 
    typosquat: dict, 
    vpn_tor_hosting: bool, 
    domain_age_under_30: bool, 
    fraud_taxonomy: str
) -> int:
    score = 0
    
    # Anomaly rules (10 per triggered flag, max 40)
    flags = [
        anomalies.get("envelope_mismatch") is True,
        anomalies.get("reply_to_hijack") is True,
        anomalies.get("message_id_forgery") is True,
        anomalies.get("time_skew") is True
    ]
    score += min(40, sum(10 for flag in flags if flag))
    
    if unauthorized_infra:
        score += 15
    if typosquat.get("lookalike") or typosquat.get("impersonation"):
        score += 15
    if vpn_tor_hosting:
        score += 10
    if domain_age_under_30:
        score += 10
        
    ai_points = {
        "legitimate": 0,
        "suspicious": 25,
        "impersonated": 45,
        "phishing": 65,
        "fraud-related": 75
    }
    score += ai_points.get(fraud_taxonomy, 0)
    
    return min(100, score)
