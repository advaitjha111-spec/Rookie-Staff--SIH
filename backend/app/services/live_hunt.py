import whois
import dns.resolver
from datetime import datetime

def run_live_hunt(domain: str) -> dict:
    """
    Performs live WHOIS and DNS lookups on a given domain.
    Returns domain age, MX records, and TXT records.
    """
    if not domain:
        return {"domain_age_days": None, "mx_records": [], "txt_records": []}
        
    result = {
        "domain_age_days": None,
        "mx_records": [],
        "txt_records": []
    }
    
    # WHOIS
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        
        # sometimes creation_date is a list
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
            
        if creation_date:
            now = datetime.now(creation_date.tzinfo) if creation_date.tzinfo else datetime.now()
            age = (now - creation_date).days
            result["domain_age_days"] = max(0, age)
    except Exception as e:
        print(f"WHOIS lookup failed for {domain}: {e}")
        
    # DNS MX
    try:
        mx_answers = dns.resolver.resolve(domain, 'MX')
        result["mx_records"] = [str(r.exchange) for r in mx_answers]
    except Exception as e:
        pass
        
    # DNS TXT (often holds SPF)
    try:
        txt_answers = dns.resolver.resolve(domain, 'TXT')
        result["txt_records"] = [str(r.to_text()) for r in txt_answers]
    except Exception as e:
        pass
        
    return result
