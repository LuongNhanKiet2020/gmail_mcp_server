# gmail.py — Gmail MCP Server (search, read, reply emails)
import os
import base64
from email.mime.text import MIMEText

from mcp.server.fastmcp import FastMCP
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ─── Config ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# ─── MCP Server ───────────────────────────────────────────────────────
mcp = FastMCP("Gmail MCP Server")

# ─── Helpers ──────────────────────────────────────────────────────────

def _get_gmail_service():
    """Authenticate with Google OAuth2 and return a Gmail API service."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _get_header(headers: list, name: str, default: str = "") -> str:
    return next((h["value"] for h in headers if h["name"].lower() == name.lower()), default)


def _decode_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8")
            if "parts" in part:
                result = _decode_body(part)
                if result:
                    return result
    else:
        data = payload.get("body", {}).get("data")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8")
    return ""


# ─── MCP Tools ────────────────────────────────────────────────────────

@mcp.tool()
def search_emails(query: str, max_results: int = 5) -> str:
    service = _get_gmail_service()
    if not service:
        return "Error: credentials.json not found."

    try:
        results = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        messages = results.get("messages", [])

        if not messages:
            return "No emails found matching the query."

        output_lines = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["Subject", "Date", "From", "To"]
            ).execute()

            headers = msg_data.get("payload", {}).get("headers", [])
            subject = _get_header(headers, "Subject", "No subject")
            date = _get_header(headers, "Date", "Unknown")
            from_addr = _get_header(headers, "From", "Unknown")

            output_lines.append(
                f"📧 ID: {msg['id']}\n"
                f"   Subject: {subject}\n"
                f"   From: {from_addr}\n"
                f"   Date: {date}\n"
                f"   Snippet: {msg_data.get('snippet', '')}\n"
            )

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error searching emails: {e}"


@mcp.tool()
def get_email_content(message_id: str) -> str:
    service = _get_gmail_service()
    if not service:
        return "Error: credentials.json not found."

    try:
        msg = service.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()

        payload = msg["payload"]
        headers = payload.get("headers", [])

        date = _get_header(headers, "Date", "Unknown")
        subject = _get_header(headers, "Subject", "No subject")
        from_addr = _get_header(headers, "From", "Unknown")
        to_addr = _get_header(headers, "To", "Unknown")

        body = _decode_body(payload)
        if not body:
            body = "(No plain text content found)"

        if len(body) > 2000:
            body = body[:2000] + "\n... (truncated)"

        return (
            f"Subject: {subject}\n"
            f"From: {from_addr}\n"
            f"To: {to_addr}\n"
            f"Date: {date}\n"
            f"Message-ID: {_get_header(headers, 'Message-ID')}\n"
            f"\n--- Body ---\n{body}"
        )

    except Exception as e:
        return f"Error getting email content: {e}"


@mcp.tool()
def reply_to_email(message_id: str, reply_text: str) -> str:
    service = _get_gmail_service()
    if not service:
        return "Error: credentials.json not found."

    try:
        # Fetch original message to get threading info
        original = service.users().messages().get(
            userId="me", id=message_id, format="metadata",
            metadataHeaders=["Subject", "From", "To", "Message-ID", "References"]
        ).execute()

        headers = original.get("payload", {}).get("headers", [])
        thread_id = original["threadId"]
        original_subject = _get_header(headers, "Subject", "")
        original_from = _get_header(headers, "From", "")
        original_to = _get_header(headers, "To", "")
        original_msg_id = _get_header(headers, "Message-ID", "")
        original_refs = _get_header(headers, "References", "")

        # Smart reply: if we sent the email, reply to the recipient
        profile = service.users().getProfile(userId="me").execute()
        my_email = profile.get("emailAddress", "").lower()

        if my_email and my_email in original_from.lower():
            reply_to = original_to
        else:
            reply_to = original_from

        # Build proper reply subject
        subject = original_subject
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        # Build MIME message with proper threading headers
        msg = MIMEText(reply_text)
        msg["to"] = reply_to
        msg["subject"] = subject

        if original_msg_id:
            msg["In-Reply-To"] = original_msg_id
            refs = f"{original_refs} {original_msg_id}".strip() if original_refs else original_msg_id
            msg["References"] = refs

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        sent = service.users().messages().send(
            userId="me",
            body={"raw": raw, "threadId": thread_id}
        ).execute()

        return f"✅ Reply sent successfully!\nNew message ID: {sent['id']}\nThread ID: {thread_id}"

    except Exception as e:
        return f"Error replying to email: {e}"


# ─── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")