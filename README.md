# workplace-compliance-monitor

Real-time AI compliance monitoring for workplace communications detecting PII leakage and toxic content. Built with FastAPI, OpenAI, and Pydantic.

## Features

- **PII Detection**: Identifies credit cards, SSNs, emails, phone numbers, and addresses.
- **Toxicity Analysis**: Detects harassment, profanity, discrimination, and threats.
- **Risk Assessment**: Calculates unified risk levels and severity scores.
- **Action Recommendations**: Provides role-based automated action suggestions.

## Setup

This project uses `uv` for dependency management.

1. **Clone the repository**
   ```bash
   git clone https://github.com/suryaelidanto/workplace-compliance-monitor.git
   cd workplace-compliance-monitor
   ```

2. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

## Running the Server

Start the API server using uvicorn:

```bash
uv run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.
A Swagger UI for interactive documentation is available at `http://localhost:8000/docs`.

## Endpoint: /monitor-communication

**Method:** `POST`

### Example 1: PII Detection (Critical Risk)

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/monitor-communication" \
-H "Content-Type: application/json" \
-d '{
    "message_text": "Hey, can you process the refund for card 4532-1234-5678-9010 immediately?",
    "sender_role": "Customer Service"
}'
```

**Response:**
```json
{
  "pii_detection": {
    "has_pii": true,
    "pii_types": [
      "credit_card"
    ],
    "risk_level": "critical",
    "explanation": "A credit card number was detected in the message."
  },
  "toxicity_detection": {
    "is_toxic": false,
    "toxicity_types": [],
    "risk_level": "safe",
    "explanation": "The message is a straightforward request for processing a refund and does not contain any toxic or inappropriate content."
  },
  "final_risk_level": "critical",
  "severity_score": 100,
  "recommended_action": "IMMEDIATE ACTION REQUIRED: Delete message immediately, notify compliance team, suspend Customer Service account pending investigation, initiate incident response protocol",
  "should_flag": true,
  "processing_time_ms": 9382
}
```

### Example 2: Toxicity Detection (Harassment)

**Request:**
```bash
curl -X POST "http://127.0.0.1:8000/monitor-communication" \
-H "Content-Type: application/json" \
-d '{
    "message_text": "You are complete trash and useless at your job.",
    "sender_role": "Management"
}'
```

**Response:**
```json
{
  "pii_detection": {
    "has_pii": false,
    "pii_types": [],
    "risk_level": "safe",
    "explanation": "No PII detected in the message."
  },
  "toxicity_detection": {
    "is_toxic": true,
    "toxicity_types": [
      "harassment"
    ],
    "risk_level": "high",
    "explanation": "The message contains a personal attack, labeling the recipient as 'trash' and 'useless', which constitutes severe harassment."
  },
  "final_risk_level": "critical",
  "severity_score": 75,
  "recommended_action": "IMMEDIATE ACTION REQUIRED: Delete message immediately, notify compliance team, suspend Management account pending investigation, initiate incident response protocol",
  "should_flag": true,
  "processing_time_ms": 2876
}
```
