from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720

    EMBEDDING_MODEL: str = "intfloat/e5-small-v2"

    LLM_GGUF_PATH: str
    LLM_CTX: int = 4096
    LLM_THREADS: int = 8

    TOP_K: int = 6

    class Config:
        env_file = ".env"


settings = Settings()

