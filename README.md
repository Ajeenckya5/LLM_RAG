# Local Multi-User Email RAG

A fully local **Retrieval-Augmented Generation** system: E5 embeddings and **Mistral 7B** over **10,000+ indexed emails** in **PostgreSQL/pgvector**, with **JWT user isolation**, embedding caching, batched retrieval, and metrics for retrieval precision and answer faithfulness. Built for horizontally scalable, concurrent multi-user sessions.

---

## Highlights (resume-aligned)

- **E5 embeddings + Mistral 7B** over 10k+ indexed emails; PostgreSQL/pgvector with embedding caching and batched retrieval to cut inference latency.
- **JWT-secured backend** with strict per-user isolation; retrieval filtered by `user_id` at the SQL layer.
- **Retrieval precision and answer faithfulness** measured across all user sessions for continuous evaluation.
- **Horizontally scalable multi-user backend** supporting concurrent independent retrieval sessions per user.
- **Referenceable sources** — responses include `/emails/{id}` links.

---

## Features

| Area | Stack |
|------|--------|
| **Vector DB** | Postgres 16 + pgvector (cosine distance) |
| **Embeddings** | `intfloat/e5-small-v2` (384 dims, CPU-friendly) |
| **LLM** | Mistral 7B Instruct GGUF via `llama-cpp-python` |
| **Backend** | FastAPI, JWT auth, per-user isolation |

---

## Repo layout

| Path | Contents |
|------|----------|
| `docker-compose.yml` | Postgres + pgvector |
| `backend/app` | FastAPI app + RAG logic |
| `backend/scripts` | Seed users, ingest `.eml`, benchmark |
| `backend/docs` | Architecture, demo script, evaluation report |
| `backend/sample_data` | Two-user demo emails |

---

## Quick start

```bash
docker compose up -d
```

See `backend/README.md` or `backend/docs` for environment setup, migrations, and running the API.

---

## Tech stack

FastAPI · SQLAlchemy · pgvector · sentence-transformers (e5-small-v2) · llama-cpp-python (Mistral 7B GGUF)
