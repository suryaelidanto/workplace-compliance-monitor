import pytest
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from app.services import detect_pii


@pytest.mark.asyncio
async def test_pii_detection_quality():
    input_text = "My email is test@example.com"
    result = await detect_pii(input_text)

    test_case = LLMTestCase(input=input_text, actual_output=result.explanation)
    metric = AnswerRelevancyMetric(threshold=0.5)
    metric.measure(test_case)

    assert result.has_pii is True
    assert metric.is_successful()
