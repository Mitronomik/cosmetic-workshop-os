from dataclasses import dataclass


@dataclass(frozen=True)
class DemoDataSession:
    id: int
    demo_version: str
    status: str
    created_at: str
    cleared_at: str | None
    summary_json: str


@dataclass(frozen=True)
class DemoDataRecord:
    id: int
    session_id: int
    table_name: str
    record_id: int
    label: str
    created_at: str
