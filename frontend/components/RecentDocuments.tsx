"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchRecentDocuments,
  getUserMessage,
  type RecentDocument,
} from "@/lib/api";
import { formatDate, statusLabel } from "@/lib/format";
import DocumentTypeBadge from "./DocumentTypeBadge";

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; docs: RecentDocument[] };

export default function RecentDocuments({ refreshKey }: { refreshKey: number }) {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchRecentDocuments(controller.signal)
      .then((docs) => setState({ kind: "ready", docs }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          kind: "error",
          message: getUserMessage(err, "Could not load recent documents."),
        });
      });
    return () => controller.abort();
  }, [refreshKey]);

  return (
    <section aria-labelledby="recent-heading">
      <h2
        id="recent-heading"
        className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500"
      >
        Recent documents
      </h2>

      {state.kind === "loading" && (
        <p className="text-sm text-slate-500">Loading recent documents…</p>
      )}

      {state.kind === "error" && (
        <p className="rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-600">
          {state.message}
        </p>
      )}

      {state.kind === "ready" && state.docs.length === 0 && (
        <p className="rounded-md border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-500">
          No documents yet. Upload a PDF or DOCX to see it here.
        </p>
      )}

      {state.kind === "ready" && state.docs.length > 0 && (
        <ul className="divide-y divide-slate-100 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {state.docs.map((doc) => (
            <li key={doc.id}>
              <Link
                href={`/documents/${doc.id}`}
                className="flex flex-col gap-1.5 px-4 py-3 transition-colors hover:bg-slate-50 focus:bg-slate-50 focus:outline-none sm:flex-row sm:items-center sm:justify-between sm:gap-4"
              >
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2">
                    <span
                      className="truncate text-sm font-medium text-slate-900"
                      title={doc.original_filename}
                    >
                      {doc.original_filename}
                    </span>
                    <DocumentTypeBadge type={doc.document_type} />
                  </span>
                  <span className="mt-0.5 block line-clamp-2 text-xs text-slate-500">
                    {doc.summary || "No summary available."}
                  </span>
                </span>
                <span className="flex shrink-0 items-center gap-3 text-xs text-slate-400">
                  <span>{statusLabel(doc.status)}</span>
                  <span>{formatDate(doc.created_at)}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
