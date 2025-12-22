"""
AI Compliance Monitor API
Production-grade system for detecting PII leakage and toxic content in workplace communications.

Author: Surya Elidanto
License: MIT
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import OpenAI
import os
from typing import List
from enum import Enum
import dotenv
from concurrent.futures import ThreadPoolExecutor
import time

dotenv.load_dotenv()

app = FastAPI(
    title="AI Compliance Monitor API",
    description="Real-time compliance monitoring for workplace communications",
    version="1.0.0",
    contact={"name": "Surya Elidanto", "url": "https://github.com/suryaelidanto"},
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-4o-mini"
MAX_WORKERS = 2


class SenderRole(str, Enum):
    """Employee role categories for risk assessment"""

    CUSTOMER_SERVICE = "Customer Service"
    SALES = "Sales"
    ENGINEERING = "Engineering"
    MANAGEMENT = "Management"
    HR = "HR"
    FINANCE = "Finance"
    OPERATIONS = "Operations"


class RiskLevel(str, Enum):
    """Risk severity levels"""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PIIDetectionResult(BaseModel):
    """Results from PII detection analysis"""

    has_pii: bool = Field(description="Whether PII was detected in the message")
    pii_types: List[str] = Field(
        description="Types of PII found (e.g., credit_card, ssn, email, phone)"
    )
    risk_level: RiskLevel = Field(description="Risk level for PII exposure")
    explanation: str = Field(description="Brief explanation of findings")


class ToxicityDetectionResult(BaseModel):
    """Results from toxicity detection analysis"""

    is_toxic: bool = Field(description="Whether toxic content was detected")
    toxicity_types: List[str] = Field(
        description="Types of toxicity (e.g., harassment, profanity, discrimination)"
    )
    risk_level: RiskLevel = Field(description="Risk level for brand safety")
    explanation: str = Field(description="Brief explanation of findings")


class MonitorRequest(BaseModel):
    """Request payload for compliance monitoring"""

    message_text: str = Field(
        min_length=1,
        max_length=5000,
        description="The message text to analyze",
        examples=["Customer John Doe, credit card 4532-1234-5678-9010"],
    )
    sender_role: SenderRole = Field(
        description="Role of the message sender", examples=[SenderRole.CUSTOMER_SERVICE]
    )


class MonitorResponse(BaseModel):
    """Response payload with compliance analysis results"""

    pii_detection: PIIDetectionResult
    toxicity_detection: ToxicityDetectionResult
    final_risk_level: RiskLevel
    severity_score: int = Field(
        ge=0, le=100, description="Overall severity score (0=safe, 100=critical)"
    )
    recommended_action: str = Field(
        description="Recommended action based on risk assessment"
    )
    should_flag: bool = Field(
        description="Whether this message should be flagged for review"
    )
    processing_time_ms: int = Field(
        description="Time taken to process the request in milliseconds"
    )


def detect_pii(message: str) -> PIIDetectionResult:
    """
    Detect Personally Identifiable Information (PII) in message text.

    Uses GPT-4o-mini to identify sensitive data including:
        - Credit card numbers
        - Social Security Numbers (SSN)
        - Passport numbers
        - Email addresses
        - Phone numbers
        - Home addresses
        - Passwords

    Args:
        message: The message text to analyze

    Returns:
        PIIDetectionResult with detection findings
    """

    system_prompt = """You are a compliance AI specialized in detecting Personally Identifiable Information (PII).
    
    Your task is to analyze text for the following PII types:
        - Credit card numbers (16 digits, formatted or unformatted)
        - Social Security Numbers (SSN) in format XXX-XX-XXXX
        - Passport numbers
        - Email addresses
        - Phone numbers (any format)
        - Home addresses (street, city, state, zip)
        - Passwords or credentials
    
    Return ONLY valid JSON matching the schema. Be strict in detection.
    """

    user_prompt = f"""Analyze this workplace message for PII:
    
    Message: "{message}"

    Return JSON with:
        - has_pii (boolean): true if any PII detected
        - pii_types (array): list of detected PII types (e.g., ["credit_card", "email"])
        - risk_level (string): safe/low/medium/high/critical based on sensitivity
        - explanation (string): brief explanation of what was found

    Risk level guidelines:
        - critical: SSN, credit card, password
        - high: passport, full address
        - medium: email, phone
        - low: partial info
        - safe: no PII
    """

    try:
        response = client.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=PIIDetectionResult,
            temperature=0.1,
        )

        return response.choices[0].message.parsed

    except Exception as e:
        return PIIDetectionResult(
            has_pii=False,
            pii_types=[],
            risk_level=RiskLevel.SAFE,
            explanation=f"Error during PII detection: {str(e)}",
        )


def detect_toxicity(message: str) -> ToxicityDetectionResult:
    """
    Detect toxic, inappropriate, or policy-violating content.

    Uses GPT-4o-mini to identify:
        - Harassment or bullying
        - Profanity or vulgar language
        - Discrimination (race, gender, religion, etc.)
        - Threats or violence
        - Sexual content
        - Hate speech

    Args:
        message: The message text to analyze

    Returns:
        ToxicityDetectionResult with detection findings
    """

    system_prompt = """You are a brand safety AI specialized in detecting toxic and inappropriate content.
    
    Your task is to analyze text for:
        - Harassment, bullying, or personal attacks
        - Profanity or vulgar language
        - Discrimination (race, gender, religion, age, disability, etc.)
        - Threats or violent language
        - Sexual or inappropriate content
        - Hate speech or extremism

    Return ONLY valid JSON matching the schema. Consider workplace context.
    """

    user_prompt = f"""Analyze this workplace message for toxicity:

    Message: "{message}"

    Return JSON with:
        - is_toxic (boolean): true if toxic content detected
        - toxicity_types (array): list of detected types (e.g., ["harassment", "profanity"])
        - risk_level (string): safe/low/medium/high/critical based on severity
        - explanation (string): brief explanation of what was found

    Risk level guidelines:
        - critical: severe harassment, threats, hate speech
        - high: clear policy violations, discrimination
        - medium: profanity, inappropriate jokes
        - low: borderline unprofessional
        - safe: professional communication
    """

    try:
        response = client.chat.completions.parse(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=ToxicityDetectionResult,
            temperature=0.1,
        )

        return response.choices[0].message.parsed

    except Exception as e:
        return ToxicityDetectionResult(
            is_toxic=False,
            toxicity_types=[],
            risk_level=RiskLevel.SAFE,
            explanation=f"Error during toxicity detection {str(e)}",
        )


def calculate_final_risk(
    pii_result: PIIDetectionResult, toxicity_result: ToxicityDetectionResult
) -> tuple[RiskLevel, int]:
    """
    Calculate unified risk level and severity score.

    Combines results from PII and toxicity detection to determine overall risk level. Uses the higher of the two risk levels.

    Args:
        pii_result: Results from PII detection
        toxicity_result: Results from toxicity detection

    Returns:
        Tuple of (final_risk_level, severity_score)
    """

    risk_scores = {
        RiskLevel.SAFE: 0,
        RiskLevel.LOW: 25,
        RiskLevel.MEDIUM: 50,
        RiskLevel.HIGH: 75,
        RiskLevel.CRITICAL: 100,
    }

    pii_score = risk_scores[pii_result.risk_level]
    toxicity_score = risk_scores[toxicity_result.risk_level]

    final_score = max(pii_score, toxicity_score)

    if final_score >= 75:
        final_risk = RiskLevel.CRITICAL
    elif final_score >= 50:
        final_risk = RiskLevel.HIGH
    elif final_score >= 25:
        final_risk = RiskLevel.MEDIUM
    elif final_score > 0:
        final_risk = RiskLevel.LOW
    else:
        final_risk = RiskLevel.SAFE

    return final_risk, final_score


def get_recommended_action(risk_level: RiskLevel, sender_role: SenderRole) -> str:
    """
    Determine recommended action based on risk level and sender role.

    Actions escalate based on risk severity and are tailored to the sender's role within the organization.

    Args:
        risk_level: The calculated risk level
        sender_role: Role of the message sender

    Returns:
        Human-readable recommended action string
    """

    if risk_level == RiskLevel.CRITICAL:
        return (
            f"IMMEDIATE ACTION REQUIRED: Delete message immediately, "
            f"notify compliance team, suspend {sender_role.value} account pending investigation, "
            f"initiate incident response protocol"
        )

    elif risk_level == RiskLevel.HIGH:
        return (
            f"URGENT: Flag for immediate compliance review, "
            f"notify {sender_role.value} manager, require mandatory training, "
            f"monitor future communications closely"
        )

    elif risk_level == RiskLevel.MEDIUM:
        return (
            f"WARNING: Log incident for audit trail, "
            f"send automated warning to {sender_role.value}, "
            f"escalate if pattern continues"
        )

    elif risk_level == RiskLevel.LOW:
        return (
            "ADVISORY: Log for compliance records, "
            "no immediate action required, monitor for patterns"
        )
    else:
        return "SAFE: No action required, message complies with policies"


@app.post("/monitor-communication", response_model=MonitorResponse)
def monitor_communication(request: MonitorRequest):
    """
    Monitor workplace communication for compliance violations.

    This endpoint performs parallel analysis for:
    1. PII (Personally Identifiable Information) detection
    2. Toxicity and inappropriate content detection

    Returns a unified risk assessment with recommended actions.

    **Use Cases:**
        - Slack/Teams message monitoring
        - Email compliance scanning
        - Customer support quality assurance
        - Internal communication auditing

    **Example Request:**
    ```json
    {
        "message_text": "Customer credit card: 4532-1234-5678-9010",
        "sender_role": "Customer Service"
    }
    ```
    """

    start_time = time.time()

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            pii_future = executor.submit(detect_pii, request.message_text)
            toxicity_future = executor.submit(detect_toxicity, request.message_text)

            pii_result = pii_future.result()
            toxicity_result = toxicity_future.result()

        final_risk, severity_score = calculate_final_risk(pii_result, toxicity_result)
        recommended_action = get_recommended_action(final_risk, request.sender_role)
        should_flag = final_risk in [
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        ]
        processing_time_ms = int((time.time() - start_time) * 1000)

        return MonitorResponse(
            pii_detection=pii_result,
            toxicity_detection=toxicity_result,
            final_risk_level=final_risk,
            severity_score=severity_score,
            recommended_action=recommended_action,
            should_flag=should_flag,
            processing_time_ms=processing_time_ms,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Compliance monitoring failed: {str(e)}"
        )


@app.get("/")
def root():
    """API root endpoint with service information"""

    return {
        "service": "AI Compliance Monitor API",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "monitor": "/monitor-communication",
            "health": "/health",
            "docs": "/docs",
        },
        "description": "Production-grade compliance monitoring for workplace communications",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers"""

    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "max_workers": MAX_WORKERS,
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
