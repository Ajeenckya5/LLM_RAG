# Demo Script

## Start DB
From repo root:
docker compose up -d

## Setup backend
cd backend
cp .env.example .env
# Edit .env and set LLM_GGUF_PATH

conda create -n emailrag python=3.10 -y
conda activate emailrag
pip install -U pip
pip install -e .

## Seed users
python scripts/create_users.py

## Add sample emails
Put `.eml` files into:
- backend/sample_data/user1_eml/
- backend/sample_data/user2_eml/

## Ingest
python scripts/ingest_eml_dir.py --user-id 1 --dir sample_data/user1_eml
python scripts/ingest_eml_dir.py --user-id 2 --dir sample_data/user2_eml

## Run server
uvicorn app.main:app --reload --port 8000

## Login + query
Get token:
curl -s -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1@example.com&password=pass1"

Query:
curl -s -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"What did Sarah say about the Q4 budget?"}'

## Isolation proof
Run the same query as user2. If the email only exists for user1, sources should be empty or unrelated.

