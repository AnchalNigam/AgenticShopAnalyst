# AgenticShop — AI Business Analyst

An incremental learning project for building an AI Business Analyst Copilot for the fictional e-commerce company Shoply.

## Current stage

Initial setup only: a FastAPI health endpoint and an empty PostgreSQL `agenticshop` database. No tables, data, LLM integration, or SQL tool have been added yet.

## Layout

- `backend/` — FastAPI service and tests
- `frontend/` — reserved for the future React + Vite client
- `database/` — reserved for schema and seed scripts
- `docs/` — setup and architecture notes

## Run locally

```bash
cp .env.example .env
# Choose a local-only password, then start PostgreSQL.
docker compose up -d postgres

cd backend
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload
```

Verify the API at `http://127.0.0.1:8000/health` and the database with:

```bash
docker compose exec postgres psql -U agenticshop_app -d agenticshop -c 'SELECT current_database();'
```

## Create V1 development data

The schema and seed data are intentionally separate. The seed script uses a fixed random seed and refuses to overwrite existing rows.

```bash
backend/.venv/bin/python -m pip install -e 'backend[dev]'
backend/.venv/bin/python -m database.seed --apply-schema --seed
backend/.venv/bin/python -m database.seed --verify
```

Run `backend/.venv/bin/python -m database.seed` first to preview the row counts and known business signals without changing the database.
