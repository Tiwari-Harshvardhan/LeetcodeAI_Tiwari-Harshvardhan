"""
Unit tests for the Dev.to publishing service in devto.py.
Tests use mock_devto_request to avoid real HTTP calls.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class TestPostToPlatform:
    async def test_successful_publish_returns_dict(self, mock_devto_request):
        """Successful publish returns parsed JSON dict."""
        from devto import post_to_platform

        result = await post_to_platform("Two Sum", "# Blog content")
        assert isinstance(result, dict)
        assert result["id"] == 123

    async def test_post_sends_correct_title(self, mock_devto_request):
        """The title is included in the request body."""
        from devto import post_to_platform

        await post_to_platform("Two Sum", "# Blog content")
        call_kwargs = mock_devto_request["request"].call_args[1]
        assert call_kwargs["json"]["article"]["title"] == "LeetCode Solution: Two Sum"

    async def test_post_sends_correct_content(self, mock_devto_request):
        """The markdown content is included in the request body."""
        from devto import post_to_platform

        await post_to_platform("Two Sum", "# Blog content here")
        call_kwargs = mock_devto_request["request"].call_args[1]
        assert (
            "# Blog content here" in (call_kwargs["json"]["article"]["body_markdown"])
        )

    async def test_devto_api_error_raises(self, mock_devto_request):
        """Non-2xx response raises an exception."""
        from devto import post_to_platform

        mock_devto_request["response"].status_code = 500
        mock_devto_request["response"].text = "Internal Server Error"

        with pytest.raises(Exception):
            await post_to_platform("Two Sum", "# Blog content")


class TestNormalizePlatforms:
    def test_defaults_to_devto(self):
        from devto import normalize_platforms

        assert normalize_platforms(None) == ["devto"]

    def test_deduplicates_platforms(self):
        from devto import normalize_platforms

        result = normalize_platforms(["dev.to", "devto"])
        assert result == ["devto"]

    def test_rejects_unknown_provider(self):
        from devto import PublisherError, normalize_platforms

        with pytest.raises(PublisherError):
            normalize_platforms(["wordpress"])


class TestHashnodePublisher:
    """
    Regression tests for issue #50:
    GraphQL error responses (HTTP 200 + 'errors' field) must not be treated
    as successful publishes.

    All tests use mock_hashnode_request to avoid real HTTP calls or API keys.
    """

    # ------------------------------------------------------------------ #
    # Credentials guard                                                    #
    # ------------------------------------------------------------------ #

    def test_missing_credentials_raises_before_http(self, mock_hashnode_request, monkeypatch):
        """PublisherError is raised when env vars are absent; no HTTP call is made."""
        from devto import HashnodePublisher, PublisherError

        monkeypatch.delenv("HASHNODE_TOKEN", raising=False)
        monkeypatch.delenv("HASHNODE_PUBLICATION_ID", raising=False)

        with pytest.raises(PublisherError, match="HASHNODE_TOKEN"):
            HashnodePublisher().publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

        mock_hashnode_request["request"].assert_not_called()

    # ------------------------------------------------------------------ #
    # Happy path                                                           #
    # ------------------------------------------------------------------ #

    def test_successful_publish_returns_url(self, mock_hashnode_request, monkeypatch):
        """Valid GraphQL success response produces PublishResult with status='success'."""
        from devto import HashnodePublisher

        monkeypatch.setenv("HASHNODE_TOKEN", "tok-valid")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub-abc123")

        result = HashnodePublisher().publish(
            "Two Sum", "# content", tags=["leetcode"], published=True
        )

        assert result.status == "success"
        assert result.url == "https://username.hashnode.dev/leetcode-solution-two-sum"
        assert result.platform == "hashnode"

    # ------------------------------------------------------------------ #
    # GraphQL error cases (core regression for issue #50)                 #
    # ------------------------------------------------------------------ #

    def test_graphql_error_raises_publisher_error(self, mock_hashnode_request, monkeypatch):
        """
        HTTP 200 + GraphQL 'errors' field must raise PublisherError, not return success.
        This is the primary regression test for issue #50.
        """
        from devto import HashnodePublisher, PublisherError

        monkeypatch.setenv("HASHNODE_TOKEN", "tok-valid")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub-abc123")

        mock_hashnode_request["response"].json.return_value = {
            "errors": [{"message": "Invalid publication ID"}],
            "data": None,
        }

        with pytest.raises(PublisherError):
            HashnodePublisher().publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    def test_graphql_error_message_is_propagated(self, mock_hashnode_request, monkeypatch):
        """The human-readable GraphQL error message is included in the exception."""
        from devto import HashnodePublisher, PublisherError

        monkeypatch.setenv("HASHNODE_TOKEN", "tok-valid")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub-abc123")

        mock_hashnode_request["response"].json.return_value = {
            "errors": [{"message": "Invalid publication ID"}],
            "data": None,
        }

        with pytest.raises(PublisherError, match="Invalid publication ID"):
            HashnodePublisher().publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    def test_graphql_multiple_errors_uses_first(self, mock_hashnode_request, monkeypatch):
        """When multiple GraphQL errors are returned, the first message is used."""
        from devto import HashnodePublisher, PublisherError

        monkeypatch.setenv("HASHNODE_TOKEN", "tok-valid")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub-abc123")

        mock_hashnode_request["response"].json.return_value = {
            "errors": [
                {"message": "First error"},
                {"message": "Second error"},
            ],
            "data": None,
        }

        with pytest.raises(PublisherError, match="First error"):
            HashnodePublisher().publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    def test_graphql_error_without_message_uses_fallback(self, mock_hashnode_request, monkeypatch):
        """If a GraphQL error object has no 'message' key, a safe fallback is used."""
        from devto import HashnodePublisher, PublisherError

        monkeypatch.setenv("HASHNODE_TOKEN", "tok-valid")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub-abc123")

        mock_hashnode_request["response"].json.return_value = {
            "errors": [{}],  # error dict present but no 'message' key
            "data": None,
        }

        with pytest.raises(PublisherError, match="Unknown Hashnode GraphQL error"):
            HashnodePublisher().publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    def test_empty_errors_list_does_not_raise(self, mock_hashnode_request, monkeypatch):
        """An empty 'errors' list is falsy and must not be treated as a failure."""
        from devto import HashnodePublisher

        monkeypatch.setenv("HASHNODE_TOKEN", "tok-valid")
        monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "pub-abc123")

        mock_hashnode_request["response"].json.return_value = {
            "errors": [],  # present but empty — not an error condition
            "data": {
                "publishPost": {
                    "post": {
                        "id": "hn-post-123",
                        "url": "https://username.hashnode.dev/leetcode-solution-two-sum",
                        "title": "LeetCode Solution: Two Sum",
                    }
                }
            },
        }

        result = HashnodePublisher().publish(
            "Two Sum", "# content", tags=["leetcode"], published=True
        )
        assert result.status == "success"

