import json
from typing import Any


def build_aria_decision_prompt(
    message: str,
    language: str,
) -> str:
    return f"""
You are ARIA, a financial risk intelligence assistant.

Your job is to decide whether the user's message is:
1. A normal conversational question, or
2. A request to analyze a financial transaction.

User language:
{language}

User message:
{message}

If the user is NOT asking for transaction risk/fraud analysis,
return ONLY valid JSON in this exact structure:

{{
  "action": "chat",
  "reply": "your concise answer"
}}

If the user IS asking for transaction risk/fraud analysis,
extract ONLY the transaction fields that are explicitly available.

Return ONLY valid JSON in this exact structure:

{{
  "action": "analyze_transaction",
  "arguments": {{
    "transaction_amount": null,
    "transaction_type": null,
    "merchant_category": null,
    "transaction_time": null,
    "distance_from_home": null,
    "location": null
  }}
}}

Rules:
- Do not invent missing transaction values.
- Use null for fields that are not provided.
- transaction_amount must be a number if provided.
- distance_from_home must be a number if provided.
- transaction_time should be an ISO 8601 datetime string if provided.
- Do not invent risk scores or fraud results.
- Return JSON only.
"""


def parse_aria_decision(raw_content: str) -> dict[str, Any]:
    """
    Parse the LLM's JSON decision safely.
    """

    content = raw_content.strip()

    # Handle accidental markdown code fences.
    if content.startswith("```"):
        content = content.replace("```json", "", 1)
        content = content.replace("```", "", 1)
        content = content.strip()

    decision = json.loads(content)

    if not isinstance(decision, dict):
        raise ValueError("ARIA decision must be a JSON object")

    action = decision.get("action")

    if action not in {
        "chat",
        "analyze_transaction",
    }:
        raise ValueError("Invalid ARIA action")

    return decision


def build_aria_analysis_prompt(
    message: str,
    analysis_result: dict[str, Any],
    language: str,
) -> str:
    return f"""
You are ARIA, a financial risk intelligence assistant.

The user asked:
{message}

The backend has performed the transaction analysis.

Verified analysis result:
{json.dumps(analysis_result, ensure_ascii=False)}

Explain the result to the user in {language}.

Important rules:
- Treat the analysis result above as authoritative.
- Do not change or invent risk_score, risk_status, is_fraud,
  model_version, or model_factors.
- Clearly explain the result in simple language.
- If model_factors are present, explain them.
- Do not claim that the model is medically, legally, or financially
  certain.
- Do not expose internal implementation details unnecessarily.

Return only the response text.
"""