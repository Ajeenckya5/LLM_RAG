from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import engine, Base, get_db, ensure_pgvector
from app import models
from app.config import settings
from app.auth import create_access_token, get_current_user, verify_password
from app.embeddings import embed_texts
from app.llm import llm_generate


app = FastAPI(title="Local Email RAG")


class QueryRequest(BaseModel):
    query: str


@app.on_event("startup")
def on_startup():
    ensure_pgvector()
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/auth/token")
def login_token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/emails/{email_id}")
def get_email(email_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    email_obj = (
        db.query(models.Email)
        .filter(models.Email.id == email_id, models.Email.user_id == user.id)
        .first()
    )
    if email_obj is None:
        raise HTTPException(status_code=404, detail="Email not found")

    return {
        "id": email_obj.id,
        "sender": email_obj.sender,
        "to": email_obj.to,
        "cc": email_obj.cc,
        "bcc": email_obj.bcc,
        "subject": email_obj.subject,
        "sent_at": email_obj.sent_at.isoformat() if email_obj.sent_at else None,
        "body": email_obj.body,
        "source": email_obj.source,
        "source_ref": email_obj.source_ref,
    }


@app.post("/query")
def query(payload: QueryRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    q = (payload.query or "").strip()
    if not q:
        return {"answer": "Empty query.", "sources": []}

    q_vec = embed_texts([q])[0]

    rows = (
        db.query(models.EmailChunk)
        .filter(models.EmailChunk.user_id == user.id)
        .order_by(models.EmailChunk.embedding.cosine_distance(q_vec))
        .limit(settings.TOP_K)
        .all()
    )

    if not rows:
        return {"answer": "I could not find any relevant emails for your account.", "sources": []}

    context_parts = []
    sources = []
    seen_email_ids = set()

    for ch in rows:
        email_obj = (
            db.query(models.Email)
            .filter(models.Email.id == ch.email_id, models.Email.user_id == user.id)
            .first()
        )
        if email_obj is None:
            continue

        context_parts.append(f"[Email {email_obj.id}] {ch.chunk_text}")

        if email_obj.id not in seen_email_ids:
            sources.append(
                {
                    "email_id": email_obj.id,
                    "subject": email_obj.subject,
                    "sender": email_obj.sender,
                    "sent_at": email_obj.sent_at.isoformat() if email_obj.sent_at else None,
                    "link": f"/emails/{email_obj.id}",
                }
            )
            seen_email_ids.add(email_obj.id)

    context = "\n\n".join(context_parts)

    prompt = (
        "You are a helpful assistant answering questions using the email context below.\n"
        "Only use facts supported by the context. Cite emails using [Email <id>].\n\n"
        "Context:\n"
        f"{context}\n\n"
        "Question:\n"
        f"{q}\n\n"
        "Answer:"
    )

    answer = llm_generate(prompt)
    return {"answer": answer, "sources": sources}
