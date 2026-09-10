from types import SimpleNamespace

import pytest

from app.analyzers import AnalyzerError, AnalyzerNotConfigured, DemoAnalyzer, OpenAIAnalyzer


@pytest.mark.parametrize(
    ("filename", "text", "expected"),
    [
        ("invoice.pdf", "INVOICE\nTotal: $100", "invoice"),
        ("terms.docx", "SERVICE AGREEMENT\nEffective Date: 2026-01-01", "contract"),
        ("resume.docx", "Jane Doe\nSkills: Python, FastAPI", "resume"),
        ("notes.docx", "Project Notes\nWeekly planning update.", "other"),
    ],
)
def test_demo_classification(filename: str, text: str, expected: str) -> None:
    result = DemoAnalyzer().analyze(text, filename)
    assert result.document_type == expected
    assert result.summary


def test_invoice_fields_have_exact_shape() -> None:
    result = DemoAnalyzer().analyze(
        "Vendor: Acme Studio\nInvoice Number: INV-42\nInvoice Date: 2026-08-01\n"
        "Total Amount: $1,250.00\nCurrency: USD",
        "invoice.pdf",
    )
    assert result.extracted_fields.model_dump() == {
        "vendor": "Acme Studio",
        "invoice_number": "INV-42",
        "invoice_date": "2026-08-01",
        "total_amount": "$1,250.00",
        "currency": "USD",
    }


def test_contract_fields_have_exact_shape() -> None:
    result = DemoAnalyzer().analyze(
        "SERVICE AGREEMENT\nParties: Acme Ltd; Northwind LLC\nEffective Date: 2026-01-01\n"
        "Expiration Date: 2026-12-31\nContract Value: USD 12,000\nSubject: Design services",
        "contract.docx",
    )
    assert result.extracted_fields.model_dump() == {
        "parties": ["Acme Ltd", "Northwind LLC"],
        "effective_date": "2026-01-01",
        "expiration_date": "2026-12-31",
        "contract_value": "USD 12,000",
        "subject": "Design services",
    }


def test_resume_fields_have_exact_shape() -> None:
    result = DemoAnalyzer().analyze(
        "Name: Jane Doe\nEmail: jane@example.com\nPhone: +1 555 010 2020\n"
        "Current Role: Backend Engineer\nSkills: Python, FastAPI, PostgreSQL",
        "resume.docx",
    )
    assert result.extracted_fields.model_dump() == {
        "candidate_name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1 555 010 2020",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "current_or_recent_role": "Backend Engineer",
    }


def test_other_fields_have_exact_shape() -> None:
    result = DemoAnalyzer().analyze("Quarterly Notes\nProduct roadmap planning", "notes.docx")
    fields = result.extracted_fields.model_dump()
    assert set(fields) == {"title", "key_terms"}
    assert fields["title"] == "Quarterly Notes"


def test_demo_analyzer_needs_no_api_key() -> None:
    assert DemoAnalyzer().analyze("Simple notes", "notes.docx").summary


def test_openai_missing_configuration() -> None:
    with pytest.raises(AnalyzerNotConfigured):
        OpenAIAnalyzer(None, None)


class FakeCompletions:
    def __init__(self, output: str):
        self.output = output

    def create(self, **_: object) -> SimpleNamespace:
        message = SimpleNamespace(content=self.output)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_openai_normalized_success() -> None:
    output = (
        '{"document_type":"other","summary":"Release notes.",'
        '"extracted_fields":{"title":"Release Notes","key_terms":["release"]}}'
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(output)))
    result = OpenAIAnalyzer("test-key", "test-model", client=client).analyze("Text", "x.docx")
    assert result.document_type == "other"
    assert result.extracted_fields.model_dump()["key_terms"] == ["release"]


@pytest.mark.parametrize("output", ["not-json", '{"document_type":"other","summary":"x"}'])
def test_openai_invalid_result_is_controlled(output: str) -> None:
    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(output)))
    with pytest.raises(AnalyzerError):
        OpenAIAnalyzer("test-key", "test-model", client=client).analyze("Text", "x.docx")
