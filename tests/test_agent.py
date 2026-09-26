import pytest

from agent.email_agent import EmailAgent
from agent.parser import parse_email_response


class DummyResponse:
    def __init__(self, payload):
        self.output_text = payload


def test_generate_email_returns_structure(monkeypatch):
    agent = EmailAgent(api_key="test-key", model="gpt-4.1-mini")

    class DummyClient:
        class responses:
            @staticmethod
            def create(**kwargs):
                return DummyResponse('{"subject": "Internship Application", "body": "Dear Hiring Manager,\\n\\nThank you for your time.\\n\\nRegards,\\nStudent"}')

    monkeypatch.setattr(agent, "client", DummyClient())

    result = agent.generate_email("Write an email for a data analyst internship")

    assert result["subject"] == "Internship Application"
    assert "Dear Hiring Manager" in result["body"]


def test_parse_email_response_extracts_subject_and_body():
    payload = '{"subject": "Follow-Up Application", "body": "Dear Team,\\n\\nI am following up."}'
    parsed = parse_email_response(payload)

    assert parsed["subject"] == "Follow-Up Application"
    assert "following up" in parsed["body"]


def test_validate_recipient_rejects_invalid_email():
    agent = EmailAgent(api_key="test-key", model="gpt-4.1-mini")

    assert agent.validate_recipient("not-an-email") is False
    assert agent.validate_recipient("user@example.com") is True


def test_validate_request_rejects_empty_input():
    agent = EmailAgent(api_key="test-key", model="gpt-4.1-mini")

    assert agent.validate_request("") is False
    assert agent.validate_request("Write a concise follow-up email") is True
