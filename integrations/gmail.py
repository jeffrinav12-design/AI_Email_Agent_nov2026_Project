import base64
import os
import re
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class EmailProvider:
    def create_draft(self, to: str, subject: str, body: str):
        raise NotImplementedError

    def send_email(self, to: str, subject: str, body: str):
        raise NotImplementedError

    def get_messages(self):
        raise NotImplementedError


class GmailProvider(EmailProvider):
    SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

    def __init__(self, token_path: str = "token.json", credentials_path: str = "credentials.json", user_email: str = "default", token_dir: str = "tokens"):
        self.credentials_path = credentials_path
        self.user_email = user_email or "default"
        self.token_dir = token_dir
        self.token_path = self._resolve_token_path(token_path, user_email, token_dir)

    def _resolve_token_path(self, token_path: str, user_email: str, token_dir: str):
        if token_path and token_path != "token.json":
            return token_path

        safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(user_email or "default")).strip("_") or "default"
        directory = os.path.join(os.getcwd(), token_dir)
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, f"{safe_name}.json")

    def set_user(self, user_email: str):
        self.user_email = user_email or "default"
        self.token_path = self._resolve_token_path("token.json", self.user_email, self.token_dir)
        return self.token_path

    def list_connected_accounts(self):
        directory = os.path.join(os.getcwd(), self.token_dir)
        if not os.path.exists(directory):
            return []
        accounts = []
        for filename in sorted(os.listdir(directory)):
            if filename.endswith(".json"):
                accounts.append(filename[:-5])
        return accounts

    def validate_recipient(self, recipient: str) -> bool:
        return bool(recipient and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", recipient.strip()))

    def get_service(self):
        creds = None

        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        return build("gmail", "v1", credentials=creds)

    def connect_account(self, account_email: str = None):
        if account_email:
            self.set_user(account_email)
        return self.get_service()

    def create_draft(self, to: str, subject: str, body: str):
        if not self.validate_recipient(to):
            raise ValueError("Please provide a valid recipient email address.")

        service = self.get_service()

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = {"message": {"raw": encoded_message}}

        result = service.users().drafts().create(userId="me", body=draft).execute()
        return result["id"]

    def send_email(self, to: str, subject: str, body: str):
        raise NotImplementedError("Automatic sending is disabled in this MVP. Use Gmail to send the draft after review.")

    def get_messages(self):
        raise NotImplementedError("Not implemented in Phase 1 MVP.")
