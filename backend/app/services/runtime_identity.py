"""Read-only Settings projection of the effective runtime application identity."""

from app.schemas.settings import SettingsStatusResponse
from app.services.settings import get_settings_status
from app.version import resolve_effective_app_version


def get_runtime_settings_status() -> SettingsStatusResponse:
    status = get_settings_status()
    app = status.app.model_copy(update={"version": resolve_effective_app_version()})
    return status.model_copy(update={"app": app})
