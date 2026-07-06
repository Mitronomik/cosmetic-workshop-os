from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ReportDocumentMetadata(BaseModel):
    id: str
    document_type: str
    format: str
    filename: str
    metadata_filename: str | None = None
    created_at: datetime
    source: str
    source_generated_at: datetime | None = None
    title: str
    warnings_count: int
    size_bytes: int


class ReportDocumentStatusResponse(BaseModel):
    documents_dir: str
    available_formats: list[str]
    available_document_types: list[str]
    can_create: bool
    documents_count: int
    message: str


class ReportDocumentListResponse(BaseModel):
    items: list[ReportDocumentMetadata]
    limit: int
    offset: int
    total: int


class ReportOverviewDocumentCreateRequest(BaseModel):
    format: str = "markdown"
    reason: str | None = Field(default=None, max_length=80)

    @field_validator("format", mode="before")
    @classmethod
    def normalize_format(cls, value: object) -> str:
        text = str(value or "markdown").strip().lower()
        return text or "markdown"

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class ReportDocumentCreateResponse(BaseModel):
    document: ReportDocumentMetadata
    message: str
