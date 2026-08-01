import sqlite3

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
    list_export_files,
    resolve_export_paths,
)
from app.services.export_audit import ExportAuditTrackingUnavailableError
from app.services.export_creation import (
    AuditedExportResult,
    create_audited_json_export,
    pending_export_audit_count,
)

router = APIRouter(prefix="/exports", tags=["exports"])

STATUS_UNAVAILABLE_MESSAGE = "Не удалось прочитать сведения об экспортах. Данные мастерской не изменялись."


def _file_response(metadata: ExportFile) -> ExportFileResponse:
    return ExportFileResponse(
        filename=metadata.filename,
        path=str(metadata.path),
        created_at=metadata.created_at,
        reason=metadata.reason,
        size_bytes=metadata.size_bytes,
    )


def _created_export_response(created: AuditedExportResult) -> ExportFileResponse:
    """Describe the new export from the creator's exact result and nothing else.

    ADR 0014: a successfully returned `ExportResult` is the authoritative result
    of the create operation, so the endpoint must not re-scan the export
    directory to decide what it just did. The scan can miss a file that exists,
    fail outright for an unrelated reason, or describe a foreign object that
    replaced the path — and it carries no information this result does not.

    The `reason` is parsed from the exact final filename through the same
    contract list and status use, never taken from `ExportResult.reason`, which
    is the human manifest reason.
    """
    result = created.result
    return ExportFileResponse(
        filename=result.export_path.name,
        path=str(result.export_path),
        created_at=result.created_at,
        reason=created.canonical_reason,
        size_bytes=result.size_bytes,
    )


@router.get("/status", response_model=ExportStatusResponse)
def get_export_status() -> ExportStatusResponse:
    paths = resolve_export_paths()
    database_exists = paths.database_path.exists() and paths.database_path.is_file()
    try:
        # No database means no ledger, and therefore no unresolved export
        # operation. That `0` is a conclusive read rather than a fabricated one,
        # and short-circuiting is what keeps this GET genuinely read-only:
        # opening a connection would create the database file as a side effect
        # of merely looking at the page.
        pending_audit_count = pending_export_audit_count(paths.export_dir) if database_exists else 0
    except (sqlite3.Error, OSError) as exc:
        # A status that cannot report its pending-Journal count truthfully is an
        # error, not a zero: the frontend clears a standing warning on a valid
        # `0`. The detail is fixed Russian text — no SQLite message, SQL
        # fragment or path is carried in it.
        #
        # The caught tuple is deliberately narrow. Catching `Exception` here
        # would dress a programming defect up as the known "ledger temporarily
        # unavailable" condition and hide a real bug behind a reassuring
        # sentence.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=STATUS_UNAVAILABLE_MESSAGE
        ) from exc
    exports = list_export_files(paths.export_dir)
    return ExportStatusResponse(
        database_path=str(paths.database_path),
        database_exists=database_exists,
        database_size_bytes=paths.database_path.stat().st_size if database_exists else None,
        export_dir=str(paths.export_dir),
        export_dir_exists=paths.export_dir.exists() and paths.export_dir.is_dir(),
        export_count=len(exports),
        latest_export=_file_response(exports[0]) if exports else None,
        pending_audit_count=pending_audit_count,
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
    try:
        created = create_audited_json_export(paths, request.reason if request is not None else None)
    except ExportSourceMissingError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="База данных не найдена. Сначала запустите приложение и создайте рабочую базу.",
        ) from exc
    except ExportAuditTrackingUnavailableError as exc:
        # CR-009: audit tracking could not be durably prepared, so no export was
        # written. The structured detail is deliberately fixed text — no SQLite
        # message, stack trace or SQL fragment reaches the user.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ExportAuditTrackingUnavailableError.code,
                "message": ExportAuditTrackingUnavailableError.message,
                "next_action": ExportAuditTrackingUnavailableError.next_action,
            },
        ) from exc
    except ExportError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ExportCreateResponse(
        export=_created_export_response(created),
        database_path=str(paths.database_path),
        export_dir=str(paths.export_dir),
        entity_counts=created.result.entity_counts,
        message="Экспорт создан.",
        audit_status=created.audit_status,
        audit_message=created.audit_message,
    )
