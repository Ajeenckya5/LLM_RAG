# Local Multi-User Email RAG — Architecture

## Goal
A local RAG system that ingests emails, stores embeddings in Postgres+pgvector, and answers questions with a local LLM. Supports multiple users with strict isolation.

## Components
### Ingestion
- Reads `.eml` files (offline demo) and parses:
  - sender, recipients, subject, body, timestamp, message_id
- Stores raw email in `emails`
- Chunks and stores vectors in `email_chunks`

### Embeddings
- Model: `intfloat/e5-small-v2` (384 dims)
- Rationale:
  - Good retrieval quality for semantic search
  - Runs on CPU
- Prefixing:
  - Query uses `query: ...`
  - Stored texts use `passage: ...`

### Vector DB
- Postgres 16 + pgvector
- Retrieval uses cosine distance ordering in SQL

### LLM
- Mistral 7B Instruct (GGUF) via llama.cpp bindings
- Quantization recommendation:
  - Q4_K_M (good quality and fast enough on CPU)

### API
- FastAPI
- JWT auth
- `/query` returns:
  - answer
  - list of sources with `/emails/{id}` links

## Multi-user Isolation (Security)
- JWT identifies current user
- Retrieval query always includes:
  - `WHERE email_chunks.user_id = current_user_id`
- Email view endpoint always checks:
  - `emails.user_id = current_user_id`
- Prompt injection cannot bypass SQL filtering.
