"""
AI Compliance Monitor API
Production-grade system for detecting PII leakage and toxic content in workplace communications.

Author: Surya Elidanto
License: MIT
"""

import asyncio
import time
import os

import dotenv
from fastapi import FastAPI, HTTPException

from .models import MonitorRequest, MonitorResponse

from .services import (
    RiskLevel,
    calculate_final_risk,
    detect_pii,
    detect_toxicity,
    get_recommended_action,
    MODEL_NAME,
)

dotenv.load_dotenv()

app = FastAPI(
    title="AI Compliance Monitor API",
    description="Real-time compliance monitoring for workplace communications",
    version="1.0.0",
    contact={"name": "Surya Elidanto", "url": "https://github.com/suryaelidanto"},
)


@app.post("/monitor-communication", response_model=MonitorResponse)
async def monitor_communication(request: MonitorRequest):
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
        pii_result, toxicity_result = await asyncio.gather(
            detect_pii(request.message_text), detect_toxicity(request.message_text)
        )

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
async def root():
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
async def health_check():
    """Health check endpoint for monitoring and load balancers"""

    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
