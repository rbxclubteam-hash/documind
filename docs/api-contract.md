DOCUMIND_API_CONTRACT_V1

# DocuMind MVP API & Data Contract

This contract is **frozen** after the bootstrap commit. Both the backend and frontend
tracks build against exactly what is written here.

## Product flow

Upload document → extract text → classify → summarize → extract structured fields →
persist to PostgreSQL → show result → reopen result from Recent Documents.

Processing is **synchronous** inside `POST /api/documents`. There are no queues and no
workers. The original binary file is **not persisted** after processing.

Persisted per document: metadata, the full extracted text, and the normalized analysis
result. The API only ever returns `text_preview` (up to 4000 characters), never the
full extracted text.

Supported inputs: text-based `.pdf` and `.docx`, maximum **10 MB**. No OCR.

## Routes

### Frontend

- `/` — Upload + Recent Documents
- `/documents/[id]` — persisted result

### API

- `GET /health`
- `POST /api/documents`
- `GET /api/documents`
- `GET /api/documents/{id}`

No additional API endpoints.

## Enums

**DocumentType:** `invoice` | `contract` | `resume` | `other`

**AnalyzerMode:** `demo` | `openai`

**DocumentStatus:** `completed`

## `GET /health`

```json
{ "status": "ok" }
```

## Document result

Returned by `POST /api/documents` (as `201`) and `GET /api/documents/{id}` (as `200`).

```json
{
  "id": "UUID",
  "original_filename": "string",
  "mime_type": "string",
  "size_bytes": 0,
  "document_type": "invoice | contract | resume | other",
  "summary": "string",
  "extracted_fields": {},
  "text_preview": "string",
  "analyzer_mode": "demo | openai",
  "status": "completed",
  "created_at": "RFC3339 UTC datetime"
}
```

The persisted database record additionally stores `extracted_text` (the full normalized
extracted text). The full extracted text does **not** need to be returned by the API.

`text_preview` is the first `<= 4000` characters of the normalized extracted text.

## `GET /api/documents` — Recent Documents

Returns the latest **20** documents, newest-first. No pagination.

Each item:

```json
{
  "id": "UUID",
  "original_filename": "string",
  "mime_type": "string",
  "size_bytes": 0,
  "document_type": "invoice | contract | resume | other",
  "summary": "string",
  "analyzer_mode": "demo | openai",
  "status": "completed",
  "created_at": "RFC3339 UTC datetime"
}
```

## `POST /api/documents` — Upload

`multipart/form-data` with a single field: `file`.

- Maximum size: 10 MB
- Supported: text-based `.pdf`, `.docx`
- Success: `201` with a Document result (see above)

## Structured field shapes

`extracted_fields` on the Document result is one of the following objects, matching
`document_type`.

### invoice

```json
{
  "vendor": "string | null",
  "invoice_number": "string | null",
  "invoice_date": "string | null",
  "total_amount": "string | null",
  "currency": "string | null"
}
```

### contract

```json
{
  "parties": ["string"],
  "effective_date": "string | null",
  "expiration_date": "string | null",
  "contract_value": "string | null",
  "subject": "string | null"
}
```

### resume

```json
{
  "candidate_name": "string | null",
  "email": "string | null",
  "phone": "string | null",
  "skills": ["string"],
  "current_or_recent_role": "string | null"
}
```

### other

```json
{
  "title": "string | null",
  "key_terms": ["string"]
}
```

## Errors

- `404` — `{"detail":"Document not found."}`
- `413` — `{"detail":"File exceeds the 10 MB limit."}`
- `415` — `{"detail":"Unsupported file type. Upload a text-based PDF or DOCX."}`
- `422` — `{"detail":"No extractable text found. Scanned PDFs are not supported."}`
- `503` — `{"detail":"Analyzer is not configured."}`
- `502` — `{"detail":"Document analysis failed."}`

FastAPI's standard `422` response remains valid for malformed request data such as a
missing multipart `file` field.

## Analyzer contract

Default: `ANALYZER_MODE=demo`.

**demo** — deterministic, heuristic, no external API, no API key, works offline. Used
for the local demo and the tests. It is not real AI and must not be described as such
in user-facing copy.

**openai** — optional, selected explicitly via `ANALYZER_MODE=openai`. Requires
`OPENAI_API_KEY` and `OPENAI_MODEL`. Returns the **same** normalized analysis contract
as `demo` (same `document_type` enum, same `summary` string, same `extracted_fields`
shapes).

There is no fallback chain and no other providers. If `ANALYZER_MODE=openai` but the
key/model are missing, `POST /api/documents` returns `503`
`{"detail":"Analyzer is not configured."}`.
