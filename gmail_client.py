import base64
import codecs
import email
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import GMAIL_SCOPES, OAUTH_CLIENT_FILE, TOKEN_FILE


def get_credentials():
    creds = None
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)
    except Exception:
        pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_FILE, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return creds


def fetch_emails(days: int = 1) -> list[dict]:
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y/%m/%d")
    query = f"after:{since}"

    result = service.users().messages().list(userId="me", q=query, maxResults=500).execute()
    messages = result.get("messages", [])

    emails = []
    for msg in messages:
        raw = service.users().messages().get(userId="me", id=msg["id"], format="raw").execute()
        raw_data = base64.urlsafe_b64decode(raw["raw"].encode("ascii"))
        parsed = email.message_from_bytes(raw_data)

        subject = _decode_header(parsed.get("Subject", ""))
        sender = _decode_header(parsed.get("From", ""))
        date_str = parsed.get("Date", "")
        body = _get_body(parsed)

        emails.append({
            "id": msg["id"],
            "subject": subject,
            "sender": sender,
            "date": _parse_date(date_str),
            "body": body[:2000],
        })

    return emails


def _decode_header(value: str) -> str:
    import email.header
    parts = email.header.decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(_decode_bytes(part, charset))
        else:
            decoded.append(part)
    return "".join(decoded)


def _decode_bytes(payload: bytes, charset: str | None = None) -> str:
    candidates = []
    if charset:
        candidates.append(charset)
    candidates.extend(["utf-8", "cp949", "euc-kr", "latin-1"])

    tried = set()
    for candidate in candidates:
        normalized = (candidate or "").strip().lower()
        if not normalized or normalized in tried or normalized == "unknown-8bit":
            continue
        tried.add(normalized)
        try:
            codecs.lookup(normalized)
            return payload.decode(normalized, errors="replace")
        except LookupError:
            continue

    return payload.decode("utf-8", errors="replace")


def _get_body(msg) -> str:
    text_plain = ""
    text_html = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            if ct == "text/plain" and not text_plain:
                text_plain = _decode_bytes(payload, charset)
            elif ct == "text/html" and not text_html:
                text_html = _decode_bytes(payload, charset)
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            if msg.get_content_type() == "text/html":
                text_html = _decode_bytes(payload, charset)
            else:
                text_plain = _decode_bytes(payload, charset)

    if text_plain:
        return text_plain
    # HTML fallback: 태그 제거 후 공백 정리
    import re as _re
    text = _re.sub(r"<[^>]+>", " ", text_html)
    text = _re.sub(r"[ \t]+", " ", text)
    return text


def _parse_date(date_str: str) -> str:
    from email.utils import parsedate_to_datetime
    try:
        dt = parsedate_to_datetime(date_str)
        kst = dt.astimezone(timezone(timedelta(hours=9)))
        return kst.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return date_str
