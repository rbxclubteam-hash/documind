import { humanizeKey } from "@/lib/format";

function FieldValue({ value }: { value: unknown }) {
  if (value === null || value === undefined || value === "") {
    return <span className="text-slate-400">Not detected</span>;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-slate-400">Not detected</span>;
    }
    return (
      <ul className="flex flex-wrap gap-1.5">
        {value.map((item, index) => (
          <li
            key={index}
            className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
          >
            {typeof item === "object" ? JSON.stringify(item) : String(item)}
          </li>
        ))}
      </ul>
    );
  }
  if (typeof value === "boolean") {
    return <span>{value ? "Yes" : "No"}</span>;
  }
  if (typeof value === "object") {
    return (
      <pre className="overflow-x-auto whitespace-pre-wrap break-words text-xs text-slate-600">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }
  return <span className="break-words">{String(value)}</span>;
}

export default function StructuredFields({
  fields,
}: {
  fields: Record<string, unknown>;
}) {
  const entries = Object.entries(fields ?? {});
  if (entries.length === 0) {
    return <p className="text-sm text-slate-500">No structured fields were extracted.</p>;
  }
  return (
    <dl className="divide-y divide-slate-100 rounded-md border border-slate-200">
      {entries.map(([key, value]) => (
        <div
          key={key}
          className="grid grid-cols-1 gap-1 px-3 py-2.5 sm:grid-cols-3 sm:gap-3"
        >
          <dt className="text-sm font-medium text-slate-600">{humanizeKey(key)}</dt>
          <dd className="text-sm text-slate-900 sm:col-span-2">
            <FieldValue value={value} />
          </dd>
        </div>
      ))}
    </dl>
  );
}
