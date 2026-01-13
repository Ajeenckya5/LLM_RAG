import argparse
import imaplib
import email
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine, Base
from app import models
from app.embeddings import chunk_text, embed_texts


def ensure_pgvector() -> None:
    """Make sure pgvector extension exists in the current database."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))


def sanitize_app_password(pw: str) -> str:
    """
    Google App Passwords are shown grouped (e.g. 'abcd efgh ijkl mnop') and sometimes
    copy/paste introduces non-breaking spaces. IMAP LOGIN expects ASCII bytes.
    This normalizes whitespace and removes it entirely.
    """
    if pw is None:
        return ""
    # normalize weird spaces
    pw = (
        pw.replace("\u00a0", " ")  # NBSP
          .replace("\u2007", " ")  # figure space
          .replace("\u202f", " ")  # narrow NBSP
          .strip()
    )
    # remove all whitespace
    pw = "".join(pw.split())
    return pw


def _decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except Exception:
        return payload.decode("utf-8", errors="replace")


def _html_to_text(html: str) -> str:
    # tiny and dependency-free; good enough for a demo
    import re
    s = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    s = re.sub(r"(?is)<.*?>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def extract_body_text(msg: Message) -> str:
    """
    Prefer text/plain; fallback to text/html stripped to text.
    Skips attachments.
    """
    if msg.is_multipart():
        plain_parts = []
        html_parts = []
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue
            if ctype == "text/plain":
                plain_parts.append(_decode_payload(part))
            elif ctype == "text/html":
                html_parts.append(_decode_payload(part))

        if plain_parts:
            return "\n".join(plain_parts).strip()
        if html_parts:
            return _html_to_text("\n".join(html_parts))
        return ""

    # single-part
    ctype = msg.get_content_type()
    if ctype == "text/plain":
        return _decode_payload(msg).strip()
    if ctype == "text/html":
        return _html_to_text(_decode_payload(msg))
    return ""


def header(msg: Message, name: str) -> Optional[str]:
    v = msg.get(name)
    return v.strip() if v else None


def ingest_imap(
    user_id: int,
    host: str,
    username: str,
    password: str,
    mailbox: str,
    max_emails: int,
) -> None:
    Base.metadata.create_all(bind=engine)
    ensure_pgvector()

    safe_pw = sanitize_app_password(password)
    if not safe_pw:
        raise RuntimeError("Empty password after sanitization. Re-copy the App Password.")

    db: Session = SessionLocal()
    try:
        m = imaplib.IMAP4_SSL(host)
        m.login(username, safe_pw)
        m.select(mailbox)

        typ, data = m.search(None, "ALL")
        if typ != "OK":
            raise RuntimeError("IMAP search failed")

        msg_ids = data[0].split()
        if max_emails > 0:
            msg_ids = msg_ids[-max_emails:]

        added = 0
        for imap_id in msg_ids:
            typ, msg_data = m.fetch(imap_id, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue

            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            message_id = (msg.get("Message-ID") or "").strip() or None
            sender = header(msg, "From")
            to = header(msg, "To")
            cc = header(msg, "Cc")
            bcc = header(msg, "Bcc")
            subject = (msg.get("Subject") or "").strip() or None

            sent_at = None
            if msg.get("Date"):
                try:
                    sent_at = parsedate_to_datetime(msg.get("Date"))
                except Exception:
                    sent_at = None

            body = extract_body_text(msg)
            if not body:
                continue

            # Dedupe per user when Message-ID exists
            if message_id:
                existing = (
                    db.query(models.Email)
                    .filter(models.Email.user_id == user_id, models.Email.message_id == message_id)
                    .first()
                )
                if existing:
                    continue

            email_obj = models.Email(
                user_id=user_id,
                message_id=message_id,
                thread_id=None,
                sender=sender,
                to=to,
                cc=cc,
                bcc=bcc,
                subject=subject,
                body=body,
                sent_at=sent_at,
                source="gmail_imap",
                source_ref=f"imap:{imap_id.decode() if isinstance(imap_id, bytes) else str(imap_id)}",
            )
            db.add(email_obj)
            db.flush()  # assigns email_obj.id

            content_for_embedding = f"Subject: {subject or ''}\n\n{body}"
            chunks = chunk_text(content_for_embedding)
            vecs = embed_texts(chunks)

            for i, (ch, v) in enumerate(zip(chunks, vecs)):
                db.add(
                    models.EmailChunk(
                        user_id=user_id,
                        email_id=email_obj.id,
                        chunk_index=i,
                        chunk_text=ch,
                        embedding=v,
                    )
                )

            added += 1

        db.commit()
        m.logout()

        print(f"Ingested {added} Gmail emails for user_id={user_id} mailbox={mailbox}")
    finally:
        db.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-id", type=int, required=True)
    ap.add_argument("--host", type=str, default="imap.gmail.com")
    ap.add_argument("--username", type=str, required=True)
    ap.add_argument("--password", type=str, required=True)
    ap.add_argument("--mailbox", type=str, default="INBOX")
    ap.add_argument("--max", type=int, default=50)
    args = ap.parse_args()

    ingest_imap(
        user_id=args.user_id,
        host=args.host,
        username=args.username,
        password=args.password,
        mailbox=args.mailbox,
        max_emails=args.max,
    )


if __name__ == "__main__":
    main()
