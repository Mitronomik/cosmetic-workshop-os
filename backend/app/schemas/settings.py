from pydantic import BaseModel


class AppSettingResponse(BaseModel):
    key: str
    value: str
    value_type: str
    description: str


class AppSettingsResponse(BaseModel):
    settings: list[AppSettingResponse]
