import json
import requests
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from app.models.schemas import ForensicAIAnalysis
from app.core.config import get_settings

from presidio_analyzer.nlp_engine import NlpEngineProvider

# Configure Presidio to use the small spacy model to prevent OOM errors
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
anonymizer = AnonymizerEngine()

def scrub_pii(text: str) -> str:
    """
    Scrubs PII (financial/ID data) from text before sending to LLM.
    Uses Microsoft Presidio NLP-based redaction.
    """
    if not text:
        return ""
    
    # Analyze text for entities
    # Note: For India specific (PAN, Aadhaar) we might need custom recognizers, 
    # but for this build we'll use Presidio's built-in + basic regex if needed.
    # In a real build, we'd add PatternRecognizer for Aadhaar/PAN.
    results = analyzer.analyze(text=text, entities=["CREDIT_CARD", "CRYPTO", "EMAIL_ADDRESS", "IBAN_CODE", "IP_ADDRESS", "PHONE_NUMBER", "US_BANK_NUMBER", "US_SSN"], language='en')
    
    # Anonymize text
    anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
    return anonymized_result.text

def analyze_email_with_llm(scrubbed_body: str) -> ForensicAIAnalysis:
    """
    Sends scrubbed email body to local Ollama (qwen2.5:3b) with schema-constrained JSON output.
    """
    settings = get_settings()
    
    prompt = f"""
    Analyze the following email body for a digital forensics investigation.
    Extract the required fields exactly as specified in the JSON schema.
    
    IMPORTANT INSTRUCTION for 'technical_justification':
    You must provide a strict 2-sentence rationale citing specific evidence from the email for the attribution flag. Do not just output a single word or phrase.
    
    Email Body:
    {scrubbed_body}
    """
    
    schema = ForensicAIAnalysis.model_json_schema()
    
    payload = {
        "model": "qwen2.5:3b",
        "prompt": prompt,
        "format": schema,
        "stream": False,
        "temperature": 0.0
    }
    
    try:
        response = requests.post(f"{settings.OLLAMA_HOST}/api/generate", json=payload)
        response.raise_for_status()
        result_json = response.json().get("response", "{}")
        
        # Parse the output with Pydantic to ensure schema compliance
        parsed_result = ForensicAIAnalysis.model_validate_json(result_json)
        return parsed_result
    except Exception as e:
        print(f"LLM Error: {e}")
        if 'result_json' in locals():
            print(f"Raw LLM Output: {result_json}")
        # Fallback if the LLM fails or doesn't return valid JSON
        # In a real environment, we'd log this and maybe retry.
        return ForensicAIAnalysis(
            fraud_taxonomy="suspicious",
            bec_subtype="none",
            infrastructure_attribution="anonymized_infrastructure",
            urgency_cues=[],
            threat_actor_claimed=None,
            requested_action=None,
            technical_justification="LLM parsing failed or timed out. Defaulting to suspicious pending human review."
        )
