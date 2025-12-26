from enum import Enum
from typing import List

from pydantic import BaseModel, Field


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
