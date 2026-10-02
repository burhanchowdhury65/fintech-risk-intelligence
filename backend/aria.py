from typing import Optional, Any, Awaitable, Callable

from pydantic import BaseModel, Field


from backend.llm_provider import call_llm_with_fallback
from backend.aria_tools import (
    build_aria_decision_prompt,
    parse_aria_decision,
    build_aria_analysis_prompt,
)


class AriaChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    language: str = Field(default="English")
    session_id: Optional[str] = None


class AriaChatResponse(BaseModel):
    reply: str
    provider: str
    session_id: Optional[str] = None
    tool_result: Optional[dict] = None


def generate_aria_decision(
    message: str,
    language: str,
) -> tuple[dict[str, Any], str]:
    """
    Ask the LLM to decide whether the user wants normal chat
    or transaction risk analysis.
    """

    prompt = build_aria_decision_prompt(
        message,
        language,
    )

    result, provider = call_llm_with_fallback(prompt)

    raw_content = result.choices[0].message.content

    decision = parse_aria_decision(raw_content)

    return decision, provider


def generate_aria_reply(
    message: str,
    language: str,
) -> tuple[str, str]:

    decision, provider = generate_aria_decision(
        message,
        language,
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
    )

    if decision["action"] == "chat":
        return (
            decision["reply"],
            provider,
            None,
        )

    arguments = decision.get("arguments", {})

    if not isinstance(arguments, dict):
        raise ValueError(
            "ARIA analysis arguments must be an object"
        )

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