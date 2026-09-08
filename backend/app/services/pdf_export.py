import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

# Make sure an exports directory exists
EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'exports'))
os.makedirs(EXPORT_DIR, exist_ok=True)

def generate_legal_pdf(case_id: str, case_data: dict) -> str:
    """
    Generates a Certificate under Section 63(4) of the Bharatiya Sakshya Adhiniyam, 2023.
    """
    filepath = os.path.join(EXPORT_DIR, f"{case_id}.pdf")
    
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=1, fontSize=14, spaceAfter=14, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SubTitle', fontSize=12, spaceAfter=10, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Mono', fontName='Courier', fontSize=9, leading=11))
    
    Story = []
    
    # Title
    Story.append(Paragraph("Certificate under Section 63(4) of the Bharatiya Sakshya Adhiniyam, 2023", styles['CenterTitle']))
    Story.append(Paragraph("pending examiner countersignature", styles['Normal']))
    Story.append(Spacer(1, 12))
    
    # Header: Hash and Timestamp
    ingestion = case_data.get("ingestion", {})
    Story.append(Paragraph(f"<b>SHA-256 Hash:</b> {ingestion.get('hash_sha256', 'N/A')}", styles['Mono']))
    Story.append(Paragraph(f"<b>Ingestion Timestamp:</b> {ingestion.get('timestamp', 'N/A')}", styles['Normal']))
    Story.append(Spacer(1, 24))
    
    # PART A
    Story.append(Paragraph("PART A: Statutory Declaration", styles['SubTitle']))
    Story.append(Paragraph("I, _________________________________ (Name), being _________________________________ (Relationship to Device) at ______________________________________________________________ (Address), do hereby declare that the electronic record identified by the cryptographic hash above was produced by a computer/device operating properly under my lawful control.", styles['Normal']))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("<b>Device Identification:</b>", styles['Normal']))
    Story.append(Paragraph("[  ] Make/Model: _______________________", styles['Normal']))
    Story.append(Paragraph("[  ] Serial No: ________________________", styles['Normal']))
    Story.append(Paragraph("[  ] IMEI/MAC: _________________________", styles['Normal']))
    Story.append(Paragraph("[  ] Cloud ID: _________________________", styles['Normal']))
    Story.append(Spacer(1, 12))
    Story.append(Paragraph("I certify that to the best of my knowledge, the computer/device was operating properly and there was no interference that could affect the accuracy of the electronic record.", styles['Normal']))
    Story.append(Spacer(1, 24))
    
    # TECHNICAL ANNEXURE
    Story.append(Paragraph("TECHNICAL ANNEXURE", styles['SubTitle']))
    metadata = case_data.get("metadata", {})
    Story.append(Paragraph(f"<b>Subject:</b> {metadata.get('subject', 'N/A')}", styles['Normal']))
    Story.append(Paragraph(f"<b>From:</b> {metadata.get('from', 'N/A')}", styles['Normal']))
    Story.append(Spacer(1, 12))
    
    forensics = case_data.get("forensics", {})
    origin_ip = forensics.get("origin_ip", "Undetermined")
    geo = forensics.get("geo_info", {})
    Story.append(Paragraph(f"<b>Origin IP:</b> {origin_ip}", styles['Normal']))
    Story.append(Paragraph(f"<b>Geolocation:</b> {geo.get('city')}, {geo.get('country')} (ASN: {geo.get('asn')})", styles['Normal']))
    Story.append(Paragraph(f"<b>Threat Score:</b> {forensics.get('threat_score', 'N/A')} / 100", styles['Normal']))
    Story.append(Spacer(1, 12))
    
    ai_analysis = case_data.get("ai_analysis", {})
    if ai_analysis:
        Story.append(Paragraph("<b>AI Analysis Summary:</b>", styles['Normal']))
        Story.append(Paragraph(f"Taxonomy: {ai_analysis.get('fraud_taxonomy')}", styles['Normal']))
        Story.append(Paragraph(f"BEC Subtype: {ai_analysis.get('bec_subtype')}", styles['Normal']))
        Story.append(Paragraph(f"Justification: {ai_analysis.get('technical_justification')}", styles['Normal']))
    Story.append(Spacer(1, 24))
    
    # PART B
    Story.append(Paragraph("PART B: Independent Expert Countersignature", styles['SubTitle']))
    Story.append(Paragraph("I, the undersigned forensic examiner, have verified the cryptographic hash and trace origin of the attached electronic record.", styles['Normal']))
    Story.append(Spacer(1, 48))
    
    # Signature Lines
    sig_data = [
        ["_________________________", "_________________________"],
        ["Device Custodian Signature", "Forensic Examiner Signature"],
        ["Date: ______________", "Date: ______________"]
    ]
    t = Table(sig_data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
    ]))
    Story.append(t)
    
    doc.build(Story)
    return filepath
