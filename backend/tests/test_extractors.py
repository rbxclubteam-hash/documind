import pytest
from conftest import docx_bytes, pdf_bytes

from app.extractors import ExtractionError, extract_docx, extract_pdf, extract_text


def test_pdf_extraction() -> None:
    assert "Invoice 123" in extract_pdf(pdf_bytes("Invoice 123"))


def test_docx_extraction_includes_paragraphs_and_tables() -> None:
    content = docx_bytes(["Contract"], [["Party", "Acme"]])
    result = extract_docx(content)
    assert "Contract" in result
    assert "Party | Acme" in result


def test_extractor_dispatches_by_extension() -> None:
    assert extract_text(docx_bytes(["Resume"]), "profile.docx") == "Resume"


def test_invalid_pdf_raises_controlled_error() -> None:
    with pytest.raises(ExtractionError):
        extract_pdf(b"not a pdf")
