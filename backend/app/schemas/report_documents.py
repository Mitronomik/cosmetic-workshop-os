from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


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
    # CR-009 B1. Documents whose Journal entry is not committed yet. Read-only:
    # this endpoint reports the count and never reconciles it.
    pending_audit_count: int = 0


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
    """A created document plus the separate result of recording it in the Journal.

    CR-009 keeps the two results apart on purpose. `message` stays the artifact
    result and never changes meaning; `audit_status` reports only whether the
    secondary Journal write succeeded. A `pending` audit is still HTTP 201 —
    the document exists, is listed and is downloadable.
    """

    document: ReportDocumentMetadata
    message: str
    audit_status: Literal["recorded", "pending"] = "recorded"
    audit_message: str | None = None

    @model_validator(mode="after")
    def check_audit_contract(self) -> "ReportDocumentCreateResponse":
        """Bind the two audit fields so an inconsistent pair cannot be returned.

        The frontend is required to reject a response whose audit contract is
        incomplete, so the backend must not be the thing that produces one: a
        `recorded` result carries no warning, and a `pending` result always
        carries the exact accepted warning.
        """
        from app.services.report_document_audit import PENDING_AUDIT_MESSAGE

        if self.audit_status == "recorded" and self.audit_message is not None:
            raise ValueError("A recorded audit result must not carry a warning message.")
        if self.audit_status == "pending" and self.audit_message != PENDING_AUDIT_MESSAGE:
            raise ValueError("A pending audit result must carry the exact accepted warning message.")
        return self
