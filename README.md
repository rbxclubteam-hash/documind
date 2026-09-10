# DocuMind — Document Intelligence

DocuMind is a portfolio demo that turns a single uploaded document into a structured
result: you upload a text-based PDF or DOCX, and the backend synchronously extracts the
text, classifies the document (invoice / contract / resume / other), writes a short
summary, and pulls a small set of type-specific structured fields. The result is
persisted to PostgreSQL and shown on its own page, and the latest documents are listed
under Recent Documents so any result can be reopened later. Original files are not kept
after processing — only metadata, the full extracted text, and the normalized analysis
are stored.

## Stack

- **Backend:** FastAPI + PostgreSQL (SQLAlchemy, Alembic). Processing is synchronous
  inside `POST /api/documents` — no queues or workers.
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind CSS.
- **Local orchestration:** Docker Compose (`db`, `backend`, `frontend`).

The frozen API and data contract lives in [`docs/api-contract.md`](docs/api-contract.md).

## Frozen MVP flow

Upload document → extract text → classify → summarize → extract structured fields →
persist to PostgreSQL → show result → reopen from Recent Documents.

Supported inputs: text-based `.pdf` and `.docx`, up to 10 MB. No OCR — scanned PDFs are
rejected.

## Analyzer

The default analyzer is `ANALYZER_MODE=demo`: a **deterministic, heuristic** analyzer
that runs fully offline with no external API and no API key. It is what the local demo
and the tests use, and it is not real AI.

`ANALYZER_MODE=openai` is optional and must be selected explicitly; it requires
`OPENAI_API_KEY` and `OPENAI_MODEL` and returns the exact same normalized analysis
contract as the demo analyzer. There is no fallback chain and no other providers.

## Local run (placeholder)

The `backend/` and `frontend/` build contexts are added by their respective feature
branches; this repository currently contains only the shared foundation.

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3001
- Backend: http://localhost:8001
- Health: http://localhost:8001/health
