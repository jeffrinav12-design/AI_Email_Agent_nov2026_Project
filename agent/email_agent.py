import json
import os
import re
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from .parser import parse_email_response
from .prompts import EMAIL_SYSTEM_PROMPT, build_email_request

load_dotenv()


class EmailAgent:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.client = OpenAI(api_key=self.api_key)

    def validate_recipient(self, recipient: str) -> bool:
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return bool(recipient and re.match(pattern, recipient.strip()))

    def validate_request(self, request: str) -> bool:
        return bool((request or "").strip())

    def generate_email(self, request: str, tone: str = "Professional") -> Dict[str, str]:
        if not self.validate_request(request):
            raise ValueError("Please enter an email request before generating.")

        response = self.client.responses.create(
            model=self.model,
            instructions=EMAIL_SYSTEM_PROMPT,
            input=build_email_request(request, tone),
        )

        raw_text = getattr(response, "output_text", "")
        if not raw_text:
            raise ValueError("OpenAI returned an empty response.")

        data = parse_email_response(raw_text)
        if not data.get("subject") or not data.get("body"):
            raise ValueError("Invalid AI response received.")

        return {
            "subject": data["subject"].strip(),
            "body": data["body"].strip(),
        }

    def rewrite_email(self, current_body: str, instruction: str, tone: str = "Professional") -> Dict[str, str]:
        if not current_body.strip():
            raise ValueError("Current email body is empty.")
        if not self.validate_request(instruction):
            raise ValueError("Please describe the change you want to make.")

        response = self.client.responses.create(
            model=self.model,
            instructions=EMAIL_SYSTEM_PROMPT,
            input=(
                f"Rewrite the email based on this instruction: {instruction}\n"
                f"Current email:\n{current_body}\n"
                f"Tone: {tone}\n"
                "Return JSON only with keys: subject and body."
            ),
        )

        return parse_email_response(getattr(response, "output_text", ""))
