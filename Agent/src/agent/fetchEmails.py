import imaplib
import email
import yaml
from pathlib import Path
import re
import html as html_module
from typing import List, Dict, Any
from email.message import Message
from bs4 import BeautifulSoup

def fetch_Email_Data() -> str | None:
    """Load confidentials.yml located next to this module. Logged into the mail and Extracted the required data. """
    cfg_path = Path(__file__).resolve().parent / "confidentials.yml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"confidentials.yml not found at expected location: {cfg_path}")

    with cfg_path.open() as f:
        data = yaml.safe_load(f)

    username, password = data.get("user"), data.get("password")
    if not username or not password:
        raise ValueError("Missing 'user' or 'password' in confidentials.yml")

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("INBOX")

        key = "FROM"
        value = "thefamilyguy138@gmail.com"

        typ, data = mail.search(None, key, value)  # we can also pass here the email of the person from whom tasks assigned to us we need to know
        if typ != "OK":
            print("No messages found or search failed")
            return []
        ids = data[0].split()
        # take the most recent `limit` ids
        ids = ids[-10:]
        results: List[Dict[str, Any]] = []
        for idb in reversed(ids):
            typ, msg_data = mail.fetch(idb, "(RFC822)")  #-> RFC822 this shows to extract the complete body
            if typ != "OK" or not msg_data:
                continue
            # msg_data can be a list of tuples
            raw = None
            if isinstance(msg_data[0], tuple):      #raw stores the data receieved from the msg_data(which is not in proper structure)
                raw = msg_data[0][1]
            elif isinstance(msg_data[0], bytes):
                raw = msg_data[0]
            if raw is None:
                continue
            msg = email.message_from_bytes(raw)
            subject = msg.get("Subject", "")
            from_ = msg.get("From", "")
            date = msg.get("Date", "")
            body = parse_message(msg)
            results.append({"subject": subject, "from": from_, "date": date, "body": body})

        try:
            mail.close()
        except Exception:
            pass
        mail.logout()
        return results
    except Exception as exc:
        print(f"IMAP fetch error: {exc}")
        return []


def html_to_text(html: str) -> str:
    """Convert HTML to plain text using BeautifulSoup"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")
        text = html_module.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        # fall back to regex stripper below
        pass


def parse_message(msg: Message) -> str:
    """Extract a best-effort text body from an email.message.Message."""
    # If multipart, prefer text/plain, else fall back to text/html
    if msg.is_multipart():
        parts = msg.walk()
        plain_chunks: List[str] = []
        html_chunks: List[str] = []
        for part in parts:
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                try:
                    plain_chunks.append(payload.decode(charset, errors="replace"))
                except Exception:
                    plain_chunks.append(payload.decode("utf-8", errors="replace"))
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                charset = part.get_content_charset() or "utf-8"
                try:
                    html_chunks.append(payload.decode(charset, errors="replace"))
                except Exception:
                    html_chunks.append(payload.decode("utf-8", errors="replace"))

        if plain_chunks:
            return "\n\n".join(plain_chunks).strip()
        if html_chunks:
            return html_to_text("\n\n".join(html_chunks))
        return ""
    else:
        payload = msg.get_payload(decode=True)
        if payload is None:
            # some payloads may be already str
            payload = msg.get_payload()
            if isinstance(payload, str):
                return payload
            return ""
        charset = msg.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except Exception:
            text = payload.decode("utf-8", errors="replace")
        if msg.get_content_type() == "text/html":
            return html_to_text(text)
        return text
        
    

            