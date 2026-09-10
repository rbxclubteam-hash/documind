import type { ReactNode } from "react";
import type { DocumentResult } from "@/lib/api";
import {
  analyzerModeLabel,
  formatBytes,
  formatDate,
  statusLabel,
} from "@/lib/format";
import DocumentTypeBadge from "./DocumentTypeBadge";
import StructuredFields from "./StructuredFields";

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-0.5 break-words text-sm text-slate-800">{value}</dd>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-6">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">{title}</h3>
      {children}
    </section>
  );
}

export default function DocumentResultView({ doc }: { doc: DocumentResult }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2
          className="min-w-0 break-words text-lg font-semibold text-slate-900"
          title={doc.original_filename}
        >
          {doc.original_filename}
        </h2>
        <DocumentTypeBadge type={doc.document_type} />
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-4">
        <MetaItem label="Status" value={statusLabel(doc.status)} />
        <MetaItem label="Analyzer" value={analyzerModeLabel(doc.analyzer_mode)} />
        <MetaItem label="Processed" value={formatDate(doc.created_at)} />
        <MetaItem label="File size" value={formatBytes(doc.size_bytes)} />
      </dl>

      <Section title="Summary">
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
          {doc.summary || "No summary was produced."}
        </p>
      </Section>

      <Section title="Structured fields">
        <StructuredFields fields={doc.extracted_fields} />
      </Section>

      <Section title="Text preview">
        <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-md border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">
          {doc.text_preview || "No text preview is available."}
        </pre>
      </Section>
    </article>
  );
}
