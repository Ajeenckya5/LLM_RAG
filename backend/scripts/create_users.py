from sqlalchemy import text
from app.db import SessionLocal, engine, Base
from app import models
from app.security import hash_password


def main():
    with engine.begin() as conn:
    	conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seeds = [
            ("user1@example.com", "pass1"),
            ("user2@example.com", "pass2"),
        ]

        for email, pw in seeds:
            exists = db.query(models.User).filter(models.User.email == email).first()
            if exists:
                continue
            db.add(models.User(email=email, password_hash=hash_password(pw)))

        db.commit()

        for u in db.query(models.User).order_by(models.User.id).all():
            print(f"user_id={u.id} email={u.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

