"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ApiError,
  fetchDocument,
  getUserMessage,
  type DocumentResult,
} from "@/lib/api";
import DocumentResultView from "@/components/DocumentResultView";

type State =
  | { kind: "loading" }
  | { kind: "notfound" }
  | { kind: "error"; message: string }
  | { kind: "ready"; doc: DocumentResult };

export default function DocumentDetailPage() {
  const params = useParams();
  const rawId = params?.id;
  const id = Array.isArray(rawId) ? rawId[0] : rawId;
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    setState({ kind: "loading" });
    fetchDocument(id, controller.signal)
      .then((doc) => setState({ kind: "ready", doc }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.status === 404) {
          setState({ kind: "notfound" });
          return;
        }
        setState({
          kind: "error",
          message: getUserMessage(err, "Could not load this document."),
        });
      });
    return () => controller.abort();
  }, [id]);

  return (
    <div className="space-y-5">
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-700"
      >
        <span aria-hidden>&larr;</span> Back to documents
      </Link>

      {state.kind === "loading" && (
        <p className="text-sm text-slate-500">Loading document…</p>
      )}

      {state.kind === "notfound" && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-700">
          Document not found.
        </div>
      )}

      {state.kind === "error" && (
        <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-700">
          {state.message}
        </div>
      )}

      {state.kind === "ready" && <DocumentResultView doc={state.doc} />}
    </div>
  );
}
