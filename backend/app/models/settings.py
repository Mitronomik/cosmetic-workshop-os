from dataclasses import dataclass


@dataclass(frozen=True)
class AppSetting:
    key: str
    value: str
    value_type: str
    description: str
