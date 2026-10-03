from typing import Optional, Any, Awaitable, Callable

from pydantic import BaseModel, Field


from backend.llm_provider import call_llm_with_fallback
from backend.aria_tools import (
    build_aria_decision_prompt,
    parse_aria_decision,
    build_aria_analysis_prompt,
)


def _normalize_transaction_time(arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a time-only transaction_time such as '03:15'
    into an ISO datetime string accepted by the ML node.

    Full ISO datetime values are left unchanged.
    """
    normalized = dict(arguments)

    value = normalized.get("transaction_time")

    if isinstance(value, str):
        value = value.strip()

        # Only normalize HH:MM or HH:MM:SS.
        if len(value) in (5, 8):
            parts = value.split(":")

            if (
                len(parts) in (2, 3)
                and all(part.isdigit() for part in parts)
            ):
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) == 3 else 0

                if (
                    0 <= hour <= 23
                    and 0 <= minute <= 59
                    and 0 <= second <= 59
                ):
                    normalized["transaction_time"] = (
                        f"2026-01-01T{hour:02d}:{minute:02d}:{second:02d}"
                    )

    return normalized


class AriaChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    language: str = Field(default="English")
    session_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class AriaChatResponse(BaseModel):
    reply: str
    provider: str
    session_id: Optional[str] = None
    tool_result: Optional[dict] = None


def generate_aria_decision(
    message: str,
    language: str,
    context: Optional[dict[str, Any]] = None,
) -> tuple[dict[str, Any], str]:
    """
    Ask the LLM to decide whether the user wants normal chat
    or transaction risk analysis.
    """

    prompt = build_aria_decision_prompt(
        message,
        language,
        context,
    )

    result, provider = call_llm_with_fallback(prompt)

    raw_content = result.choices[0].message.content

    decision = parse_aria_decision(raw_content)

    return decision, provider


def generate_aria_reply(
    message: str,
    language: str,
    context: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:

    decision, provider = generate_aria_decision(
        message,
        language,
        context,
    )

    if decision["action"] == "chat":
        return decision["reply"], provider

    raise ValueError(
        "ARIA requested transaction analysis, "
        "but the transaction analysis tool has not been connected yet."
    )


def generate_aria_analysis_reply(
    message: str,
    analysis_result: dict[str, Any],
    language: str,
) -> tuple[str, str]:
    """
    Convert a verified transaction analysis result
    into a user-friendly ARIA response.
    """

    prompt = build_aria_analysis_prompt(
        message,
        analysis_result,
        language,
    )

    result, provider = call_llm_with_fallback(prompt)

    reply = result.choices[0].message.content

    return reply, provider

async def handle_aria_message(
    message: str,
    language: str,
    analyze_tool: Callable[..., Awaitable[dict[str, Any]]],
    context: Optional[dict[str, Any]] = None,
) -> tuple[str, str, Optional[dict[str, Any]]]:
    """
    Main ARIA orchestration layer.

    ARIA first decides whether the message is normal conversation
    or requires transaction analysis.

    If analysis is requested, the existing backend analysis tool
    is executed through the injected handler.
    """

    decision, provider = generate_aria_decision(
        message,
        language,
        context,
    )

    if decision["action"] == "explain_current_result":
        existing_result = None

        if isinstance(context, dict):
            existing_result = context.get("result")

        if not isinstance(existing_result, dict):
            return (
                "There is no current transaction result to explain. Please analyze a transaction first.",
                provider,
                None,
            )

        reply, analysis_provider = generate_aria_analysis_reply(
            message,
            existing_result,
            language,
        )

        return (
            reply,
            analysis_provider,
            existing_result,
        )

    if decision["action"] == "chat":
        existing_result = None
        if isinstance(context, dict):
            existing_result = context.get("result")

        return (
            decision["reply"],
            provider,
            existing_result,
        )

    arguments = decision.get("arguments", {})

    if not isinstance(arguments, dict):
        raise ValueError(
            "ARIA analysis arguments must be an object"
        )

    arguments = _normalize_transaction_time(arguments)

    analysis_result = await analyze_tool(
        **arguments
    )

    reply, analysis_provider = generate_aria_analysis_reply(
        message,
        analysis_result,
        language,
    )

    return (
        reply,
        analysis_provider,
        analysis_result,
    )