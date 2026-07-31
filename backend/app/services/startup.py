from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import UserDataPaths, create_user_data_directories, resolve_user_data_paths
from app.db.migrations import pending_migration_ids
from app.services.backup import BackupResult, backup_sqlite_database
from app.services.database import initialize_database
from app.services.report_document_audit import ReportDocumentReconciliationResult, reconcile_report_documents

StartupMode = Literal["development", "user"]
ALLOWED_STARTUP_MODES: tuple[StartupMode, ...] = ("development", "user")


@dataclass(frozen=True)
class StartupInitializationResult:
    mode: StartupMode
    database_path: Path
    user_data_paths: UserDataPaths | None
    applied_migrations: list[str]
    backup: BackupResult | None = None
    # CR-009 B1. Internal reconciliation counters, exposed to startup code for
    # logging and tests only; never rendered in ordinary launcher output.
    report_document_audit_reconciliation: ReportDocumentReconciliationResult | None = None


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
    backup = None
    if user_data_paths is not None:
        database_existed_before_startup = user_data_paths.database_path.exists()
        migrations_pending = (
            bool(pending_migration_ids(DatabaseConfig(path=user_data_paths.database_path)))
            if database_existed_before_startup
            else False
        )
        create_user_data_directories(user_data_paths)
        config = DatabaseConfig(path=user_data_paths.database_path)
        if database_existed_before_startup and migrations_pending:
            backup = backup_sqlite_database(
                source_path=config.path,
                backup_dir=user_data_paths.backups_dir,
                reason="before_migration",
            )
    else:
        config = get_database_config()
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
    return StartupInitializationResult(
        mode=validated_mode,
        database_path=config.path,
        user_data_paths=user_data_paths,
        applied_migrations=applied_migrations,
        backup=backup,
        report_document_audit_reconciliation=reconciliation,
    )
