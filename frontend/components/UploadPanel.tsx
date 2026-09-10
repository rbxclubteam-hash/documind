"use client";

import { useRef, useState } from "react";
import { getUserMessage, uploadDocument, type DocumentResult } from "@/lib/api";
import { formatBytes } from "@/lib/format";

const MAX_BYTES = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".docx"];

type State =
  | { kind: "idle" }
  | { kind: "selected"; file: File }
  | { kind: "processing"; file: File }
  | { kind: "error"; message: string; file: File | null }
  | { kind: "done"; fileName: string };

function validate(file: File): string | null {
  const name = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext))) {
    return "Unsupported file type. Upload a text-based PDF or DOCX.";
  }
  if (file.size > MAX_BYTES) {
    return "File is too large. Maximum size is 10 MB.";
  }
  if (file.size === 0) {
    return "That file appears to be empty. Choose a different file.";
  }
  return null;
}

export default function UploadPanel({
  onUploaded,
  onReset,
}: {
  onUploaded: (doc: DocumentResult) => void;
  onReset: () => void;
}) {
  const [state, setState] = useState<State>({ kind: "idle" });
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const busy = state.kind === "processing";

  function pick(file: File | undefined | null) {
    if (!file) return;
    const error = validate(file);
    if (error) {
      setState({ kind: "error", message: error, file: null });
      return;
    }
    setState({ kind: "selected", file });
  }

  async function submit(file: File) {
    setState({ kind: "processing", file });
    try {
      const doc = await uploadDocument(file);
      setState({ kind: "done", fileName: doc.original_filename });
      onUploaded(doc);
    } catch (err) {
      setState({
        kind: "error",
        message: getUserMessage(err, "Something went wrong. Please try again."),
        file,
      });
    }
  }

  function reset() {
    setState({ kind: "idle" });
    if (inputRef.current) inputRef.current.value = "";
    onReset();
  }

  if (state.kind === "done") {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3">
        <p className="text-sm text-emerald-800">
          Processed <span className="font-medium">{state.fileName}</span>. The result is
          shown below.
        </p>
        <button
          type="button"
          onClick={reset}
          className="rounded-md border border-emerald-300 bg-white px-3 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-100"
        >
          Upload another
        </button>
      </div>
    );
  }

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        if (!busy) setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragActive(false);
        if (busy) return;
        pick(event.dataTransfer.files?.[0]);
      }}
      className={`rounded-lg border-2 border-dashed p-6 text-center transition-colors sm:p-10 ${
        dragActive ? "border-indigo-400 bg-indigo-50" : "border-slate-300 bg-white"
      }`}
    >
      <p className="text-sm font-medium text-slate-700">Drag and drop a document here</p>
      <p id="upload-constraints" className="mt-1 text-xs text-slate-500">
        PDF or DOCX · Max 10 MB · Text-based files only (no scanned PDFs)
      </p>

      <div className="mt-4">
        <label className="inline-flex cursor-pointer items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-indigo-600">
          Choose file
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="sr-only"
            disabled={busy}
            aria-describedby="upload-constraints"
            onChange={(event) => pick(event.target.files?.[0])}
          />
        </label>
      </div>

      {(state.kind === "selected" || state.kind === "processing") && (
        <div className="mx-auto mt-5 max-w-sm rounded-md border border-slate-200 bg-slate-50 p-3 text-left">
          <p
            className="truncate text-sm font-medium text-slate-800"
            title={state.file.name}
          >
            {state.file.name}
          </p>
          <p className="text-xs text-slate-500">{formatBytes(state.file.size)}</p>
        </div>
      )}

      {state.kind === "processing" && (
        <p
          className="mt-4 flex items-center justify-center gap-2 text-sm text-slate-600"
          role="status"
        >
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
            aria-hidden
          />
          Processing document…
        </p>
      )}

      {state.kind === "selected" && (
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          <button
            type="button"
            onClick={() => submit(state.file)}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Analyze document
          </button>
          <button
            type="button"
            onClick={reset}
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Clear
          </button>
        </div>
      )}

      {state.kind === "error" && (
        <div className="mx-auto mt-5 max-w-sm rounded-md border border-red-200 bg-red-50 p-3 text-left">
          <p className="text-sm text-red-700">{state.message}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {state.file && (
              <button
                type="button"
                onClick={() => {
                  if (state.kind === "error" && state.file) submit(state.file);
                }}
                className="rounded border border-red-300 bg-white px-2.5 py-1 text-xs font-medium text-red-700 hover:bg-red-100"
              >
                Try again
              </button>
            )}
            <button
              type="button"
              onClick={reset}
              className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
            >
              Choose another file
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
