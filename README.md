# AI Email Agent

A Python + Streamlit AI Email Agent with OpenAI-generated drafts and Gmail draft saving.

## Features
- Generate email subject and body using OpenAI
- Review and edit email before saving
- Save drafts to Gmail
- Open a prefilled Gmail compose window or download an `.eml` draft without Gmail OAuth
- SQLite-backed email history
- Per-user Gmail account tracking
- Login, sign-up, logout, and account switching

## Setup
1. Create a `.env` file with:
   - `OPENAI_API_KEY=...`
   - `OPENAI_MODEL=gpt-4.1-mini`
2. Install dependencies:
   `python -m pip install -r requirements.txt`
3. Run the app:
   `python -m streamlit run app.py`

## Notes
- The Login tab uses an app username and password. Gmail accounts are connected separately from the sidebar using Google OAuth 2.0.
- Do not enter a Gmail password into the app. Google handles the password and consent in its own OAuth page.
- Gmail OAuth requires Google Cloud verification for public multi-user access.
- For local testing, add approved Gmail users to the Google OAuth consent screen test users.
- Recipient email can be any valid address; the Gmail account selected is the sender account used to save the draft.
- Sending is intentionally disabled; users review and send saved drafts from Gmail.
- Gmail Compose and `.eml` export are available while OAuth verification is pending.
