import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.models.database import get_cases
from app.utils.geoip import get_geo_info
from app.services.forensics import check_ip_threat_intel

def test_sqlite():
    print("\n--- Testing SQLite ---")
    cases = get_cases()
    print(f"Total cases in SQLite DB: {len(cases)}")
    for case in cases:
        print(f"Case ID: {case['case_id']}, Threat Score: {case['threat_score']}, Origin IP: {case['origin_ip']}")

def test_geoip():
    print("\n--- Testing MaxMind GeoIP Wrapper ---")
    ip = "8.8.8.8"
    info = get_geo_info(ip)
    print(f"GeoIP for {ip}: {info}")
    
def test_threat_intel():
    print("\n--- Testing Threat Intel (Spamhaus / Tor) ---")
    # Using dummy IPs that might or might not be in the list, just to show it runs
    ip = "185.20.30.40"
    intel = check_ip_threat_intel(ip)
    print(f"Threat Intel for {ip}: {intel}")

if __name__ == "__main__":
    print("="*50)
    print("Phase 2 Integration Tests")
    print("="*50)
    test_sqlite()
    test_geoip()
    test_threat_intel()
    print("\n[Phase 2 Testing Complete]")
