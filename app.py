from email.message import EmailMessage
from urllib.parse import urlencode

import streamlit as st
from dotenv import load_dotenv

from agent.email_agent import EmailAgent
from auth.authentication import UserAuthManager
from database.database import EmailHistoryDB
from integrations.gmail import GmailProvider

load_dotenv()

st.set_page_config(page_title="AI Email Agent", page_icon="✉️", layout="wide")


def build_gmail_compose_url(recipient: str, subject: str, body: str) -> str:
    query = urlencode({"view": "cm", "fs": "1", "to": recipient, "su": subject, "body": body})
    return f"https://mail.google.com/mail/?{query}"


def build_eml(recipient: str, subject: str, body: str) -> bytes:
    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    return message.as_bytes()

agent = EmailAgent()
db = EmailHistoryDB(db_path="email_history.db")
auth = UserAuthManager(db_path="email_history.db")

if "generated_email" not in st.session_state:
    st.session_state.generated_email = {"subject": "", "body": ""}
if "status_message" not in st.session_state:
    st.session_state.status_message = ""
if "draft_id" not in st.session_state:
    st.session_state.draft_id = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "gmail_account" not in st.session_state:
    st.session_state.gmail_account = "default"

if st.session_state.user_id is None:
    st.title("AI Email Agent")
    st.caption("Create an app account first, then connect Gmail securely with Google OAuth.")
    st.info("This login is for the AI Email Agent, not your Gmail password. Never enter your Google password here.")
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                user = auth.login_user(username, password)
                st.session_state.user_id = user["id"]
                st.session_state.gmail_account = user.get("gmail_account") or "default"
                st.success("Logged in successfully.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with signup_tab:
        new_username = st.text_input("Create username")
        new_password = st.text_input("Create password", type="password")
        if st.button("Create Account"):
            try:
                auth.register_user(new_username, new_password)
                st.success("Account created. Please log in.")
            except Exception as exc:
                st.error(str(exc))
    st.stop()

current_user = auth.get_user_by_id(st.session_state.user_id)
provider = GmailProvider(token_path="token.json", credentials_path="credentials.json", user_email=st.session_state.gmail_account)

page = st.sidebar.radio("Navigation", ["Generate Email", "Email History"])

st.sidebar.markdown("---")
st.sidebar.caption(f"Signed in as: {current_user['username']}")
if st.sidebar.button("Log out", icon=":material/logout:"):
    for key in ("user_id", "gmail_account", "generated_email", "status_message", "draft_id"):
        st.session_state.pop(key, None)
    st.rerun()

connected_accounts = auth.get_user_gmail_accounts(st.session_state.user_id)
account_names = [item["gmail_account"] for item in connected_accounts]
account_options = ["default"] + account_names
selected_index = account_options.index(st.session_state.gmail_account) if st.session_state.gmail_account in account_options else 0
selected_account = st.sidebar.selectbox(
    "Connected Gmail account",
    options=account_options,
    index=selected_index,
)

if selected_account != "default":
    st.session_state.gmail_account = selected_account
    provider = GmailProvider(token_path="token.json", credentials_path="credentials.json", user_email=st.session_state.gmail_account)

account_email = st.sidebar.text_input("Google account email to connect", value="", placeholder="you@gmail.com")
st.sidebar.caption("After you click connect, Google will open its secure OAuth sign-in. Your Gmail password is never shared with this app.")
if st.sidebar.button("Connect Gmail Account"):
    if not account_email.strip():
        st.sidebar.error("Please enter a Gmail account email to connect.")
    else:
        st.session_state.gmail_account = account_email.strip()
        provider.set_user(st.session_state.gmail_account)
        try:
            provider.connect_account(st.session_state.gmail_account)
            auth.set_gmail_account(st.session_state.user_id, st.session_state.gmail_account, provider.token_path)
            st.sidebar.success(f"Connected to {st.session_state.gmail_account}")
            st.rerun()
        except Exception as exc:
            error_text = str(exc)
            if "access_denied" in error_text or "403" in error_text:
                st.sidebar.error(
                    "Google blocked this account. Add it under Google Cloud Console > OAuth consent screen > Test users, "
                    "or publish and verify the OAuth app for public access."
                )
            else:
                st.sidebar.error(f"Unable to connect to Gmail: {error_text}")

st.sidebar.info("Recipient email can be any valid email address. The Gmail account selected above is the sender account used to save drafts.")

if page == "Generate Email":
    st.title("AI Email Agent")
    st.caption("Write better emails with AI — generate, review, edit and save or export your draft.")

    with st.form("email_form", clear_on_submit=False):
        recipient = st.text_input("Recipient Email", value="", placeholder="example@gmail.com")
        request = st.text_area("Email Request", value="", height=120, placeholder="Write an email applying for a Data Analyst internship.")
        tone = st.selectbox("Tone", ["Professional", "Formal", "Friendly", "Concise", "Apologetic", "Persuasive", "Thank You"])

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            generate_clicked = st.form_submit_button("Generate Email")
        with col2:
            regenerate_clicked = st.form_submit_button("Regenerate")
        with col3:
            clear_clicked = st.form_submit_button("Clear")

        if clear_clicked:
            st.session_state.generated_email = {"subject": "", "body": ""}
            st.session_state.status_message = ""
            st.session_state.draft_id = ""
            st.rerun()

        if generate_clicked or regenerate_clicked:
            try:
                if not recipient.strip():
                    raise ValueError("Please enter a recipient email address.")
                if not agent.validate_recipient(recipient):
                    raise ValueError("Please provide a valid recipient email address.")
                if not agent.validate_request(request):
                    raise ValueError("Please describe what you want the email to say.")

                result = agent.generate_email(request, tone=tone)
                st.session_state.generated_email = result
                st.session_state.status_message = ""
                st.session_state.draft_id = ""
                st.success("Email generated successfully.")
            except Exception as exc:
                st.error(str(exc))

    if st.session_state.generated_email["subject"] or st.session_state.generated_email["body"]:
        st.markdown("## Email Preview")
        st.write(f"Recipient: {recipient}")

        subject = st.text_input("Subject", value=st.session_state.generated_email["subject"])
        body = st.text_area("Email Body", value=st.session_state.generated_email["body"], height=250)

        st.session_state.generated_email["subject"] = subject
        st.session_state.generated_email["body"] = body

        save_clicked = st.button("Save to Gmail Draft")
        fallback_col1, fallback_col2 = st.columns(2)
        with fallback_col1:
            st.link_button(
                "Open in Gmail Compose",
                build_gmail_compose_url(recipient, subject, body),
                icon=":material/open_in_new:",
            )
        with fallback_col2:
            st.download_button(
                "Download .eml",
                data=build_eml(recipient, subject, body),
                file_name="ai_email_draft.eml",
                mime="message/rfc822",
                icon=":material/download:",
            )
        st.caption("Gmail Compose and .eml export work without Gmail OAuth. Save to Gmail Draft requires a connected account.")

        if save_clicked:
            try:
                if not recipient.strip():
                    raise ValueError("Please enter a recipient email address.")
                if not agent.validate_recipient(recipient):
                    raise ValueError("Please provide a valid recipient email address.")
                if not subject.strip() or not body.strip():
                    raise ValueError("The email subject and body cannot be empty.")
                if st.session_state.gmail_account == "default":
                    raise ValueError("Please connect a Gmail account before saving the draft.")

                draft_id = provider.create_draft(recipient, subject, body)
                st.session_state.draft_id = draft_id
                st.session_state.status_message = "✓ Email saved to Gmail Drafts"
                db.save_email(str(st.session_state.user_id), recipient, subject, body, tone, "draft_saved", draft_id)
                st.success(f"✓ Email saved to Gmail Drafts\nDraft ID: {draft_id}\nSaved in Gmail account: {st.session_state.gmail_account}")
            except Exception as exc:
                st.error(str(exc))

    if st.session_state.status_message:
        st.info(st.session_state.status_message)

else:
    st.title("Email History")
    history = db.get_history(user_id=str(st.session_state.user_id), limit=20)
    if not history:
        st.write("No saved emails yet.")
    else:
        for item in history:
            st.markdown(f"- **{item['created_time']}** | {item['recipient']} | **{item['subject']}** | {item['status']}")
