# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Source of truth and current status

- `Doc/文档2.MD` is the authoritative executable spec. Follow its phase boundaries and default decision table when implementing behavior that is not yet fully reflected in code.
- `README.md` is still the main implementation overview, but it is Phase-0-oriented. Verify the current repo state against the actual code before relying on it for Phase 1+ work.
- The repository has progressed beyond the original scaffold: it now contains the Phase 0 FastAPI/infrastructure foundation **plus Phase 1 database work** (ORM models, Alembic setup, initial migration, minimal CRUD helpers, and DB-oriented tests).
- User preference: always run Python-related work inside the project-specific virtual environment / conda environment, never the user’s global Python installation.

## Common commands

## Environment setup

Use a dedicated project environment rather than the system interpreter.

### Conda workflow (preferred when available)

```bash
conda create -n rag_sec_phase1 python=3.11 -y
conda activate rag_sec_phase1
pip install -e ".[test]"
```

If you only need a single command without shell activation, prefer:

```bash
conda run -n rag_sec_phase1 pip install -e ".[test]"
conda run -n rag_sec_phase1 pytest
```

### venv fallback

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -e ".[test]"
```

## Run the backend locally

The Python package is rooted at `backend/`, so run the app from `backend/`:

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Notes:
- `Settings` loads `.env` from the current working directory. Running from `backend/` expects `backend/.env`; Docker Compose avoids that mismatch by injecting environment variables directly.
- With no PostgreSQL/Redis/Qdrant running, `GET /health` still returns `{"status":"ok"}`, while `GET /api/v1/health/ready` reports degraded dependencies.

## Run with Docker Compose

From the repo root:

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f backend
docker compose down
docker compose down -v
```

Useful service targets during DB-focused work:

```bash
docker compose up -d postgres redis qdrant
```

Endpoints after startup:
- API root: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Qdrant dashboard: `http://localhost:6333/dashboard`

## Database migration commands

From `backend/`:

```bash
alembic upgrade head
alembic downgrade base
```

When using conda without activation:

```bash
conda run -n rag_sec_phase1 bash -lc 'cd backend && alembic upgrade head'
```

## Test commands

From the repo root:

```bash
pytest
pytest -m integration
pytest -m ""
pytest backend/tests/test_health.py
pytest backend/tests/test_health.py::test_health_returns_ok
pytest backend/tests/test_models.py -m integration
pytest backend/tests/test_crud.py -m integration
pytest backend/tests/test_integration.py::test_health_ready_all_ok -m integration
```

Important details:
- `pyproject.toml` sets `testpaths = ["backend/tests"]`.
- Default pytest options exclude integration tests with `-m 'not integration'`.
- Database-heavy tests live in the `integration` lane and expect PostgreSQL to be reachable.
- There is currently **no lint command configured** in the repo (`pyproject.toml` does not define Ruff/Black/mypy/etc.), so do not invent one in automation or docs.

## High-level architecture

## Repository shape

- Root contains packaging, orchestration, documentation, and local model directories: `pyproject.toml`, `docker-compose.yml`, `.env.example`, `README.md`, `Doc/`, and `models/`.
- Application code lives under `backend/app/`.
- Alembic lives under `backend/alembic/` and uses the project’s own `Settings` + `Base.metadata` rather than a separate database config.
- Tests live under `backend/tests/` and are split between lightweight app/config checks and real database/infrastructure integration tests.

## What is implemented now vs. what is placeholder

Implemented now:
- app bootstrap, configuration, logging, dependency clients, DB session factory, `/health`, `/api/v1/health/ready`
- SQLAlchemy ORM models for the Phase 1 core schema
- Alembic configuration and the initial migration
- minimal CRUD helpers in `backend/app/services/crud_service.py`
- model/CRUD integration tests in addition to the Phase 0 tests

Still largely placeholder:
- most business APIs under `app/api/` besides health
- most business services under `app/services/` besides the minimal CRUD helper
- workers, prompts, and query/ingest pipeline implementations
- Pydantic schemas for the full business API surface

Do not assume a file is implemented just because it exists; many files were scaffolded ahead of their phase.

## Runtime layering

The current request/runtime path is:

1. `backend/app/main.py` creates the FastAPI app, initializes logging, registers routes, and installs a minimal global exception handler.
2. `backend/app/api/__init__.py` aggregates routers under `/api/v1`.
3. `backend/app/api/health.py` exposes the implemented HTTP endpoints and keeps route handlers thin.
4. Infrastructure and persistence are delegated downward:
   - config via `backend/app/config.py`
   - PostgreSQL engine/session via `backend/app/db/session.py`
   - Redis/Qdrant/shared deps via `backend/app/dependencies.py`

Preserve this split: routes should remain thin, while operational and persistence logic belongs in services/workers/DB helpers.

## Database architecture (Phase 1)

Phase 1 established the persistence base for later phases:

- `backend/app/db/base.py` defines the shared `DeclarativeBase`
- `backend/app/models/__init__.py` imports all models so Alembic can discover metadata
- `backend/app/models/*.py` define the core PostgreSQL schema:
  - `documents`
  - `document_versions`
  - `chunks`
  - `query_logs`
  - `feedback`
  - `ingest_tasks`
  - `eval_datasets`
  - `eval_dataset_items`
  - `eval_runs`
  - `eval_run_items`
- `backend/alembic/env.py` reuses project config and metadata instead of duplicating DSN/config logic
- `backend/alembic/versions/0001_phase1_initial.py` is the initial schema migration

Key schema characteristics that matter for future work:
- UUID primary keys everywhere
- JSONB fields with explicit defaults on both ORM and migration sides
- `chunks.search_tsv` exists already, even though FTS behavior is not implemented yet
- several GIN indexes are part of the schema, not a later optimization
- `documents.current_version_id` and `document_versions` form a cycle, so migration ordering matters

## Minimal CRUD boundary

`backend/app/services/crud_service.py` exists only to provide Phase 1 persistence verification and limited reuse. It is **not** the full business service layer.

Use it for:
- creating core records needed in tests or early persistence wiring
- fetching records by primary key

Do not treat it as permission to implement upload, ingestion, indexing, retrieval, or query orchestration early.

## Planned big-picture architecture from the spec

The repository layout already reflects the intended RAG system, even though most of it is not implemented yet.

### Ingest pipeline

upload → raw file storage → file hash → `document` / `document_version` / `ingest_task` creation → async worker processing → parse → clean → chunk → chunk hash → PostgreSQL persistence → embed **child chunks only** → Qdrant upsert → PostgreSQL FTS update → task completion

Expected ownership by module family:
- `app/api/upload.py`, `app/api/documents.py`: HTTP endpoints
- `app/workers/`: async ingest/reindex orchestration
- `app/services/parser_service.py`, `cleaner_service.py`, `chunk_service.py`: content preparation
- `app/services/embedding_service.py`, `vector_store.py`, `keyword_store.py`, `index_service.py`: indexing
- `app/models/`: document/version/chunk/task persistence model

### Query pipeline

user query → `safety_guard` → `intent_classifier` → `term_expander` → `query_rewriter` → `metadata_filter` → vector search + PostgreSQL FTS → RRF fusion → reranker → parent-context fetch → `answer_generator` → `citation_checker`

Expected ownership by module family:
- `app/api/query.py`: query-facing endpoints
- `app/services/safety_guard.py`: first-stage safety boundary
- `app/services/retriever.py`, `fusion.py`, `reranker.py`: retrieval and ranking
- `app/services/answer_generator.py`, `citation_checker.py`, `llm_service.py`: grounded answer generation
- `app/prompts/*.md`: prompt templates referenced by service-layer model wrappers

## Non-obvious rules from the spec that should shape code changes

These constraints appear across the docs and are easy to violate if you only read the current code:

- Implement strictly by phase; do not fill in later-phase modules early just because files already exist.
- API routes should stay thin; business logic belongs in services/workers.
- Uploading a file creates a new document; creating a new version is a separate replace flow.
- Incremental updates must be chunk-diff based rather than full reindex.
- Only **child chunks** are indexed in Qdrant/keyword search; parent chunks are for context reconstruction.
- Task state is intended to be dual-written to Redis and PostgreSQL.
- Default retrieval scope is the active document, active version, and active chunks only.
- Safety filtering is a first-stage query step, not an afterthought near answer generation.

## Testing structure

Tests are intentionally layered:
- `backend/tests/test_health.py`: HTTP contract and response-shape checks that do not require live services
- `backend/tests/test_config.py`: settings/bootstrap assertions
- `backend/tests/test_integration.py`: Phase 0 infrastructure connectivity tests
- `backend/tests/test_models.py`: Phase 1 schema/defaults/constraint coverage
- `backend/tests/test_crud.py`: Phase 1 minimal CRUD coverage
- `backend/tests/conftest.py`: shared TestClient plus DB migration/session fixtures

Keep new tests aligned with this split: fast default tests when possible, explicit `integration` marking when real PostgreSQL/infra is required.
