from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BackupFileResponse(BaseModel):
    filename: str
    path: str
    created_at: datetime | None
    reason: str | None
    size_bytes: int


class BackupStatusResponse(BaseModel):
    database_path: str
    database_exists: bool
    database_size_bytes: int | None
    backup_dir: str
    backup_dir_exists: bool
    backup_count: int
    latest_backup: BackupFileResponse | None


class BackupListResponse(BaseModel):
    backups: list[BackupFileResponse]
    backup_dir: str


class BackupCreateRequest(BaseModel):
    reason: str | None = Field(default="manual", max_length=80)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str:
        if value is None:
            return "manual"
        text = str(value).strip()
        return text or "manual"


class BackupCreateResponse(BaseModel):
    backup: BackupFileResponse
    database_path: str
    backup_dir: str
    message: str
