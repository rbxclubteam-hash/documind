import type { AnalyzerMode, DocumentStatus, DocumentType } from "./api";

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  const decimals = value >= 10 ? 0 : 1;
  return `${value.toFixed(decimals)} ${units[index]}`;
}

export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function humanizeKey(key: string): string {
  const spaced = key
    .replace(/_or_/g, " / ")
    .replace(/[_-]+/g, " ")
    .trim();
  if (!spaced) return key;
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export function documentTypeLabel(type: DocumentType): string {
  switch (type) {
    case "invoice":
      return "Invoice";
    case "contract":
      return "Contract";
    case "resume":
      return "Resume";
    default:
      return "Other";
  }
}

export function analyzerModeLabel(mode: AnalyzerMode): string {
  return mode === "openai" ? "OpenAI analysis" : "Document analysis";
}

export function statusLabel(status: DocumentStatus): string {
  return status === "completed" ? "Completed" : String(status);
}
