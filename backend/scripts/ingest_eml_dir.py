import argparse
from pathlib import Path
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine, Base
from app import models
from app.email_parse import parse_eml_file
from app.embeddings import chunk_text, embed_texts


def ingest_dir(user_id: int, eml_dir: Path) -> None:
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        files = sorted(eml_dir.glob("**/*.eml"))
        if not files:
            print(f"No .eml files found under: {eml_dir}")
            return

        added = 0
        for f in files:
            data = parse_eml_file(f)
            body = (data.get("body") or "").strip()
            if not body:
                continue

            message_id = data.get("message_id")
            if message_id:
                dup = (
                    db.query(models.Email)
                    .filter(models.Email.user_id == user_id, models.Email.message_id == message_id)
                    .first()
                )
                if dup:
                    continue

            email_obj = models.Email(
                user_id=user_id,
                message_id=message_id,
                thread_id=data.get("thread_id"),
                sender=data.get("sender"),
                to=data.get("to"),
                cc=data.get("cc"),
                bcc=data.get("bcc"),
                subject=data.get("subject"),
                body=body,
                sent_at=data.get("sent_at"),
                source="eml",
                source_ref=str(f),
            )
            db.add(email_obj)
            db.flush()

            content = f"Subject: {email_obj.subject}\n\n{email_obj.body}"
            chunks = chunk_text(content)
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
        print(f"Ingested {added} emails for user_id={user_id}")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user-id", type=int, required=True)
    ap.add_argument("--dir", type=str, required=True)
    args = ap.parse_args()
    ingest_dir(args.user_id, Path(args.dir))

