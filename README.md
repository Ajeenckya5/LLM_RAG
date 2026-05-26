# Multi-User Email RAG

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/pgvector-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Production-grade RAG over 10,000+ emails with per-user vector isolation.**
E5-small-v2 embeddings · Mistral 7B · pgvector · JWT auth · sub-200ms retrieval

</div>

---

## Architecture

```
Client
  │  JWT token
  ▼
FastAPI  ──► JWT auth ──► user_id extracted
  │
  ├── /ingest   ──► e5-small-v2 embed ──► pgvector (user_id, vector, chunk)
  │
  └── /query    ──► embed query
                      │
                      ▼
                pgvector cosine search
                WHERE user_id = :uid        ← hard SQL isolation
                      │
                      ▼
                Top-K chunks + metadata
                      │
                      ▼
                Mistral 7B (llama-cpp-python)
                      │
                      ▼
                Answer + source /emails/{id} links
```

**Key design decision:** user isolation is enforced at the SQL layer (`WHERE user_id = :uid`), not application logic. No amount of prompt injection can leak cross-user data.

---

## Features

- **Multi-user isolation** — JWT auth with SQL-enforced per-user filtering at the pgvector layer
- **10K+ email index** — batch ingestion with embedding caching to avoid re-embedding on restart
- **E5-small-v2 embeddings** — 384-dim, CPU-friendly, strong retrieval precision
- **Mistral 7B Instruct** — local GGUF inference via `llama-cpp-python`, no OpenAI dependency
- **Retrieval metrics** — precision@5, answer faithfulness, and latency benchmarks included
- **Source references** — every answer cites `/emails/{id}` links for auditability
- **Docker Compose** — single command brings up Postgres 16 + pgvector

---

## Performance

| Metric | Value |
|--------|-------|
| Index size | 10,000+ emails |
| Retrieval latency (p50) | < 80ms |
| End-to-end query latency | < 4s (Mistral 7B, CPU) |
| Retrieval precision@5 | 0.84 |
| Answer faithfulness | 0.79 |
| Cross-user data leakage | **0** (SQL-enforced) |

---

## Project Structure

```
email-rag/
├── docker-compose.yml          # Postgres 16 + pgvector
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app
│   │   ├── auth.py             # JWT token issuance + validation
│   │   ├── ingest.py           # Email parsing + chunking + embedding
│   │   ├── retrieval.py        # pgvector cosine search with user filter
│   │   ├── generation.py       # Mistral 7B inference via llama-cpp-python
│   │   └── models.py           # SQLAlchemy ORM (emails, chunks, users)
│   ├── scripts/
│   │   ├── seed_users.py       # Create demo users + JWT tokens
│   │   ├── ingest_emails.py    # Batch ingest .eml files
│   │   └── benchmark.py        # Retrieval precision + faithfulness eval
│   ├── docs/
│   │   ├── architecture.md
│   │   └── evaluation_report.md
│   └── sample_data/            # Two-user demo email set
└── requirements.txt
```

---

## Quickstart

```bash
git clone https://github.com/Ajeenckya5/LLM_RAG
cd LLM_RAG

# 1. Start Postgres + pgvector
docker compose up -d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed demo users and ingest emails
python backend/scripts/seed_users.py
python backend/scripts/ingest_emails.py --data backend/sample_data/

# 4. Start the API
uvicorn backend.app.main:app --reload

# 5. Query
curl -H "Authorization: Bearer <jwt>" \
  "http://localhost:8000/query?q=What+meetings+were+scheduled+last+week"
```

---

## Why pgvector Instead of a Dedicated Vector DB

pgvector keeps the entire system in a single Postgres instance — no separate Pinecone/Weaviate service to manage, no cross-service auth, and user isolation is a single `WHERE` clause on an indexed column rather than a multi-tenant API policy.

---

## Tech Stack

`Python 3.10+` · `FastAPI` · `PostgreSQL 16 + pgvector` · `intfloat/e5-small-v2` · `Mistral 7B GGUF` · `llama-cpp-python` · `SQLAlchemy` · `Docker Compose` · `JWT (PyJWT)`
