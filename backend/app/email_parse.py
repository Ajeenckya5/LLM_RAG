from __future__ import annotations

import email
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


def _get_header(msg: Message, name: str) -> str | None:
    v = msg.get(name)
    return v.strip() if v else None


def _extract_text(msg: Message) -> str:
    if msg.is_multipart():
        parts = msg.walk()
    else:
        parts = [msg]

    plain_parts: list[str] = []
    html_parts: list[str] = []

    for part in parts:
        ctype = part.get_content_type()
        disp = (part.get("Content-Disposition") or "").lower()
        if "attachment" in disp:
            continue

        payload = part.get_payload(decode=True)
        if payload is None:
            continue

        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="replace")
        except Exception:
            text = payload.decode("utf-8", errors="replace")

        if ctype == "text/plain":
            plain_parts.append(text)
        elif ctype == "text/html":
            html_parts.append(text)

    if plain_parts:
        return "\n".join(plain_parts).strip()

    if html_parts:
        import re

        html = "\n".join(html_parts)
        html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
        html = re.sub(r"(?is)<.*?>", " ", html)
        html = re.sub(r"\s+", " ", html)
        return html.strip()

    return ""


def parse_eml_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    raw = path.read_bytes()
    msg = email.message_from_bytes(raw)

    sent_at = None
    if msg.get("Date"):
        try:
            sent_at = parsedate_to_datetime(msg.get("Date"))
        except Exception:
            sent_at = None

    return {
        "message_id": (msg.get("Message-ID") or "").strip() or None,
        "thread_id": None,
        "sender": _get_header(msg, "From"),
        "to": _get_header(msg, "To"),
        "cc": _get_header(msg, "Cc"),
        "bcc": _get_header(msg, "Bcc"),
        "subject": (msg.get("Subject") or "").strip() or None,
        "body": _extract_text(msg),
        "sent_at": sent_at,
    }

