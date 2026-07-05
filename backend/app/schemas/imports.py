from pydantic import BaseModel


class ImportTargetResponse(BaseModel):
    type: str
    label: str
    required_columns: list[str]
    optional_columns: list[str]


class ImportTargetsResponse(BaseModel):
    targets: list[ImportTargetResponse]


class ImportIssueResponse(BaseModel):
    severity: str
    code: str
    message: str
    row_number: int | None = None
    field: str | None = None


class ImportApplyReadinessResponse(BaseModel):
    can_apply: bool
    status: str
    blocking_error_count: int
    warning_count: int
    valid_row_count: int
    invalid_row_count: int
    blocking_reasons: list[str]
    warnings: list[str]
    next_action: str


class ImportDraftSummaryResponse(BaseModel):
    id: int
    source_id: int
    target_type: str
    status: str
    row_count: int
    valid_row_count: int
    invalid_row_count: int
    warning_count: int
    error_count: int
    headers: list[str]
    summary: dict[str, object]
    apply_readiness: ImportApplyReadinessResponse
    created_at: str
    updated_at: str


class ImportDraftRowResponse(BaseModel):
    id: int
    row_number: int
    raw_values: dict[str, str]
    normalized_values: dict[str, str]
    issues: list[ImportIssueResponse]
    status: str
    created_at: str


class ImportSourceResponse(BaseModel):
    id: int
    original_filename: str
    content_type: str
    file_extension: str
    file_size_bytes: int
    target_type: str
    status: str
    created_at: str
    updated_at: str


class ImportDraftCreateResponse(BaseModel):
    draft: ImportDraftSummaryResponse
    preview_rows: list[ImportDraftRowResponse]
    issues: list[ImportIssueResponse]
    message: str


class ImportDraftListResponse(BaseModel):
    drafts: list[ImportDraftSummaryResponse]
    limit: int
    offset: int


class ImportDraftDetailResponse(BaseModel):
    draft: ImportDraftSummaryResponse
    source: ImportSourceResponse
    preview_rows: list[ImportDraftRowResponse]
    issues: list[ImportIssueResponse]
    limit: int
    offset: int


class ImportDraftCancelResponse(BaseModel):
    draft: ImportDraftSummaryResponse
    message: str
