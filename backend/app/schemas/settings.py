from datetime import datetime
from typing import Literal

from pydantic import BaseModel


SettingsCapabilityStatus = Literal["ready", "available", "planned", "disabled"]
SettingsDefinitionStatus = Literal[
    "editable_now",
    "read_only_now",
    "safe_mvp_candidate",
    "requires_backend_rules",
    "v2_or_later",
    "not_mvp",
]
SettingsWarningSeverity = Literal["info", "warning"]


class AppSettingResponse(BaseModel):
    key: str
    value: str
    value_type: str
    description: str


class AppSettingsResponse(BaseModel):
    settings: list[AppSettingResponse]


class AppSettingsInfo(BaseModel):
    product_name: str
    repository_name: str | None = None
    mode: str
    local_first: bool
    internet_required: bool
    version: str | None = None


class LocalDataStatus(BaseModel):
    user_data_separate_from_code: bool
    user_data_path_available: bool
    user_data_path_display: str | None
    backup_before_migration_required: bool
    message: str


class SettingsCapability(BaseModel):
    id: str
    title: str
    status: SettingsCapabilityStatus
    route: str | None
    description: str
    mutates_from_settings: bool


class SettingsDefinition(BaseModel):
    id: str
    title: str
    status: SettingsDefinitionStatus
    editable_in_pr95: bool
    affects_calculations: bool
    affects_historical_data: bool
    requires_backend_service: bool
    description: str
    safety_note: str


class SettingsGroup(BaseModel):
    id: str
    title: str
    description: str
    items: list[SettingsDefinition]


class SettingsWarning(BaseModel):
    code: str
    message: str
    severity: SettingsWarningSeverity = "info"


class SettingsStatusResponse(BaseModel):
    generated_at: datetime
    app: AppSettingsInfo
    local_data: LocalDataStatus
    capabilities: list[SettingsCapability]
    setting_groups: list[SettingsGroup]
    editable_settings_available: bool
    message: str
    warnings: list[SettingsWarning]


class WorkshopProfile(BaseModel):
    workshop_name: str = ""
    master_name: str = ""
    workshop_contact_text: str = ""
    workshop_note: str = ""


class WorkshopProfileUpdateRequest(BaseModel):
    workshop_name: str = ""
    master_name: str = ""
    workshop_contact_text: str = ""
    workshop_note: str = ""


class WorkshopProfileResponse(BaseModel):
    profile: WorkshopProfile
    is_configured: bool
    updated_at: datetime | None = None
    message: str
