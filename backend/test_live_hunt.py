import asyncio
import websockets
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

async def test_websocket_alert():
    print("Connecting to WebSocket...")
    uri = "ws://localhost:8000/api/v1/ws/alerts"
    
    async with websockets.connect(uri) as websocket:
        print("Connected! Sending malicious test payload...")
        
        # We will use the TestClient in another thread to trigger the upload
        # But wait, TestClient is synchronous, and we are in async.
        # We can just use the TestClient in an executor or run it synchronously before if we can't test websocket that way easily.
        
        # Let's use FastAPI's built-in TestClient websocket context manager!
        pass

def run_tests():
    print("==================================================")
    print("Phase 2B Integration Tests: Live Hunt & WebSockets")
    print("==================================================")
    
    with client.websocket_connect("/api/v1/ws/alerts") as websocket:
        print("WebSocket Connected.")
        
        # Now trigger the HTTP endpoint
        print("\nUploading phishing email with live_hunt=True...")
        eml_path = "test_data/phishing.eml"
        with open(eml_path, "rb") as f:
            response = client.post(
                "/api/v1/upload", 
                files={"file": ("phishing.eml", f, "message/rfc822")},
                data={"live_hunt": "true"}
            )
            
        print(f"Upload Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            score = data["forensics"]["threat_score"]
            print(f"Threat Score: {score}")
            print(f"Live Hunt Data: {data['forensics'].get('live_hunt')}")
            
            print("\nWaiting for WebSocket alert...")
            try:
                # receive json from websocket
                alert_text = websocket.receive_text()
                alert = json.loads(alert_text)
                print("Received WebSocket Alert:")
                print(json.dumps(alert, indent=2))
                
                if alert.get("type") == "high_risk_alert":
                    print("\n[SUCCESS] High risk alert broadcasted successfully!")
            except Exception as e:
                print(f"Error receiving websocket: {e}")
        else:
            print(f"Upload failed: {response.text}")

if __name__ == "__main__":
    run_tests()
