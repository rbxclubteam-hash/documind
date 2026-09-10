import uuid
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzers import AnalyzerError, AnalyzerNotConfigured, DemoAnalyzer, OpenAIAnalyzer
from app.config import Settings, get_settings
from app.db import get_db
from app.extractors import ExtractionError, extract_text
from app.models import AnalyzerMode, Document, DocumentStatus, DocumentType
from app.schemas import DocumentListItem, DocumentResult

MAX_FILE_SIZE = 10 * 1024 * 1024
TEXT_PREVIEW_SIZE = 4000
SUPPORTED_FILES = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
        "application/zip",
    },
}

app = FastAPI(
    title="DocuMind API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _analyzer(settings: Settings):
    if settings.analyzer_mode == "openai":
        return OpenAIAnalyzer(settings.openai_api_key, settings.openai_model)
    return DemoAnalyzer()


def _result(document: Document) -> DocumentResult:
    return DocumentResult(
        id=document.id,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        size_bytes=document.size_bytes,
        document_type=document.document_type,
        summary=document.summary,
        extracted_fields=document.extracted_fields,
        text_preview=document.extracted_text[:TEXT_PREVIEW_SIZE],
        analyzer_mode=document.analyzer_mode,
        status=document.status,
        created_at=document.created_at,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/documents", response_model=DocumentResult, status_code=status.HTTP_201_CREATED)
def create_document(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentResult:
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_FILES or file.content_type not in SUPPORTED_FILES[suffix]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Upload a text-based PDF or DOCX.",
        )

    content = file.file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File exceeds the 10 MB limit.",
        )

    try:
        text = extract_text(content, filename)
    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No extractable text found. Scanned PDFs are not supported.",
        ) from exc
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="No extractable text found. Scanned PDFs are not supported.",
        )

    try:
        analysis = _analyzer(current_settings).analyze(text, filename)
    except AnalyzerNotConfigured as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Analyzer is not configured.",
        ) from exc
    except AnalyzerError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Document analysis failed.",
        ) from exc

    document = Document(
        original_filename=filename,
        mime_type=file.content_type,
        size_bytes=len(content),
        document_type=DocumentType(analysis.document_type),
        summary=analysis.summary,
        extracted_fields=analysis.extracted_fields.model_dump(),
        extracted_text=text,
        analyzer_mode=AnalyzerMode(current_settings.analyzer_mode),
        status=DocumentStatus.completed,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _result(document)


@app.get("/api/documents", response_model=list[DocumentListItem])
def list_documents(db: Annotated[Session, Depends(get_db)]) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc()).limit(20)).all())


@app.get("/api/documents/{document_id}", response_model=DocumentResult)
def get_document(document_id: uuid.UUID, db: Annotated[Session, Depends(get_db)]) -> DocumentResult:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _result(document)
