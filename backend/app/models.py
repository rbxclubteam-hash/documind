import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DocumentType(StrEnum):
    invoice = "invoice"
    contract = "contract"
    resume = "resume"
    other = "other"


class AnalyzerMode(StrEnum):
    demo = "demo"
    openai = "openai"


class DocumentStatus(StrEnum):
    completed = "completed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    analyzer_mode: Mapped[AnalyzerMode] = mapped_column(
        Enum(AnalyzerMode, name="analyzer_mode"), nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.completed,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
