import hashlib
import email
from email import policy
from email.message import EmailMessage
from datetime import datetime, timezone
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, Any, List

URL_SHORTENERS = {'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd', 'buff.ly'}
SUSPICIOUS_EXTENSIONS = {'.exe', '.scr', '.js', '.vbs', '.bat', '.cmd', '.jar', '.docm', '.xlsm', '.pptm'}
ELEVATED_RISK_TLDS = {'.zip', '.xyz', '.top', '.club', '.work'}

IP_LITERAL_REGEX = re.compile(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

def compute_hash(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()

def extract_urls(html_content: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html_content, 'html.parser')
    urls = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        display_text = a_tag.get_text(strip=True)
        
        flags = []
        parsed_url = urlparse(href)
        domain = parsed_url.netloc.lower()
        
        # Check shorteners
        if domain in URL_SHORTENERS:
            flags.append("url_shortener")
            
        # Check IP literal
        if IP_LITERAL_REGEX.match(href):
            flags.append("ip_literal")
            
        # Check suspicious TLDs
        if any(domain.endswith(tld) for tld in ELEVATED_RISK_TLDS):
            flags.append("suspicious_tld")
            
        # Check mismatch
        if display_text:
            # If the display text looks like a domain or URL but doesn't match the href domain
            display_parsed = urlparse(display_text if display_text.startswith('http') else 'http://' + display_text)
            display_domain = display_parsed.netloc.lower()
            if display_domain and '.' in display_domain and display_domain != domain:
                flags.append("display_href_mismatch")
                
        urls.append({
            "url": href,
            "display_text": display_text,
            "domain": domain,
            "flags": flags
        })
        
    return urls

def extract_attachments(msg: EmailMessage) -> List[Dict[str, Any]]:
    attachments = []
    for part in msg.iter_attachments():
        filename = part.get_filename()
        if filename:
            ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
            flags = []
            if ext in SUSPICIOUS_EXTENSIONS:
                flags.append("executable_or_script")
                
            # Special case for HTML with embedded forms
            if ext in {'.htm', '.html'}:
                content = part.get_payload(decode=True)
                if content:
                    try:
                        decoded_content = content.decode('utf-8', errors='ignore')
                        if '<form' in decoded_content.lower():
                            flags.append("html_with_form")
                    except Exception:
                        pass
                        
            attachments.append({
                "filename": filename,
                "extension": ext,
                "flags": flags
            })
    return attachments

def parse_eml(raw_bytes: bytes) -> Dict[str, Any]:
    # 1. Hashing and timestamp
    file_hash = compute_hash(raw_bytes)
    ingested_at = datetime.now(timezone.utc).isoformat()
    
    # 2. Parse RFC 822
    msg = email.message_from_bytes(raw_bytes, policy=policy.default)
    
    metadata = {
        "subject": msg.get("Subject", ""),
        "from": msg.get("From", ""),
        "to": msg.get("To", ""),
        "date": msg.get("Date", "")
    }
    
    headers = {
        "received": msg.get_all("Received", []),
        "message_id": msg.get("Message-ID", ""),
        "reply_to": msg.get("Reply-To", ""),
        "return_path": msg.get("Return-Path", ""),
        "authentication_results": msg.get("Authentication-Results", "")
    }
    
    # Extract body
    body_text = ""
    html_content = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    body_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    html_content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        content_type = msg.get_content_type()
        if content_type == "text/plain":
            body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        elif content_type == "text/html":
            html_content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
    # If we only have HTML, strip it for the raw text
    if html_content and not body_text:
        soup = BeautifulSoup(html_content, 'html.parser')
        body_text = soup.get_text(separator=' ', strip=True)
        
    # 3. IoC Extraction
    urls = extract_urls(html_content) if html_content else extract_urls(body_text) # Fallback to regex if plain text only? Simplified here.
    attachments = extract_attachments(msg)
    
    return {
        "ingestion": {
            "hash_sha256": file_hash,
            "timestamp": ingested_at
        },
        "metadata": metadata,
        "headers": headers,
        "body_text": body_text,
        "iocs": {
            "urls": urls,
            "attachments": attachments
        }
    }
