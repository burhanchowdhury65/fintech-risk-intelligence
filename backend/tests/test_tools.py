import asyncio

import pytest

from backend.tools import (
    ALLOWED_TOOLS,
    dispatch_tool,
    is_allowed_tool,
    validate_tool_input_types,
    validate_tool_output,
)


def test_allowed_tools_are_explicit():
    assert ALLOWED_TOOLS == {
        "analyze_transaction",
        "health/status",
    }


def test_allowed_tool_check():
    assert is_allowed_tool("analyze_transaction")
    assert is_allowed_tool("health/status")


def test_unsupported_tool_is_rejected():
    assert not is_allowed_tool("delete_transaction")


def test_dispatch_allowed_tools():
    async def analyze_transaction(**kwargs):
        return {
            "is_fraud": False,
            "risk_score": 25.0,
            "risk_status": "low",
            "model_factors": [],
            "model_version": "baseline-v1",
        }

    async def health_status(**kwargs):
        return {
            "status": "ok",
            "service": "fintech-risk-intelligence-api",
        }

    handlers = {
        "analyze_transaction": analyze_transaction,
        "health/status": health_status,
    }

    async def run():
        result = await dispatch_tool(
            "analyze_transaction",
            handlers,
            transaction_amount=100,
            transaction_type="purchase",
            merchant_category="grocery",
        )

        assert result["is_fraud"] is False
        assert result["risk_score"] == 25.0
        assert result["risk_status"] == "low"
        assert result["model_version"] == "baseline-v1"

        result = await dispatch_tool(
            "health/status",
            handlers,
        )

        assert result == {
            "status": "ok",
            "service": "fintech-risk-intelligence-api",
        }

    asyncio.run(run())


def test_dispatch_rejects_unsupported_tool():
    async def handler(**kwargs):
        return {}

    handlers = {
        "analyze_transaction": handler,
    }

    async def run():
        with pytest.raises(ValueError, match="Tool not allowed"):
            await dispatch_tool(
                "delete_transaction",
                handlers,
            )

    asyncio.run(run())


def test_dispatch_rejects_missing_handler():
    async def run():
        with pytest.raises(ValueError, match="No handler registered"):
            await dispatch_tool(
                "analyze_transaction",
                {},
            )

    asyncio.run(run())


def test_input_schema_accepts_valid_input():
    validate_tool_input_types(
        "analyze_transaction",
        {
            "transaction_amount": 100,
            "transaction_type": "purchase",
            "merchant_category": "grocery",
        },
    )


def test_input_schema_rejects_wrong_type():
    with pytest.raises(ValueError, match="Invalid type"):
        validate_tool_input_types(
            "analyze_transaction",
            {
                "transaction_amount": "one hundred",
            },
        )


def test_input_schema_rejects_non_object():
    with pytest.raises(
        ValueError,
        match="Tool input must be an object",
    ):
        validate_tool_input_types(
            "analyze_transaction",
            [],
        )


def test_output_schema_accepts_valid_result():
    validate_tool_output(
        "analyze_transaction",
        {
            "is_fraud": False,
            "risk_score": 25.0,
            "risk_status": "low",
            "model_factors": [],
            "model_version": "baseline-v1",
        },
    )


def test_output_schema_rejects_missing_field():
    with pytest.raises(
        ValueError,
        match="Missing output fields",
    ):
        validate_tool_output(
            "analyze_transaction",
            {
                "is_fraud": False,
                "risk_score": 25.0,
                "risk_status": "low",
                "model_factors": [],
            },
        )


def test_output_schema_rejects_wrong_type():
    with pytest.raises(
        ValueError,
        match="Invalid output type",
    ):
        validate_tool_output(
            "analyze_transaction",
            {
                "is_fraud": "false",
                "risk_score": 25.0,
                "risk_status": "low",
                "model_factors": [],
                "model_version": "baseline-v1",
            },
        )


def test_dispatch_rejects_invalid_input_type():
    async def analyze_transaction(**kwargs):
        return {
            "is_fraud": False,
            "risk_score": 25.0,
            "risk_status": "low",
            "model_factors": [],
            "model_version": "baseline-v1",
        }

    handlers = {
        "analyze_transaction": analyze_transaction,
    }

    async def run():
        with pytest.raises(
            ValueError,
            match="Invalid type",
        ):
            await dispatch_tool(
                "analyze_transaction",
                handlers,
                transaction_amount="one hundred",
            )

    asyncio.run(run())


def test_dispatch_rejects_invalid_tool_output():
    async def analyze_transaction(**kwargs):
        return {
            "is_fraud": "false",
            "risk_score": 25.0,
            "risk_status": "low",
            "model_factors": [],
            "model_version": "baseline-v1",
        }

    handlers = {
        "analyze_transaction": analyze_transaction,
    }

    async def run():
        with pytest.raises(
            ValueError,
            match="Invalid output type",
        ):
            await dispatch_tool(
                "analyze_transaction",
                handlers,
                transaction_amount=100,
            )

    asyncio.run(run())
