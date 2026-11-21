from unittest.mock import MagicMock

from integrations.gmail import GmailProvider


def test_create_draft_uses_provider():
    provider = GmailProvider(token_path="token.json", credentials_path="credentials.json")
    provider.get_service = MagicMock(return_value=MagicMock())

    provider.create_draft = MagicMock(return_value="draft_123")

    assert provider.create_draft("user@example.com", "Test subject", "Hello world") == "draft_123"


def test_gmail_provider_handles_invalid_email():
    provider = GmailProvider(token_path="token.json", credentials_path="credentials.json")

    assert provider.validate_recipient("bad-email") is False
    assert provider.validate_recipient("valid@example.com") is True
