import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

load_dotenv()


PRIMARY_PROVIDER = "groq"
SECONDARY_PROVIDER = "openai"


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    return Groq(api_key=api_key)


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    return OpenAI(api_key=api_key)


def call_primary_llm(prompt: str) -> Any:
    client = get_groq_client()

    return client.chat.completions.create(
       model="openai/gpt-oss-20b",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )


def call_secondary_llm(prompt: str) -> Any:
    client = get_openai_client()

    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )


def call_llm_with_fallback(prompt: str) -> tuple[Any, str]:
    """
    Call the primary LLM first.
    If it fails, automatically switch to the secondary provider.
    """

    try:
        result = call_primary_llm(prompt)
        return result, PRIMARY_PROVIDER

    except Exception:
        result = call_secondary_llm(prompt)
        return result, SECONDARY_PROVIDER
