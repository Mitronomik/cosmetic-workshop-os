from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import UserDataPaths, create_user_data_directories, resolve_user_data_paths
from app.db.startup_compatibility import (
    StartupSchemaCompatibility,
    inspect_startup_schema_compatibility,
)
from app.services.backup import BackupResult
from app.services.backup_audit import BackupReconciliationResult, reconcile_manual_backups
from app.services.database import initialize_database
from app.services.export_audit import ExportReconciliationResult, reconcile_json_exports
from app.services.report_document_audit import ReportDocumentReconciliationResult, reconcile_report_documents
from app.services.update_safety import execute_staged_update, reconcile_interrupted_update
from app.version import resolve_effective_app_version

StartupMode = Literal["development", "user"]
ALLOWED_STARTUP_MODES: tuple[StartupMode, ...] = ("development", "user")


@dataclass(frozen=True)
class StartupInitializationResult:
    mode: StartupMode
    database_path: Path
    user_data_paths: UserDataPaths | None
    app_version: str
    schema_compatibility: StartupSchemaCompatibility
    applied_migrations: list[str]
    backup: BackupResult | None = None
    report_document_audit_reconciliation: ReportDocumentReconciliationResult | None = None
    json_export_audit_reconciliation: ExportReconciliationResult | None = None
    manual_backup_audit_reconciliation: BackupReconciliationResult | None = None


def validate_startup_mode(mode: str) -> StartupMode:
    if mode not in ALLOWED_STARTUP_MODES:
        allowed = ", ".join(ALLOWED_STARTUP_MODES)
        raise ValueError(f"Unsupported startup mode {mode!r}. Allowed modes: {allowed}.")
    return cast(StartupMode, mode)


def startup_database_config(mode: str = "development") -> DatabaseConfig:
    validated_mode = validate_startup_mode(mode)
    if validated_mode == "user":
        return DatabaseConfig(path=resolve_user_data_paths().database_path)
    return get_database_config()


def initialize_startup(mode: str = "development") -> StartupInitializationResult:
    validated_mode = validate_startup_mode(mode)
    user_data_paths = resolve_user_data_paths() if validated_mode == "user" else None
    config = (
        DatabaseConfig(path=user_data_paths.database_path)
        if user_data_paths is not None
        else get_database_config()
    )

    # D4-A remains the pre-mutation authority. Unsupported existing lineage stops
    # before user directories, backup files, update metadata, stages or migrations.
    app_version = resolve_effective_app_version()
    schema_compatibility = inspect_startup_schema_compatibility(config)

    backup = None
    if user_data_paths is not None:
        create_user_data_directories(user_data_paths)
        # D4-B always reconciles one durable interrupted `started` record before a
        # new attempt. It never resumes or promotes an old stage blindly.
        reconcile_interrupted_update(user_data_paths, schema_compatibility)
        if schema_compatibility.migrations_pending:
            update = execute_staged_update(
                config=config,
                paths=user_data_paths,
                app_version=app_version,
                compatibility=schema_compatibility,
            )
            applied_migrations = update.applied_migrations
            backup = update.backup
        else:
            # Fresh creation and an already-current DB keep the existing path.
            applied_migrations = initialize_database(config)
    else:
        # D4 is packaged/user-mode update safety, not a second development mode.
        applied_migrations = initialize_database(config)

    # CR-009 reconciliation runs only after the canonical DB is current. For a
    # D4-B migration this is after verified atomic stage publication, never on stage.
    reconciliation = reconcile_report_documents(config)
    export_reconciliation = reconcile_json_exports(config)
    backup_reconciliation = reconcile_manual_backups(config)
    return StartupInitializationResult(
        mode=validated_mode,
        database_path=config.path,
        user_data_paths=user_data_paths,
        app_version=app_version,
        schema_compatibility=schema_compatibility,
        applied_migrations=applied_migrations,
        backup=backup,
        report_document_audit_reconciliation=reconciliation,
        json_export_audit_reconciliation=export_reconciliation,
        manual_backup_audit_reconciliation=backup_reconciliation,
    )
