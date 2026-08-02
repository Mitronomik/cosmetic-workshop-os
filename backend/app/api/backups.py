import sqlite3

from fastapi import APIRouter, Body, HTTPException, status

from app.schemas.backups import (
    BackupCreateRequest,
    BackupCreateResponse,
    BackupFileResponse,
    BackupListResponse,
    BackupStatusResponse,
)
from app.services.backup import (
    BackupError,
    BackupFileMetadata,
    BackupSourceMissingError,
    list_backup_files,
    resolve_backup_paths,
)
from app.services.backup_audit import BackupAuditTrackingUnavailableError
from app.services.backup_creation import (
    AuditedBackupResult,
    create_audited_backup,
    pending_backup_audit_count,
)

router = APIRouter(prefix="/backups", tags=["backups"])

STATUS_UNAVAILABLE_MESSAGE = (
    "Не удалось прочитать сведения о резервных копиях. Данные мастерской не изменялись."
)


def _file_response(metadata: BackupFileMetadata) -> BackupFileResponse:
    return BackupFileResponse(
        filename=metadata.filename,
        path=str(metadata.path),
        created_at=metadata.created_at,
        reason=metadata.reason,
        size_bytes=metadata.size_bytes,
    )


def _created_backup_response(created: AuditedBackupResult) -> BackupFileResponse:
    """Describe the new backup from the engine's exact result and nothing else.

    CR-004 measured the previous directory re-scan turning a complete, verified
    backup into an HTTP 500, and found it could also raise `StopIteration` or
    describe a different file. The scan carries no information this result does
    not, so the create path no longer performs it.

    The `reason` is parsed from the exact final filename through the strict
    generated-name grammar, never taken from `BackupResult.reason`, which is the
    human request reason.
    """
    result = created.result
    return BackupFileResponse(
        filename=result.backup_path.name,
        path=str(result.backup_path),
        created_at=result.created_at,
        reason=created.canonical_reason,
        size_bytes=result.size_bytes,
    )


@router.get("/status", response_model=BackupStatusResponse)
def get_backup_status() -> BackupStatusResponse:
    paths = resolve_backup_paths()
    database_exists = paths.database_path.exists() and paths.database_path.is_file()
    try:
        # No database means no ledger, and therefore no unresolved backup
        # operation. That `0` is a conclusive read rather than a fabricated one,
        # and short-circuiting is what keeps this GET genuinely read-only:
        # opening a connection would create the database file as a side effect
        # of merely looking at the page.
        pending_audit_count = (
            pending_backup_audit_count(paths.backup_dir) if database_exists else 0
        )
    except (sqlite3.Error, OSError) as exc:
        # A status that cannot report its pending-Journal count truthfully is an
        # error, not a zero: the frontend clears a standing warning on a valid
        # `0`. The detail is fixed Russian text — no SQLite message, SQL fragment
        # or path is carried in it.
        #
        # The caught tuple is deliberately narrow. Catching `Exception` here
        # would dress a programming defect up as the known "ledger temporarily
        # unavailable" condition and hide a real bug behind a reassuring
        # sentence.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=STATUS_UNAVAILABLE_MESSAGE
        ) from exc
    backups = list_backup_files(paths.backup_dir)
    return BackupStatusResponse(
        database_path=str(paths.database_path),
        database_exists=database_exists,
        database_size_bytes=paths.database_path.stat().st_size if database_exists else None,
        backup_dir=str(paths.backup_dir),
        backup_dir_exists=paths.backup_dir.exists() and paths.backup_dir.is_dir(),
        backup_count=len(backups),
        latest_backup=_file_response(backups[0]) if backups else None,
        pending_audit_count=pending_audit_count,
    )


@router.get("", response_model=BackupListResponse)
def list_backups() -> BackupListResponse:
    paths = resolve_backup_paths()
    return BackupListResponse(
        backups=[_file_response(backup) for backup in list_backup_files(paths.backup_dir)],
        backup_dir=str(paths.backup_dir),
    )


@router.post("", response_model=BackupCreateResponse, status_code=status.HTTP_201_CREATED)
def create_backup(
    request: BackupCreateRequest | None = Body(default=None),
) -> BackupCreateResponse:
    paths = resolve_backup_paths()
    try:
        created = create_audited_backup(paths, request.reason if request is not None else None)
    except BackupSourceMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="База данных не найдена. Сначала запустите приложение и создайте рабочую базу.",
        ) from exc
    except BackupAuditTrackingUnavailableError as exc:
        # CR-009: audit tracking could not be durably prepared, so no backup was
        # written. The structured detail is deliberately fixed text — no SQLite
        # message, stack trace or SQL fragment reaches the user.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": BackupAuditTrackingUnavailableError.code,
                "message": BackupAuditTrackingUnavailableError.message,
                "next_action": BackupAuditTrackingUnavailableError.next_action,
            },
        ) from exc
    except BackupError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return BackupCreateResponse(
        backup=_created_backup_response(created),
        database_path=str(created.result.source_path),
        backup_dir=str(paths.backup_dir),
        message="Резервная копия создана.",
        audit_status=created.audit_status,
        audit_message=created.audit_message,
    )
