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
    BackupBusyError,
    BackupError,
    BackupFileMetadata,
    BackupSourceMissingError,
    list_backup_files,
    resolve_backup_paths,
)
from app.services.backup_audit import (
    BackupArtifactUnverifiedError,
    BackupAuditTrackingUnavailableError,
)
from app.services.backup_creation import (
    AuditedBackupResult,
    create_audited_backup,
    pending_backup_audit_count,
)

router = APIRouter(prefix="/backups", tags=["backups"])

STATUS_UNAVAILABLE_MESSAGE = (
    "Не удалось прочитать сведения о резервных копиях. Данные мастерской не изменялись."
)

DATABASE_MISSING_MESSAGE = (
    "База данных не найдена. Сначала запустите приложение и создайте рабочую базу."
)

# Fixed user-facing text for the two ways the snapshot itself can fail. A
# `BackupError` may carry an absolute database path and a SQLite message, so its
# text is never propagated to the API — it stays available through exception
# chaining, logs and tests.
BACKUP_BUSY_MESSAGE = (
    "База данных сейчас занята другой операцией, поэтому резервная копия не создана. "
    "Рабочие данные мастерской не изменялись."
)
BACKUP_BUSY_NEXT_ACTION = "Подождите несколько секунд и повторите создание резервной копии."
BACKUP_FAILED_MESSAGE = (
    "Не удалось создать резервную копию. Рабочие данные мастерской не изменялись."
)
BACKUP_FAILED_NEXT_ACTION = (
    "Повторите создание резервной копии. Если ошибка повторяется, перезапустите приложение."
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
            status_code=status.HTTP_404_NOT_FOUND, detail=DATABASE_MISSING_MESSAGE
        ) from exc
    except BackupAuditTrackingUnavailableError as exc:
        # CR-009: audit tracking could not be durably prepared, so no backup was
        # written at all.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": BackupAuditTrackingUnavailableError.code,
                "message": BackupAuditTrackingUnavailableError.message,
                "next_action": BackupAuditTrackingUnavailableError.next_action,
            },
        ) from exc
    except BackupArtifactUnverifiedError as exc:
        # Something exists at the reserved path but did not pass mandatory
        # verification, so it is not a trustworthy backup. This is deliberately
        # *not* a `201` with a pending Journal entry: that would report an
        # unverified artifact as a created backup.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": BackupArtifactUnverifiedError.code,
                "message": BackupArtifactUnverifiedError.message,
                "next_action": BackupArtifactUnverifiedError.next_action,
            },
        ) from exc
    except BackupBusyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "backup_source_busy",
                "message": BACKUP_BUSY_MESSAGE,
                "next_action": BACKUP_BUSY_NEXT_ACTION,
            },
        ) from exc
    except BackupError as exc:
        # `str(exc)` is never returned: a `BackupError` may embed an absolute
        # database path, a filename or a SQLite message. The chained exception
        # keeps all of that for logs and tests.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "backup_failed",
                "message": BACKUP_FAILED_MESSAGE,
                "next_action": BACKUP_FAILED_NEXT_ACTION,
            },
        ) from exc

    return BackupCreateResponse(
        backup=_created_backup_response(created),
        database_path=str(created.result.source_path),
        backup_dir=str(paths.backup_dir),
        message="Резервная копия создана.",
        audit_status=created.audit_status,
        audit_message=created.audit_message,
    )
