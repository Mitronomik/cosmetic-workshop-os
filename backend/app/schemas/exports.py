from datetime import datetime

from pydantic import BaseModel, Field, field_validator


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
    export: ExportFileResponse
    database_path: str
    export_dir: str
    entity_counts: dict[str, int]
    message: str
