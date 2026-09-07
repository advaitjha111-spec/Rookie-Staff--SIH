import os
import sys
import json
from fastapi.testclient import TestClient

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app

client = TestClient(app)

def test_upload_endpoint():
    print(f"\n{'='*50}\nTesting FastAPI Ingestion Endpoint\n{'='*50}")
    
    base_dir = os.path.dirname(__file__)
    files = [
        os.path.join(base_dir, "test_data/legit.eml"), 
        os.path.join(base_dir, "test_data/phishing.eml"), 
        os.path.join(base_dir, "test_data/spoofed_bec.eml")
    ]
    
    for file_path in files:
        print(f"\nTesting {file_path}...")
        with open(file_path, "rb") as f:
            response = client.post(
                "/api/v1/upload", 
                files={"file": (os.path.basename(file_path), f, "message/rfc822")}
            )
            
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Hash:", data["ingestion"]["hash_sha256"])
            print("Origin IP:", data["forensics"]["origin_ip"])
            print("Threat Score:", data["forensics"]["threat_score"])
            
            ai_data = data.get("ai_analysis")
            if ai_data:
                print("AI Taxonomy:", ai_data.get("fraud_taxonomy"))
                print("AI Infrastructure:", ai_data.get("infrastructure_attribution"))
            else:
                print("AI Analysis: None")
                
            print("\nScrubbed Body Snippet:")
            print(repr(data.get("scrubbed_body_snippet")))
        else:
            print("Response:", response.text)

if __name__ == "__main__":
    test_upload_endpoint()
