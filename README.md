# Clinician-Facing Diagnosis Support System

A full-stack AI-powered clinical decision support platform that guides clinicians through a structured patient intake workflow and generates evidence-based diagnostic reports using a RAG (Retrieval-Augmented Generation) pipeline with human-in-the-loop review at critical stages.

## Overview

The system combines a LangGraph-orchestrated AI pipeline with a React frontend to assist clinicians in:

- Capturing structured patient demographics, chief complaints, vitals, and history
- Recommending systemic examinations based on clinical presentation
- Retrieving relevant clinical knowledge from indexed medical textbooks (Weaviate vector DB)
- Generating differential diagnoses with confidence-graded CRAG (Corrective RAG) validation
- Producing a final clinical report after 4 human-in-the-loop approval checkpoints

## Architecture

```
frontend/          React + TypeScript + Tailwind (Vite)
app/
  api/             FastAPI REST server (auth, pipeline, sessions, patients)
  pipeline/        LangGraph state machine (graph.py) + CRAG chain (crag.py)
  llm/             Azure OpenAI client + prompt templates
  retrieval/       Weaviate vector search + chapter/query builders
  indexing/        PDF ingestion → Weaviate index builder
  db/              Supabase Postgres (patients, sessions, HITL logs, reports)
  schemas/         Pydantic clinical data models
  validation/      AI output validators and normalizers
  worker/          Celery task queue (async pipeline execution)
scripts/           Dev/utility scripts
```

## Pipeline Stages

The LangGraph pipeline runs these stages, pausing at each HITL checkpoint for clinician review:

| Stage | Description | HITL |
|-------|-------------|------|
| 1A | Extract structured chief complaints from free text | — |
| 1B | Recommend systemic examinations | HITL 1 — exam approval |
| 2 | Collect systemic examination findings | HITL 2 — findings entry |
| 3 | Retrieve clinical knowledge, generate differentials | HITL 3 — diagnosis review |
| 3b | Flag and resolve missing/ambiguous data | HITL 3b — missing data |
| 4 | CRAG validation + final report generation | HITL 4 — confirmation |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Radix UI, Zustand, TanStack Query |
| Backend | FastAPI, LangGraph, Celery |
| LLM | Azure AI Foundry (GPT deployment) |
| Vector DB | Weaviate (cloud sandbox) + Cohere reranking |
| Embeddings | Hugging Face Inference API |
| Database | Supabase (Postgres + Auth) |
| Cache/Queue | Upstash Redis (Celery broker) |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Accounts: Supabase, Weaviate, Azure AI Foundry, Upstash Redis, Cohere, Hugging Face

### Backend

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in all values in .env

uvicorn app.api.server:app --reload
```

### Celery Worker

```bash
celery -A app.worker.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies API requests to `http://localhost:8000`.

### Index Medical Textbooks

Place PDF textbook files outside the repo (they are copyrighted), then set `DOC_PATH` in `.env` and run:

```bash
python -m app.indexing.build_index
```

## Environment Variables

See [`.env.example`](.env.example) for all required variables:

- `AZURE_OPENAI_API_KEY` / `AZURE_FOUNDRY_ENDPOINT` / `AZURE_FOUNDRY_DEPLOYMENT` — LLM
- `WEAVIATE_CLUSTER` / `WEAVIATE_API_KEY` / `COLLECTION_NAME` — vector store
- `HF_API_KEY` — embeddings
- `COHERE_API_KEY` — reranking
- `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_KEY` / `SUPABASE_DB_URL` — database
- `UPSTASH_REDIS_URL` — Celery broker

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/signup` | Register a new doctor account |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Current doctor profile |
| POST | `/pipeline/start` | Start a new pipeline run |
| POST | `/pipeline/resume/{thread_id}` | Resume a paused HITL step |
| GET | `/pipeline/state/{thread_id}` | Get current pipeline state |
| GET | `/sessions` | List all sessions for authenticated doctor |
| GET | `/sessions/{thread_id}` | Single session detail |
| GET | `/patients` | List all patients |
| GET | `/patients/{patient_id}` | Patient detail + session history |
| GET | `/patients/{patient_id}/reports` | All final reports for a patient |
