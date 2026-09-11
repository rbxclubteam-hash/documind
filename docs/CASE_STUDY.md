# DocuMind — Case Study

A portfolio demonstration of a document-intelligence workflow: upload a business
document, extract and structure its content, and persist a reviewable result. Built with
FastAPI, PostgreSQL, and Next.js, run locally with Docker Compose.

All data is fictional demo material. There are no real customers, no production
deployment, and no processing-accuracy claims — this document describes what was built
and how.

## Business problem

Invoices, contracts, and resumes typically arrive as PDFs or Word files. They're
readable by a person, but not directly usable by anything downstream — a bookkeeping
tool, a search index, a review queue. Someone still has to open each file and manually
pull out the vendor, the total, the parties, or the candidate's skills. Turning that
first read into structured, reviewable data is a small but recurring piece of a lot of
back-office workflows.

## Product goal

Demonstrate a complete document-processing workflow, end to end, on a real stack:

1. Accept a real file upload, validated server-side (type, size).
2. Extract the document's actual text.
3. Map that text into a normalized shape: a document type plus a small set of
   type-specific fields, alongside a short summary.
4. Persist the result — not just render it once — so it can be found again.
5. Let a reviewer browse recent uploads and reopen any one of them.

Deliberately **not** in this demo: authentication, multi-user workspaces, OCR for
scanned/image PDFs, search, tagging, folders, or document editing. Those are real-product
concerns; the demo stays focused on the upload → structure → persist → review loop.

## Implemented workflow

`Upload → Extraction → Structured analysis → Persistence → Recent Documents → Detail review`

- **Upload** (`/`): a drag-and-drop / file-picker area accepts a text-based PDF or DOCX
  up to 10 MB. Type and size are validated both in the UI and by the API.
- **Extraction + analysis**: `POST /api/documents` runs synchronously — no background
  job, no polling. It extracts the document's text, classifies it as
  invoice / contract / resume / other, writes a short summary, and extracts
  type-specific structured fields (e.g. vendor / invoice number / total / currency for
  an invoice).
- **Persistence**: the document's metadata, the **full extracted text**, and the
  normalized analysis are written to PostgreSQL. The original uploaded file is discarded
  after processing.
- **Recent Documents**: the homepage lists the most recent uploads (newest first), each
  linking to its detail page.
- **Detail review** (`/documents/[id]`): reopens a persisted record — filename, document
  type, status, analyzer mode, timestamp, structured fields, and a preview of the
  extracted text.

## Technical approach

| Concern | Choice |
| --- | --- |
| API | FastAPI, a small frozen contract (`docs/api-contract.md`) — 4 endpoints, no more |
| Processing | Synchronous, inside the upload request — no queue, no worker |
| Persistence | PostgreSQL via SQLAlchemy; schema managed with Alembic |
| Extraction | Real text extraction from PDF/DOCX (no OCR; scanned PDFs are rejected) |
| Analysis | A deterministic, offline heuristic analyzer by default (see below) |
| Frontend | Next.js (App Router) + TypeScript + Tailwind CSS |
| Local run | Docker Compose: `db`, `backend`, `frontend`, migrations applied on backend start |

The API surface is intentionally small: upload, list recent, and fetch one document's
detail. No endpoint exists that the two frontend routes don't need.

## Data integrity / persistence

Every successfully processed document is written to PostgreSQL with:

- Metadata: original filename, MIME type, size, document type, status, timestamp.
- The **full extracted text** (not just a preview) — stored so the underlying content
  stays reviewable even though the original file is gone.
- The normalized structured analysis (summary + type-specific fields) as JSON.

The API itself only ever returns a **preview** of the extracted text (up to 4000
characters) — the full text lives in the database, not in every API response. This keeps
response payloads small while still making the complete content available where it
matters (the persisted record). A document reopened from Recent Documents reflects
exactly what was persisted at upload time, not a fresh re-analysis.

## Demo vs. production boundaries

The default and only analyzer used in this demo, `ANALYZER_MODE=demo`, is
**deterministic and heuristic** — regex- and pattern-based extraction over the real
extracted text, running fully offline with no API key. It is explicitly **not** described
as AI-generated analysis anywhere in the product or these docs, and its output is
reproducible for the same input.

An optional `ANALYZER_MODE=openai` path exists in the codebase behind the same output
contract (same document types, same field shapes), selected explicitly via
`OPENAI_API_KEY` + `OPENAI_MODEL` configuration. It is **not enabled or demonstrated** in
this portfolio candidate — no live model call is made here, and no accuracy claim is
made for either path.

No OCR: scanned or image-only PDFs are rejected with a clear error rather than silently
producing empty or wrong results.

## What this project demonstrates to a potential client

- **A complete file-processing workflow**, not a front-end mockup: real upload
  validation, real extraction, real persistence, real review UI.
- **A synchronous, dependency-light architecture** — no queues, workers, or extra
  infrastructure, appropriate for a first version of this kind of workflow.
- **Persistent structured data** with a clean boundary between what's returned by the
  API (a bounded preview) and what's stored (the complete extracted text).
- **A working document-review UX**: upload, structured result, recent list, and detail
  reopen, all wired to the same backend.
- **A reproducible, full-stack delivery**: the whole thing runs from one
  `docker compose up --build`, with a real sample document included for review.
