# DocuMind Frontend

English-only responsive UI for DocuMind, built against the frozen API contract in
[`../docs/api-contract.md`](../docs/api-contract.md).

- **Stack:** Next.js (App Router) + TypeScript + Tailwind CSS
- **Routes:** `/` (upload + Recent Documents) and `/documents/[id]` (saved result)
- **API base:** `NEXT_PUBLIC_API_BASE_URL` (local default `http://localhost:8001`),
  inlined at build time.

## Scripts

```bash
npm install
npm run typecheck   # tsc --noEmit
npm run lint        # next lint
npm run build       # production build (output: standalone)
npm run dev         # local dev server on :3000
```

## Docker

`Dockerfile` produces a standalone Next.js server on internal port `3000`. The root
`docker-compose.yml` maps host `3001 -> 3000` and passes `NEXT_PUBLIC_API_BASE_URL`
as both a build arg and a runtime env var.

## Notes

The default analyzer (`ANALYZER_MODE=demo`) is deterministic and offline. The UI uses
neutral wording ("Document analysis"); an `OpenAI analysis` label appears only when a
document's `analyzer_mode` is `openai`.
