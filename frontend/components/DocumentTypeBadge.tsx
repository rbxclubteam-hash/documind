import type { DocumentType } from "@/lib/api";
import { documentTypeLabel } from "@/lib/format";

const STYLES: Record<DocumentType, string> = {
  invoice: "border-amber-200 bg-amber-50 text-amber-700",
  contract: "border-indigo-200 bg-indigo-50 text-indigo-700",
  resume: "border-emerald-200 bg-emerald-50 text-emerald-700",
  other: "border-slate-200 bg-slate-100 text-slate-600",
};

export default function DocumentTypeBadge({ type }: { type: DocumentType }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${
        STYLES[type] ?? STYLES.other
      }`}
    >
      {documentTypeLabel(type)}
    </span>
  );
}
