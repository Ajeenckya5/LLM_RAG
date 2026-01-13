# Local Multi-User Email RAG (Postgres + pgvector + Mistral 7B)

A fully local Retrieval-Augmented Generation system that:
- ingests emails (`.eml` demo; extendable to Gmail IMAP),
- embeds and stores chunks in Postgres + pgvector,
- answers questions using a local Mistral 7B GGUF via llama.cpp,
- enforces strict multi-user isolation (no cross-user retrieval).

## Features
- **Multi-user**: JWT auth; retrieval is filtered by `user_id` at the SQL layer.
- **Vector DB**: Postgres 16 + pgvector (cosine distance retrieval).
- **Embeddings**: `intfloat/e5-small-v2` (CPU-friendly, 384 dims).
- **LLM**: Mistral 7B Instruct GGUF via `llama-cpp-python`.
- **Referenceable sources**: responses include `/emails/{id}` links.

## Repo layout
- `docker-compose.yml` – Postgres + pgvector
- `backend/app` – FastAPI app + RAG logic
- `backend/scripts` – seed users, ingest `.eml`, benchmark
- `backend/docs` – architecture, demo script, evaluation report
- `backend/sample_data` – two-user demo emails

## Quick start

### 1) Start Postgres
```bash
docker compose up -d

