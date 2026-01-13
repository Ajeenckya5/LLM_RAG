from passlib.context import CryptContext
_pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(pw: str) -> str:
    return _pwd.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return _pwd.verify(pw, hashed)
