import json
import re
from collections.abc import Sequence
from typing import Protocol

from openai import OpenAI

from app.schemas import AnalysisResult, analysis_adapter


class AnalyzerError(RuntimeError):
    pass


class AnalyzerNotConfigured(AnalyzerError):
    pass


class Analyzer(Protocol):
    def analyze(self, text: str, filename: str) -> AnalysisResult: ...


def _match(patterns: Sequence[str], text: str) -> str | None:
    for pattern in patterns:
        found = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if found:
            return found.group(1).strip(" \t:|-.,")
    return None


def _list_after_label(label: str, text: str) -> list[str]:
    value = _match([rf"^{label}\s*[:|-]\s*(.+)$"], text)
    if not value:
        return []
    return [item.strip() for item in re.split(r"[,;|]", value) if item.strip()]


def _summary(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    first = re.split(r"(?<=[.!?])\s+", compact)[0]
    return (first[:277] + "...") if len(first) > 280 else first


class DemoAnalyzer:
    def analyze(self, text: str, filename: str) -> AnalysisResult:
        haystack = f"{filename}\n{text}".lower()
        if any(term in haystack for term in ("invoice", "invoice number", "amount due")):
            payload = self._invoice(text)
        elif any(term in haystack for term in ("agreement", "contract", "effective date")):
            payload = self._contract(text)
        elif any(
            term in haystack for term in ("resume", "curriculum vitae", "skills", "experience")
        ):
            payload = self._resume(text)
        else:
            payload = self._other(text)
        return analysis_adapter.validate_python(payload)

    def _invoice(self, text: str) -> dict[str, object]:
        amount = _match([r"(?:total(?: amount)?|amount due)\s*[:|-]?\s*([$€£]?\s?[\d,.]+)"], text)
        currency = _match([r"\b(USD|EUR|GBP|CAD|AUD)\b"], text)
        if not currency and amount:
            currency = {"$": "USD", "€": "EUR", "£": "GBP"}.get(amount.strip()[0])
        return {
            "document_type": "invoice",
            "summary": _summary(text),
            "extracted_fields": {
                "vendor": _match(
                    [r"^(?:vendor|from|company)\s*[:|-]\s*(.+)$", r"^([^\n]+)\n+invoice\b"],
                    text,
                ),
                "invoice_number": _match(
                    [r"invoice\s*(?:number|no\.?|#)\s*[:#-]?\s*([\w-]+)"], text
                ),
                "invoice_date": _match([r"invoice date\s*[:|-]\s*([^\n]+)"], text),
                "total_amount": amount,
                "currency": currency,
            },
        }

    def _contract(self, text: str) -> dict[str, object]:
        parties = _list_after_label("parties", text)
        if not parties:
            match = re.search(r"between\s+(.+?)\s+and\s+(.+?)(?:[.,\n]|$)", text, re.I)
            if match:
                parties = [match.group(1).strip(), match.group(2).strip()]
        return {
            "document_type": "contract",
            "summary": _summary(text),
            "extracted_fields": {
                "parties": parties,
                "effective_date": _match([r"effective date\s*[:|-]\s*([^\n]+)"], text),
                "expiration_date": _match(
                    [r"(?:expiration|expiry|end) date\s*[:|-]\s*([^\n]+)"], text
                ),
                "contract_value": _match(
                    [r"contract value\s*[:|-]\s*([^\n]+)", r"value\s*[:|-]\s*([^\n]+)"],
                    text,
                ),
                "subject": _match([r"subject\s*[:|-]\s*([^\n]+)"], text),
            },
        }

    def _resume(self, text: str) -> dict[str, object]:
        lines = text.splitlines()
        candidate_name = _match([r"^(?:name|candidate)\s*[:|-]\s*(.+)$"], text)
        if not candidate_name and lines:
            candidate_name = lines[0].strip()
        return {
            "document_type": "resume",
            "summary": _summary(text),
            "extracted_fields": {
                "candidate_name": candidate_name,
                "email": _match([r"([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})"], text),
                "phone": _match([r"(\+?[\d][\d\s().-]{7,}\d)"], text),
                "skills": _list_after_label("skills", text),
                "current_or_recent_role": _match(
                    [r"^(?:current role|recent role|role|title)\s*[:|-]\s*(.+)$"], text
                ),
            },
        }

    def _other(self, text: str) -> dict[str, object]:
        lines = text.splitlines()
        words = re.findall(r"[A-Za-z][A-Za-z-]{3,}", text.lower())
        stop = {"this", "that", "with", "from", "have", "will", "your", "about"}
        terms = list(dict.fromkeys(word for word in words if word not in stop))[:8]
        return {
            "document_type": "other",
            "summary": _summary(text),
            "extracted_fields": {"title": lines[0] if lines else None, "key_terms": terms},
        }


class OpenAIAnalyzer:
    def __init__(self, api_key: str | None, model: str | None, client: object | None = None):
        if not api_key or not model:
            raise AnalyzerNotConfigured("OpenAI analyzer is not configured.")
        self.model = model
        self.client = client or OpenAI(api_key=api_key)

    def analyze(self, text: str, filename: str) -> AnalysisResult:
        prompt = (
            "Analyze the document and return JSON only. Use exactly one document_type: "
            "invoice, contract, resume, or other. Return summary and extracted_fields with "
            "exactly the fields specified by the DocuMind contract; use null for missing scalar "
            "values and [] for missing lists.\n"
            f"Filename: {filename}\nDocument text:\n{text}"
        )
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            payload = json.loads(response.choices[0].message.content)
            return analysis_adapter.validate_python(payload)
        except Exception as exc:
            raise AnalyzerError("Document analysis failed.") from exc
