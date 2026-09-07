from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class ForensicAIAnalysis(BaseModel):
    fraud_taxonomy: Literal[
        "legitimate", "suspicious", "impersonated", "phishing", "fraud-related"
    ]
    bec_subtype: Literal[
        "payment_diversion", "fake_invoice_request",
        "credential_harvesting", "executive_impersonation", "none"
    ]
    infrastructure_attribution: Literal[
        "compromised_account", "spoofed_domain",
        "anonymized_infrastructure", "direct_malicious_actor"
    ]
    urgency_cues: List[str]          # exact phrases quoted from the email, not paraphrased
    threat_actor_claimed: Optional[str] = None
    requested_action: Optional[str] = None
    technical_justification: str = Field(
        description="Strict 2-sentence rationale citing specific evidence for the attribution flag"
    )
