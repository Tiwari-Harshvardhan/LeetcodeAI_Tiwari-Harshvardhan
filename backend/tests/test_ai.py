import re

import pytest
from dotenv import load_dotenv

from ai.provider_manager import ProviderManager

load_dotenv()


@pytest.mark.parametrize(
    "provider_name",
    [
        "gemini",
        "openai",
        "perplexity",
    ],
)
def test_provider_generation(
    monkeypatch,
    provider_name,
):
    """
    Test that each provider generates
    a valid response about Python.
    """

    monkeypatch.setenv(
        "AI_PROVIDER",
        provider_name,
    )

    manager = ProviderManager()

    response = manager.generate(
        "Write one short sentence about Python."
    )

    print(f"\n[{provider_name}] Response: {response}")

    # basic validation
    assert isinstance(response, str)
    assert response.strip() != ""
    assert len(response.strip()) > 10

    # content validation
    assert re.search(
        r"\bpython\b",
        response,
        re.IGNORECASE,
    ), f"{provider_name} response does not mention Python"

    # common API/auth errors should fail
    error_patterns = [
        r"invalid api key",
        r"unauthorized",
        r"authentication",
        r"rate limit",
        r"quota",
        r"forbidden",
        r"error",
        r"failed",
    ]

    for pattern in error_patterns:
        assert not re.search(
            pattern,
            response,
            re.IGNORECASE,
        ), (
            f"{provider_name} returned an error response: "
            f"{response}"
        )