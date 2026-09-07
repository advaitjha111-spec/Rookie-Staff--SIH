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
            filename=f"certificate_{case_id}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")
