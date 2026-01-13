from sqlalchemy.orm import Session
from sqlalchemy import select

from . import models
from .embeddings import embed_query
from .config import settings


def retrieve(db: Session, user_id: int, query: str, top_k: int | None = None) -> list[dict]:
    """
    Isolation is enforced here. Every retrieval includes:
      WHERE email_chunks.user_id = current_user.id
    """
    top_k = top_k or settings.TOP_K
    q_emb = embed_query(query)

    stmt = (
        select(models.EmailChunk, models.Email)
        .join(models.Email, models.Email.id == models.EmailChunk.email_id)
        .where(models.EmailChunk.user_id == user_id)
        .order_by(models.EmailChunk.embedding.cosine_distance(q_emb))
        .limit(top_k)
    )

    rows = db.execute(stmt).all()
    out = []
    for chunk, email in rows:
        out.append(
            {
                "chunk_id": chunk.id,
                "email_id": email.id,
                "subject": email.subject,
                "sender": email.sender,
                "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                "chunk_text": chunk.chunk_text,
            }
        )
    return out

