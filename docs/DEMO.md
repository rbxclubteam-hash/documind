# DocuMind — Demo walkthrough

A short, exact path through the strongest DocuMind workflow: upload the included sample
invoice, review the structured result, and confirm it persists. About one minute.

## Before you start

```bash
cp .env.example .env
docker compose up --build
```

Wait for the backend to report healthy, then open:

- **App:** <http://localhost:3001/>
- **API health:** <http://localhost:8001/health>

## 1. Upload the sample invoice (~20s)

1. On the homepage, under **Analyze a document**, click **Choose file** (or drag and
   drop) and select [`samples/sample_invoice.pdf`](../samples/sample_invoice.pdf) from
   the repository.
2. The dropzone shows the selected filename and size, then an **Analyze document**
   button.
3. Click **Analyze document**. Processing is synchronous — the button shows
   "Processing document…" briefly while the backend extracts and analyzes the file.

## 2. Review the structured result (~20s)

The page scrolls to a **Result** panel showing:

- **Status:** Completed · **Analyzer:** Document analysis · **Processed:** a timestamp ·
  **File size:** 954 B
- A **Summary** line drawn from the extracted text.
- **Structured fields** for the detected document type (**Invoice**): Vendor, Currency,
  Invoice date, Total amount, Invoice number.
- A **Text preview** showing the actual extracted text from the PDF.

> Point out: this is real extraction from the actual uploaded PDF, not placeholder
> content — the structured fields and the text preview both come from
> `samples/sample_invoice.pdf`'s real content. The **Analyzer** label reads "Document
> analysis" because the default analyzer is deterministic and offline, not a live AI
> call (see the README).

## 3. Confirm it appears in Recent Documents (~10s)

Scroll down (or click **Upload another**, then look below the upload area) to
**Recent Documents**. The document you just uploaded appears at the top — filename,
detected type badge, a short summary, status, and timestamp.

## 4. Reopen the persisted record (~10s)

1. Click the document's row in Recent Documents to open its detail page at
   `/documents/{id}`.
2. The detail page shows the same status, analyzer, structured fields, and text preview
   as the original result — reloaded from PostgreSQL, not kept in browser memory.
3. Click **Back to documents** to return to the homepage; the record remains in Recent
   Documents.

> Point out: reloading the detail page, or navigating away and back through Recent
> Documents, shows the same persisted result every time — this is a real database
> record, not client-side state.

## Optional: try an unsupported or oversized file

Dropping a non-PDF/DOCX file or one over 10 MB is rejected with a friendly message
before any upload is sent — the same limits are also enforced by the backend if bypassed
directly against the API (`415` for an unsupported type, `413` for over 10 MB).
