from fastapi import APIRouter, Body, HTTPException, status

from app.schemas.exports import (
    ExportCreateRequest,
    ExportCreateResponse,
    ExportFileResponse,
    ExportListResponse,
    ExportStatusResponse,
)
from app.services.export import (
    ExportError,
    ExportFile,
    ExportSourceMissingError,
    create_json_export,
    list_export_files,
    normalize_export_reason,
    resolve_export_paths,
)

router = APIRouter(prefix="/exports", tags=["exports"])


def _file_response(metadata: ExportFile) -> ExportFileResponse:
    return ExportFileResponse(
        filename=metadata.filename,
        path=str(metadata.path),
        created_at=metadata.created_at,
        reason=metadata.reason,
        size_bytes=metadata.size_bytes,
    )


@router.get("/status", response_model=ExportStatusResponse)
def get_export_status() -> ExportStatusResponse:
    paths = resolve_export_paths()
    exports = list_export_files(paths.export_dir)
    database_exists = paths.database_path.exists() and paths.database_path.is_file()
    return ExportStatusResponse(
        database_path=str(paths.database_path),
        database_exists=database_exists,
        database_size_bytes=paths.database_path.stat().st_size if database_exists else None,
        export_dir=str(paths.export_dir),
        export_dir_exists=paths.export_dir.exists() and paths.export_dir.is_dir(),
        export_count=len(exports),
        latest_export=_file_response(exports[0]) if exports else None,
    )


@router.get("", response_model=ExportListResponse)
def list_exports() -> ExportListResponse:
    paths = resolve_export_paths()
    return ExportListResponse(
        exports=[_file_response(export) for export in list_export_files(paths.export_dir)],
        export_dir=str(paths.export_dir),
    )


@router.post("", response_model=ExportCreateResponse, status_code=status.HTTP_201_CREATED)
def create_export(request: ExportCreateRequest | None = Body(default=None)) -> ExportCreateResponse:
    paths = resolve_export_paths()
    reason = normalize_export_reason(request.reason if request is not None else None)
    try:
        result = create_json_export(paths.database_path, paths.export_dir, reason=reason)
    except ExportSourceMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="База данных не найдена. Сначала запустите приложение и создайте рабочую базу.",
        ) from exc
    except ExportError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    metadata = next(
        (export for export in list_export_files(paths.export_dir) if export.path == result.export_path),
        ExportFile(
            filename=result.export_path.name,
            path=result.export_path,
            created_at=result.created_at,
            reason=result.reason,
            size_bytes=result.size_bytes,
        ),
    )
    return ExportCreateResponse(
        export=_file_response(metadata),
        database_path=str(paths.database_path),
        export_dir=str(paths.export_dir),
        entity_counts=result.entity_counts,
        message="Экспорт создан.",
    )
