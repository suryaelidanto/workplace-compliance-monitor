from openai import AsyncOpenAI
import os
from .models import PIIDetectionResult, ToxicityDetectionResult, RiskLevel, SenderRole


client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-4o-mini"


async def detect_pii(message: str) -> PIIDetectionResult:
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
        response = await client.chat.completions.parse(
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


async def detect_toxicity(message: str) -> ToxicityDetectionResult:
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
        response = await client.chat.completions.parse(
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
