import json
import re


def parse_email_response(raw_response: str):
    if not raw_response:
        raise ValueError("AI response was empty.")

    text = str(raw_response).strip()

    if text.startswith("{"):
        try:
            payload = json.loads(text)
            if isinstance(payload, dict):
                subject = str(payload.get("subject") or "").strip()
                body = str(payload.get("body") or "").strip()
                if subject and body:
                    return {"subject": subject, "body": body}
        except json.JSONDecodeError:
            pass

    subject_match = re.search(r"SUBJECT\s*[:\-]\s*(.+)", text, re.IGNORECASE)
    body_match = re.search(r"BODY\s*[:\-]\s*(.*)", text, re.IGNORECASE | re.DOTALL)

    if subject_match or body_match:
        subject = subject_match.group(1).strip() if subject_match else "AI Generated Email"
        body = body_match.group(1).strip() if body_match else text
        return {"subject": subject, "body": body}

    lines = text.splitlines()
    if len(lines) >= 2:
        subject = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        if subject and body:
            return {"subject": subject, "body": body}

    raise ValueError("AI response did not contain a valid subject and body.")
