import uuid
from datetime import UTC, datetime, timedelta

from conftest import docx_bytes, pdf_bytes
from sqlalchemy import func, select

from app.analyzers import AnalyzerError
from app.config import Settings, get_settings
from app.db import SessionLocal
from app.main import MAX_FILE_SIZE, app
from app.models import AnalyzerMode, Document, DocumentStatus, DocumentType

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def upload_docx(client, text: str, filename: str = "notes.docx"):
    return client.post(
        "/api/documents",
        files={"file": (filename, docx_bytes(text.splitlines()), DOCX_MIME)},
    )


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_valid_pdf_upload_and_persistence(client) -> None:
    response = client.post(
        "/api/documents",
        files={
            "file": (
                "invoice.pdf",
                pdf_bytes("Invoice Number: INV-1\nTotal: $50"),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["document_type"] == "invoice"
    assert payload["status"] == "completed"
    assert payload["analyzer_mode"] == "demo"
    assert payload["text_preview"]
    with SessionLocal() as session:
        saved = session.get(Document, uuid.UUID(payload["id"]))
        assert saved is not None
        assert "Invoice Number" in saved.extracted_text


def test_valid_docx_upload(client) -> None:
    response = upload_docx(client, "Jane Doe\nSkills: Python, FastAPI", "resume.docx")
    assert response.status_code == 201
    assert response.json()["document_type"] == "resume"


def test_unsupported_format(client) -> None:
    response = client.post("/api/documents", files={"file": ("image.png", b"png", "image/png")})
    assert response.status_code == 415
    assert response.json() == {"detail": "Unsupported file type. Upload a text-based PDF or DOCX."}


def test_mime_extension_mismatch_is_unsupported(client) -> None:
    response = client.post("/api/documents", files={"file": ("invoice.pdf", b"x", DOCX_MIME)})
    assert response.status_code == 415


def test_oversized_file(client) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("large.docx", b"x" * (MAX_FILE_SIZE + 1), DOCX_MIME)},
    )
    assert response.status_code == 413
    assert response.json() == {"detail": "File exceeds the 10 MB limit."}


def test_empty_pdf_is_unprocessable_and_not_persisted(client) -> None:
    response = client.post(
        "/api/documents", files={"file": ("scan.pdf", pdf_bytes(), "application/pdf")}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "No extractable text found. Scanned PDFs are not supported."
    }
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_preview_is_limited_but_full_text_is_stored(client) -> None:
    long_text = "Project notes " * 500
    response = upload_docx(client, long_text)
    assert response.status_code == 201
    payload = response.json()
    assert len(payload["text_preview"]) <= 4000
    with SessionLocal() as session:
        saved = session.get(Document, uuid.UUID(payload["id"]))
        assert saved is not None
        assert len(saved.extracted_text) > 4000


def make_document(index: int, created_at: datetime) -> Document:
    return Document(
        original_filename=f"document-{index}.docx",
        mime_type=DOCX_MIME,
        size_bytes=100,
        document_type=DocumentType.other,
        summary=f"Summary {index}",
        extracted_fields={"title": f"Document {index}", "key_terms": []},
        extracted_text=f"Document {index}",
        analyzer_mode=AnalyzerMode.demo,
        status=DocumentStatus.completed,
        created_at=created_at,
    )


def test_recent_documents_newest_first_and_maximum_20(client) -> None:
    now = datetime.now(UTC)
    with SessionLocal.begin() as session:
        session.add_all([make_document(i, now + timedelta(seconds=i)) for i in range(25)])
    response = client.get("/api/documents")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 20
    assert payload[0]["original_filename"] == "document-24.docx"
    assert payload[-1]["original_filename"] == "document-5.docx"
    assert "text_preview" not in payload[0]


def test_document_detail_success(client) -> None:
    created = upload_docx(client, "Project Brief\nLaunch plan").json()
    response = client.get(f"/api/documents/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_document_detail_not_found(client) -> None:
    response = client.get(f"/api/documents/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found."}


def test_openai_mode_missing_configuration_returns_503(client) -> None:
    app.dependency_overrides[get_settings] = lambda: Settings(
        analyzer_mode="openai", openai_api_key=None, openai_model=None
    )
    try:
        response = upload_docx(client, "Project notes")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Analyzer is not configured."}


def test_analyzer_failure_returns_502_and_does_not_persist(client, monkeypatch) -> None:
    class FailingAnalyzer:
        def analyze(self, text: str, filename: str):
            raise AnalyzerError("provider failed")

    monkeypatch.setattr("app.main._analyzer", lambda settings: FailingAnalyzer())
    response = upload_docx(client, "Project notes")
    assert response.status_code == 502
    assert response.json() == {"detail": "Document analysis failed."}
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(Document)) == 0


def test_upload_without_file_is_client_error(client) -> None:
    response = client.post("/api/documents")
    assert response.status_code == 422
