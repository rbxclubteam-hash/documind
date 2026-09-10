import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from app.models import AnalyzerMode, DocumentStatus, DocumentType


class InvoiceFields(BaseModel):
    vendor: str | None
    invoice_number: str | None
    invoice_date: str | None
    total_amount: str | None
    currency: str | None

    model_config = ConfigDict(extra="forbid")


class ContractFields(BaseModel):
    parties: list[str]
    effective_date: str | None
    expiration_date: str | None
    contract_value: str | None
    subject: str | None

    model_config = ConfigDict(extra="forbid")


class ResumeFields(BaseModel):
    candidate_name: str | None
    email: str | None
    phone: str | None
    skills: list[str]
    current_or_recent_role: str | None

    model_config = ConfigDict(extra="forbid")


class OtherFields(BaseModel):
    title: str | None
    key_terms: list[str]

    model_config = ConfigDict(extra="forbid")


class InvoiceAnalysis(BaseModel):
    document_type: Literal["invoice"]
    summary: str = Field(min_length=1)
    extracted_fields: InvoiceFields


class ContractAnalysis(BaseModel):
    document_type: Literal["contract"]
    summary: str = Field(min_length=1)
    extracted_fields: ContractFields


class ResumeAnalysis(BaseModel):
    document_type: Literal["resume"]
    summary: str = Field(min_length=1)
    extracted_fields: ResumeFields


class OtherAnalysis(BaseModel):
    document_type: Literal["other"]
    summary: str = Field(min_length=1)
    extracted_fields: OtherFields


AnalysisResult = Annotated[
    InvoiceAnalysis | ContractAnalysis | ResumeAnalysis | OtherAnalysis,
    Field(discriminator="document_type"),
]
analysis_adapter = TypeAdapter(AnalysisResult)


class DocumentResult(BaseModel):
    id: uuid.UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    document_type: DocumentType
    summary: str
    extracted_fields: dict[str, object]
    text_preview: str
    analyzer_mode: AnalyzerMode
    status: DocumentStatus
    created_at: datetime


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    document_type: DocumentType
    summary: str
    analyzer_mode: AnalyzerMode
    status: DocumentStatus
    created_at: datetime
