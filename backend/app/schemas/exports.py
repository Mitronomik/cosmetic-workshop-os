from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ExportFileResponse(BaseModel):
    filename: str
    path: str
    created_at: datetime | None
    reason: str | None
    size_bytes: int


class ExportStatusResponse(BaseModel):
    database_path: str
    database_exists: bool
    database_size_bytes: int | None
    export_dir: str
    export_dir_exists: bool
    export_count: int
    latest_export: ExportFileResponse | None
    # CR-009 B2. Exports whose Journal entry is not committed yet. Read-only:
    # this endpoint reports the count and never reconciles it.
    pending_audit_count: int = 0


class ExportListResponse(BaseModel):
    exports: list[ExportFileResponse]
    export_dir: str


class ExportCreateRequest(BaseModel):
    reason: str | None = Field(default="manual", max_length=80)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str:
        if value is None:
            return "manual"
        text = str(value).strip()
        return text or "manual"


class ExportCreateResponse(BaseModel):
    """A created export plus the separate result of recording it in the Journal.

    CR-009 keeps the two results apart on purpose. `message` stays the artifact
    result and never changes meaning; `audit_status` reports only whether the
    secondary Journal write succeeded. A `pending` audit is still HTTP 201 — the
    export exists, is listed and is byte-identical to what was written.
    """

    export: ExportFileResponse
    database_path: str
    export_dir: str
    entity_counts: dict[str, int]
    message: str
    audit_status: Literal["recorded", "pending"] = "recorded"
    audit_message: str | None = None

    @model_validator(mode="after")
    def check_audit_contract(self) -> "ExportCreateResponse":
        """Bind the two audit fields so an inconsistent pair cannot be returned.

        The frontend is required to reject a response whose audit contract is
        incomplete, so the backend must not be the thing that produces one: a
        `recorded` result carries no warning, and a `pending` result always
        carries the exact accepted warning.
        """
        from app.services.export_audit import PENDING_AUDIT_MESSAGE

        if self.audit_status == "recorded" and self.audit_message is not None:
            raise ValueError("A recorded audit result must not carry a warning message.")
        if self.audit_status == "pending" and self.audit_message != PENDING_AUDIT_MESSAGE:
            raise ValueError("A pending audit result must carry the exact accepted warning message.")
        return self
