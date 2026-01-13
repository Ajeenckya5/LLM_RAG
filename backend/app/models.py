from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship()

    message_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    thread_id: Mapped[str | None] = mapped_column(String(512), nullable=True)

    sender: Mapped[str | None] = mapped_column(String(512), nullable=True)
    to: Mapped[str | None] = mapped_column(Text, nullable=True)
    cc: Mapped[str | None] = mapped_column(Text, nullable=True)
    bcc: Mapped[str | None] = mapped_column(Text, nullable=True)

    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped[str] = mapped_column(String(50), default="eml")
    source_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "message_id", name="uq_user_message_id"),
        Index("ix_emails_user_sent_at", "user_id", "sent_at"),
    )


class EmailChunk(Base):
    __tablename__ = "email_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(Integer, index=True)
    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), index=True)
    email: Mapped["Email"] = relationship()

    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)

    # intfloat/e5-small-v2 => 384 dims
    embedding: Mapped[list[float]] = mapped_column(Vector(384))

    __table_args__ = (
        Index("ix_chunks_user_email", "user_id", "email_id"),
    )

