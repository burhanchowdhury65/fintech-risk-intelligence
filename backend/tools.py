import asyncio
from typing import Any, Awaitable, Callable


ALLOWED_TOOLS = {
    "analyze_transaction",
    "health/status",
}


ToolHandler = Callable[..., Awaitable[Any]]


def is_allowed_tool(tool_name: str) -> bool:
    """Return True only when the tool is explicitly allow-listed."""
    return tool_name in ALLOWED_TOOLS


def require_allowed_tool(tool_name: str) -> None:
    """Reject any tool that is not explicitly allow-listed."""
    if not is_allowed_tool(tool_name):
        raise ValueError(f"Tool not allowed: {tool_name}")


REQUIRED_TOOL_INPUTS = {
    "analyze_transaction": set(),
    "health/status": set(),
}


def validate_tool_input(
    tool_name: str,
    payload: dict[str, Any],
) -> None:
    """Validate the basic input contract for an allow-listed tool."""

    require_allowed_tool(tool_name)

    if not isinstance(payload, dict):
        raise ValueError("Tool input must be an object")

    required_fields = REQUIRED_TOOL_INPUTS[tool_name]

    missing_fields = required_fields - payload.keys()

    if missing_fields:
        raise ValueError(
            f"Missing required fields: {sorted(missing_fields)}"
        )


TOOL_INPUT_TYPES = {
    "analyze_transaction": {
        "transaction_amount": (int, float, type(None)),
        "transaction_type": (str, type(None)),
        "merchant_category": (str, type(None)),
        "transaction_time": (str, type(None)),
        "distance_from_home": (int, float, type(None)),
        "location": (
            dict,
            list,
            str,
            int,
            float,
            bool,
            type(None),
        ),
        "simulate_timeout": (bool,),
        "simulate_unavailable": (bool,),
    },
    "health/status": {},
}


def validate_tool_input_types(
    tool_name: str,
    payload: dict[str, Any],
) -> None:
    """Validate individual input field types."""

    validate_tool_input(tool_name, payload)

    expected_types = TOOL_INPUT_TYPES[tool_name]

    for field, value in payload.items():
        if field not in expected_types:
            continue

        if not isinstance(value, expected_types[field]):
            expected = expected_types[field]

            raise ValueError(
                f"Invalid type for '{field}': "
                f"expected {expected}, "
                f"got {type(value).__name__}"
            )


REQUIRED_TOOL_OUTPUTS = {
    "analyze_transaction": {
        "is_fraud": bool,
        "risk_score": (int, float),
        "risk_status": str,
        "model_factors": list,
        "model_version": str,
    },
    "health/status": {
        "status": str,
        "service": str,
    },
}


def validate_tool_output(
    tool_name: str,
    result: Any,
) -> None:
    """Validate the structured output returned by an allowed tool."""

    require_allowed_tool(tool_name)

    if not isinstance(result, dict):
        raise ValueError("Tool output must be an object")

    expected_fields = REQUIRED_TOOL_OUTPUTS[tool_name]

    missing_fields = set(expected_fields) - result.keys()

    if missing_fields:
        raise ValueError(
            f"Missing output fields: {sorted(missing_fields)}"
        )

    for field, expected_type in expected_fields.items():
        value = result[field]

        if not isinstance(value, expected_type):
            raise ValueError(
                f"Invalid output type for '{field}': "
                f"expected {expected_type}, "
                f"got {type(value).__name__}"
            )


async def dispatch_tool(
    tool_name: str,
    handlers: dict[str, ToolHandler],
    **kwargs: Any,
) -> Any:
    """
    Execute an explicitly allow-listed tool with
    input and output schema validation.
    """

    # 1. Tool must be allow-listed.
    require_allowed_tool(tool_name)

    # 2. Validate input before executing the handler.
    validate_tool_input_types(
        tool_name,
        kwargs,
    )

    # 3. Find the registered handler.
    handler = handlers.get(tool_name)

    if handler is None:
        raise ValueError(
            f"No handler registered for tool: {tool_name}"
        )

    # 4. Execute the tool.
    result = await handler(**kwargs)

    # 5. Validate the structured output.
    validate_tool_output(
        tool_name,
        result,
    )

    # 6. Return only validated output.
    return result


RETRY_MAX_ATTEMPTS = 2
RETRY_DELAY_SECONDS = 0.1


async def retry_async(
    operation: Callable[[], Awaitable[Any]],
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    delay_seconds: float = RETRY_DELAY_SECONDS,
) -> Any:
    """
    Retry an async operation a bounded number of times.

    The operation is attempted at most max_attempts times.
    """
    last_error = None

    for attempt in range(max_attempts):
        try:
            return await operation()

        except Exception as exc:
            last_error = exc

            if attempt == max_attempts - 1:
                raise

            await asyncio.sleep(delay_seconds)

    raise last_error
