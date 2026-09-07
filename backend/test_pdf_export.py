import os
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import get_db_connection

client = TestClient(app)

def run_tests():
    print("==================================================")
    print("Phase 2C Integration Tests: Legal PDF Export")
    print("==================================================")
    
    # Let's get the first available case from the SQLite DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT case_id FROM cases LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("No cases found in DB to test PDF export on. Run Phase 2 tests first.")
        return
        
    case_id = row[0]
    print(f"Testing PDF export for Case ID: {case_id}")
    
    # Test the API endpoint
    response = client.get(f"/api/v1/cases/{case_id}/pdf")
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code == 200:
        content_type = response.headers.get("content-type")
        print(f"Content Type: {content_type}")
        if content_type == "application/pdf":
            print("[SUCCESS] PDF endpoint returned application/pdf!")
        else:
            print("[ERROR] Wrong content type.")
            
        # Verify the file is actually on disk where expected
        base_dir = os.path.dirname(os.path.abspath(__file__))
        pdf_path = os.path.join(base_dir, "exports", f"{case_id}.pdf")
        if os.path.exists(pdf_path):
            print(f"[SUCCESS] PDF file physically exists at {pdf_path}")
            size = os.path.getsize(pdf_path)
            print(f"File Size: {size} bytes")
        else:
            print(f"[ERROR] PDF file not found at {pdf_path}")
            
    else:
        print(f"Failed to generate PDF. Response: {response.text}")

if __name__ == "__main__":
    run_tests()
