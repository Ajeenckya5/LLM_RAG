# Local Email RAG (Multi-User)

This repo builds a fully local RAG system:
- Stores email embeddings in Postgres + pgvector
- Uses SentenceTransformers embeddings locally
- Uses Mistral 7B (GGUF) locally via llama.cpp bindings
- Enforces multi-user isolation in SQL (no cross-user retrieval)

## Quick start
1) Start DB from repo root:
   docker compose up -d

2) Setup Python env:
   cd backend
   cp .env.example .env
   # edit .env and set LLM_GGUF_PATH
   conda create -n emailrag python=3.10 -y
   conda activate emailrag
   pip install -U pip
   pip install -e .

3) Seed users:
   python scripts/create_users.py

4) Add .eml files:
   sample_data/user1_eml/
   sample_data/user2_eml/

5) Ingest:
   python scripts/ingest_eml_dir.py --user-id 1 --dir sample_data/user1_eml
   python scripts/ingest_eml_dir.py --user-id 2 --dir sample_data/user2_eml

6) Run API:
   uvicorn app.main:app --reload --port 8000

Open docs:
http://localhost:8000/docs

