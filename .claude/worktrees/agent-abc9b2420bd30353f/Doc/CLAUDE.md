# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository status

This repo is **pre-implementation**. It currently contains only two Chinese-language specification documents and an LLM API key file — no source code, no build system, no tests yet. All work is greenfield and is driven by the two specs:

- `文档.md` — high-level design rationale and tech-stack survey (background reading only; not a contract).
- `文档2.MD` — **the authoritative executable specification.** Every implementation decision must trace back to this file. Read it fully before writing any code.
- `LLMAPKKEY.txt` — contains a hardcoded LLM API key and `base_url` for the chat/completion model (gpt-5.4 via `api.krill-ai.com`). This is the LLM to call from `llm_service.py` for all non-embedding/rerank LLM calls. Do not commit additional secrets; load keys from `.env` per the spec.

## Project intent

A cybersecurity-domain RAG knowledge-base system (`cybersec-rag-agent`) for private material: cybersecurity laws/regulations, standards (e.g. GB/T 22239), and textbooks (PDF/EPUB/Markdown/TXT). It is **not** a general chatbot — it does structured ingestion, hybrid retrieval, citation-grounded answers, version/incremental updates, and a defensive safety boundary.

## Execution discipline (from §22 of 文档2.MD)

This is the most important thing to internalize:

1. **Implement strictly in Phase order (Phase 0 → Phase 10).** One phase at a time.
2. **Only implement what the current Phase explicitly requires.** Do not pre-build later-phase features. If a module isn't needed yet, leave a `TODO` placeholder — do not flesh it out to "look complete."
3. When a spec detail is undefined, follow the **default decision table** (below) rather than inventing design.
4. Each completed Phase must produce: files changed, run commands, test commands, and acceptance-criteria verification.
5. The spec says to stop after Phase 0 and await instructions. Respect that stop point unless told otherwise.

## Architecture (two pipelines)

**Ingest pipeline** (§4.1): upload → save raw file → `file_hash` → create `document` + `document_version` + `ingest_task(queued)` → Celery async → parse → clean → chunk (parent/child) → `chunk_hash` → write PostgreSQL → embed **child chunks only** → upsert Qdrant → write PostgreSQL FTS `search_tsv` → task `completed`.

**Query pipeline** (§4.2): user input → `safety_guard` → `intent_classifier` → `term_expander` → `query_rewriter` → `metadata_filter_builder` → vector search (Qdrant) → keyword search (PostgreSQL FTS) → RRF fusion → reranker → parent-context回取 → `answer_generator` → `citation_checker` → answer + citations.

Layering rule: **API routes must not contain business logic.** Routes call services; all external model calls go through a service-layer wrapper (`llm_service.py`, `embedding_service.py`, `reranker.py`). Python 3.11+, Pydantic v2, SQLAlchemy 2.x, type annotations required, all config from `.env`.

## Default decision table (non-obvious, must-follow)

These are fixed constraints from `文档2.MD` §2 — do not deviate even if a more "standard" pattern seems available:

- **Upload/replace semantics (§2.1):** `POST /documents/upload` only creates new documents — it never attaches to an existing document. New versions come only via `POST /documents/{id}/replace`. No title-based version auto-matching. Do not accept `document_id` on the upload endpoint.
- **Incremental update (§2.2):** Updates are **chunk-diff only**. Re-parse and re-chunk only the replaced document; compare `chunk_hash` sets to compute added/removed/unchanged/updated; embed **only** added/changed child chunks; reuse unchanged chunks' existing embeddings and index data. Never rebuild the whole vector store; never re-embed the whole library for a single-doc update.
- **Index only child chunks (§2.3):** Parent chunks are context-fill only — they never enter Qdrant and never enter the keyword index. On a child hit, fetch the parent via `parent_chunk_id` for answer generation.
- **Task state is dual-write (§2.4):** Redis for live state, PostgreSQL `ingest_tasks` table for persistence/audit. The business API reads from the DB; may supplement with Redis. Do not shoehorn task state into `documents`/`document_versions`.
- **Models (§2.5–2.7):** Embedding = **local Qwen Embedding** loaded in-process (not an OpenAI-compatible proxy). Reranker = **local Qwen3 Reranker** in-process. The LLM (chat/completion) is an **API call** using the key in `LLMAPKKEY.txt`. Both local model dirs live under `models/embedding/` and `models/reranker/` at the repo root; `models/` **must be in `.gitignore`** and paths read from config — never commit model files.
- **Default retrieval scope (§2.8):** Only `documents.status=active` AND `document_versions.version_status=active` AND `chunks.is_active=true` AND `current_version_id` of the document. Loosen only when the user explicitly asks about old/new version differences.
- **Citation minimum (§2.9):** Every citation must include `chunk_id`, `doc_title`, `page_start`, `page_end`. Add `chapter`/`section`/`article_no` only when actually identifiable; otherwise return `null`. **Never fabricate** article/chapter numbers.
- **Law/standard chunking (§2.10, §10.2):** Split by 章→节→条; when a single 条 exceeds **800 tokens**, sub-split into natural-paragraph child chunks. The article number must be retained on every sub-chunk.

## Tech stack & layout

Stack (§3): FastAPI, Pydantic v2, SQLAlchemy 2.x + Alembic, PostgreSQL (incl. FTS `tsvector` for keyword search — **no OpenSearch in MVP**), Redis, Celery, Qdrant, PyMuPDF + pdfplumber for PDF. Dep management via `pyproject.toml`; tests via `pytest`. Primary keys are UUIDs; timestamps use DB time; API returns ISO-8601 strings.

The intended project root is `cybersec-rag-agent/` with this layout (full tree in §5 of `文档2.MD`): `backend/app/{api,db,models,schemas,services,workers,prompts,utils}`, `backend/tests/`, `backend/alembic/`, plus root `docker-compose.yml`, `.env.example`, `pyproject.toml`, and `models/{embedding,reranker}/`.

## Key data model notes

Six tables (full DDL in §6): `documents` (logical doc, `doc_type` enum: law/regulation/standard/textbook/case/policy/manual/note/other; `status`: active/deleted/archived), `document_versions` (version_no, file_hash, `version_status`: active/expired/amended/draft/unknown), `chunks` (parent/child, `chunk_hash`, `search_tsv TSVECTOR`, rich metadata JSONB, `is_active`), `ingest_tasks` (task_type ingest/replace/reindex; status queued/processing/completed/failed), `query_logs`, `feedback`. Note `chunks` carries both the `chunk_hash` for diff and the `search_tsv` GIN-indexed FTS column.

## MVP scope (§1.1 / §1.2)

In scope: FastAPI backend, PostgreSQL, Redis, Qdrant, PDF/MD/TXT parsing, cleaning, law/standard/textbook chunking, parent-child chunks, local embedding, query rewrite, metadata filter, vector+FTS hybrid retrieval, RRF fusion, answer generation, citations, replace + incremental update, soft delete, attack-request safety guard, basic eval.

**Explicitly out of MVP** (do not build): OpenSearch, multi-tenancy, permissions, complex OCR, any frontend, **LangGraph**, auto-syncing regulations from the web, automatic taxonomy construction.

## Safety boundary (§13.1, §20)

`safety_guard` runs first in the query pipeline. Allow: regulation/standard explanation, textbook concepts, high-level vulnerability explanation, fix/detection/defense/incident-response guidance. Refuse or defensively redirect: real-target attack steps, attack-script generation, WAF/EDR/IDS bypass, malware/AV-evasion/persistence, mass exploitation, credential theft, destructive actions, unauthorized intrusion. Output is fixed JSON `{action, risk_type, reason, safe_response}` with `action ∈ allow|refuse|redirect`. Rule-match first, LLM classification only when rules are ambiguous; all refusals/redirects are logged to `query_logs`.

## Useful file pointers in the spec

- Fixed retrieval params (vector/keyword top_k=30, RRF k=60, rerank input=20, final evidence=5): §14.2–14.3.
- RRF reference implementation: §14.3.
- API endpoint contracts (health, upload, task status, document list/detail, replace, delete, query/answer, query/retrieve debug, query/rewrite debug, eval/run): §17.
- Prompt files live in `app/prompts/*.md` (intent_classifier, query_rewriter, answer_generator, safety_guard, citation_checker): §5, §13, §15, §16.
- Phase-by-phase acceptance criteria: §21 (Phase 0 = scaffold + `GET /health` + Postgres/Redis/Qdrant via docker-compose, no RAG logic).
