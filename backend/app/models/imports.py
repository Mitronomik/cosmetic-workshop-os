from dataclasses import dataclass


@dataclass(frozen=True)
class ImportSource:
    id: int
    original_filename: str
    content_type: str
    file_extension: str
    file_size_bytes: int
    content_hash: str
    target_type: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ImportDraft:
    id: int
    source_id: int
    target_type: str
    status: str
    row_count: int
    valid_row_count: int
    invalid_row_count: int
    warning_count: int
    error_count: int
    headers_json: str
    summary_json: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ImportDraftRow:
    id: int
    draft_id: int
    row_number: int
    raw_values_json: str
    normalized_values_json: str
    issues_json: str
    status: str
    created_at: str
