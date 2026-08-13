from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import UserDataPaths, create_user_data_directories, resolve_user_data_paths
from app.db.startup_compatibility import (
    StartupSchemaCompatibility,
    inspect_startup_schema_compatibility,
)
from app.services.backup import BackupResult, backup_sqlite_database
from app.services.backup_audit import BackupReconciliationResult, reconcile_manual_backups
from app.services.database import initialize_database
from app.services.export_audit import ExportReconciliationResult, reconcile_json_exports
from app.services.report_document_audit import ReportDocumentReconciliationResult, reconcile_report_documents
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
    # CR-009 B1. Internal reconciliation counters, exposed to startup code for
    # logging and tests only; never rendered in ordinary launcher output.
    report_document_audit_reconciliation: ReportDocumentReconciliationResult | None = None
    # CR-009 B2. The same, for JSON exports.
    json_export_audit_reconciliation: ExportReconciliationResult | None = None
    # CR-009 B3. The same, for user-created manual SQLite backups. The automatic
    # `before_migration` backup below is deliberately not covered by it.
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

    # D4-A: application identity and schema compatibility are resolved before any
    # mutation-capable startup helper. A malformed packaged version projection or
    # unsupported existing lineage therefore cannot create directories, create a
    # backup, create/repair schema_migrations, run migrations or start the backend.
    app_version = resolve_effective_app_version()
    schema_compatibility = inspect_startup_schema_compatibility(config)

    backup = None
    if user_data_paths is not None:
        create_user_data_directories(user_data_paths)
        if schema_compatibility.migrations_pending:
            backup = backup_sqlite_database(
                source_path=config.path,
                backup_dir=user_data_paths.backups_dir,
                reason="before_migration",
            )

    # D4-A intentionally leaves execution semantics unchanged after the gate.
    # Supported older databases still take the existing direct migration path;
    # D4-B alone is authorized to replace it with staged migration + commit.
    applied_migrations = initialize_database(config)
    # CR-009 B1: bounded report-document reconciliation, strictly after
    # successful initialization and migrations — the ledger table may not exist
    # until `0020` has run — and strictly before the API is served. It is not a
    # background task: it completes here, once, and then startup continues.
    #
    # It never raises, so a pending Journal event cannot make the application
    # unusable. That deliberately does not extend to migration or database
    # failures above: those still propagate untouched.
    reconciliation = reconcile_report_documents(config)
    # CR-009 B2: JSON exports reconcile next, in this fixed order, on the same
    # config. Neither pass raises, so one artifact kind failing cannot prevent
    # the other from being reconciled or the application from starting.
    export_reconciliation = reconcile_json_exports(config)
    # CR-009 B3: manual backups reconcile last, in this fixed order, on the same
    # config. It also never raises. The automatic `before_migration` backup taken
    # above stays outside this pass entirely: it runs before migrations, is not a
    # user action, has no ledger row, and is never audited.
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
