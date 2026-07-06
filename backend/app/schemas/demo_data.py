from pydantic import BaseModel


class DemoDataStatusResponse(BaseModel):
    is_installed: bool
    active_session_id: int | None
    demo_version: str
    can_install: bool
    can_clear: bool
    has_business_data: bool
    has_non_demo_business_data: bool
    created_counts: dict[str, int]
    blocking_reasons: list[str]
    message: str


class DemoDataInstallRequest(BaseModel):
    confirm_install: bool = False
    understand_demo_data: bool = False


class DemoDataInstallResponse(BaseModel):
    session_id: int
    demo_version: str
    created_counts: dict[str, int]
    message: str


class DemoDataClearRequest(BaseModel):
    confirm_clear: bool = False


class DemoDataClearResponse(BaseModel):
    session_id: int
    deleted_counts: dict[str, int]
    message: str
