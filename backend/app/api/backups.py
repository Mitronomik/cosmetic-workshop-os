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
    BackupSourceMissingError,
    backup_sqlite_database,
    list_backup_files,
    normalize_backup_reason,
    resolve_backup_paths,
)

router = APIRouter(prefix="/backups", tags=["backups"])


def _file_response(metadata) -> BackupFileResponse:
    return BackupFileResponse(
        filename=metadata.filename,
        path=str(metadata.path),
        created_at=metadata.created_at,
        reason=metadata.reason,
        size_bytes=metadata.size_bytes,
    )


@router.get("/status", response_model=BackupStatusResponse)
def get_backup_status() -> BackupStatusResponse:
    paths = resolve_backup_paths()
    backups = list_backup_files(paths.backup_dir)
    database_exists = paths.database_path.exists() and paths.database_path.is_file()
    return BackupStatusResponse(
        database_path=str(paths.database_path),
        database_exists=database_exists,
        database_size_bytes=paths.database_path.stat().st_size if database_exists else None,
        backup_dir=str(paths.backup_dir),
        backup_dir_exists=paths.backup_dir.exists() and paths.backup_dir.is_dir(),
        backup_count=len(backups),
        latest_backup=_file_response(backups[0]) if backups else None,
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
    reason = normalize_backup_reason(request.reason if request is not None else None)
    try:
        result = backup_sqlite_database(paths.database_path, paths.backup_dir, reason=reason)
    except BackupSourceMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="База данных не найдена. Сначала запустите приложение и создайте рабочую базу.",
        ) from exc
    except BackupError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    metadata = list_backup_files(paths.backup_dir)[0]
    if metadata.path != result.backup_path:
        metadata = next(
            backup for backup in list_backup_files(paths.backup_dir) if backup.path == result.backup_path
        )
    return BackupCreateResponse(
        backup=_file_response(metadata),
        database_path=str(result.source_path),
        backup_dir=str(paths.backup_dir),
        message="Резервная копия создана.",
    )
