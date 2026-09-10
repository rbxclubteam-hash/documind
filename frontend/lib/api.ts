export type DocumentType = "invoice" | "contract" | "resume" | "other";
export type AnalyzerMode = "demo" | "openai";
export type DocumentStatus = "completed";

export interface DocumentResult {
  id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  document_type: DocumentType;
  summary: string;
  extracted_fields: Record<string, unknown>;
  text_preview: string;
  analyzer_mode: AnalyzerMode;
  status: DocumentStatus;
  created_at: string;
}

export interface RecentDocument {
  id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  document_type: DocumentType;
  summary: string;
  analyzer_mode: AnalyzerMode;
  status: DocumentStatus;
  created_at: string;
}

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:8001";

const NETWORK_MESSAGE = "Could not reach the server. Please try again.";

export class ApiError extends Error {
  readonly status: number;
  readonly userMessage: string;

  constructor(status: number, userMessage: string) {
    super(userMessage);
    this.name = "ApiError";
    this.status = status;
    this.userMessage = userMessage;
  }
}

function friendlyMessage(status: number, detail?: string): string {
  switch (status) {
    case 413:
      return "File is too large. Maximum size is 10 MB.";
    case 415:
      return "Unsupported file type. Upload a text-based PDF or DOCX.";
    case 422:
      return "No extractable text was found. Scanned PDFs are not supported.";
    case 404:
      return "Document not found.";
    case 503:
      return "Document analyzer is not configured.";
    case 502:
      return "Document analysis failed. Please try again.";
    default:
      if (status >= 500) return "The server had a problem. Please try again.";
      return detail && detail.trim()
        ? detail
        : "The request could not be completed. Please try again.";
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  let detail: string | undefined;
  let detailIsArray = false;
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body?.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body?.detail)) {
      detailIsArray = true;
    }
  } catch {
    // response had no JSON body
  }
  if (res.status === 422 && detailIsArray) {
    return new ApiError(422, "The upload request was invalid. Please choose a file and try again.");
  }
  return new ApiError(res.status, friendlyMessage(res.status, detail));
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { signal, cache: "no-store" });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, NETWORK_MESSAGE);
  }
  if (!res.ok) throw await toApiError(res);
  return (await res.json()) as T;
}

export function fetchRecentDocuments(signal?: AbortSignal): Promise<RecentDocument[]> {
  return getJson<RecentDocument[]>("/api/documents", signal);
}

export function fetchDocument(id: string, signal?: AbortSignal): Promise<DocumentResult> {
  return getJson<DocumentResult>(`/api/documents/${encodeURIComponent(id)}`, signal);
}

export async function uploadDocument(file: File): Promise<DocumentResult> {
  const form = new FormData();
  form.append("file", file);
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/api/documents`, { method: "POST", body: form });
  } catch {
    throw new ApiError(0, NETWORK_MESSAGE);
  }
  if (!res.ok) throw await toApiError(res);
  return (await res.json()) as DocumentResult;
}

export function getUserMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return err.userMessage;
  if (err && typeof err === "object" && "userMessage" in err) {
    const message = (err as Record<string, unknown>).userMessage;
    if (typeof message === "string") return message;
  }
  return fallback;
}
