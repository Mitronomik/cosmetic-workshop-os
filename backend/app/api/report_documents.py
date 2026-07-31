from fastapi import APIRouter, Body, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.schemas.report_documents import (
    ReportDocumentCreateResponse,
    ReportDocumentListResponse,
    ReportDocumentStatusResponse,
    ReportOverviewDocumentCreateRequest,
)
from app.services.report_document_audit import ReportDocumentAuditTrackingUnavailableError
from app.services.report_documents import (
    ReportDocumentError,
    ReportDocumentFileMissingError,
    ReportDocumentNotFoundError,
    ReportDocumentService,
    ReportDocumentUnsafePathError,
    UnsupportedReportDocumentDispositionError,
    UnsupportedReportDocumentFormatError,
)

router = APIRouter(prefix="/report-documents", tags=["report-documents"])


@router.get("/status", response_model=ReportDocumentStatusResponse)
def get_report_documents_status() -> ReportDocumentStatusResponse:
    return ReportDocumentService().status()


@router.get("", response_model=ReportDocumentListResponse)
def list_report_documents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ReportDocumentListResponse:
    return ReportDocumentService().list_documents(limit=limit, offset=offset)


@router.get("/{document_id}/download")
def download_report_document(
    document_id: str,
    disposition: str = Query(default="attachment"),
) -> FileResponse:
    try:
        metadata, path, media_type, effective_disposition = ReportDocumentService().get_document_file(
            document_id, disposition=disposition
        )
    except ReportDocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ReportDocumentFileMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ReportDocumentUnsafePathError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except UnsupportedReportDocumentDispositionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return FileResponse(
        path=path,
        media_type=media_type,
        filename=metadata.filename,
        content_disposition_type=effective_disposition,
    )


@router.post("/reports/overview", response_model=ReportDocumentCreateResponse, status_code=status.HTTP_201_CREATED)
def create_overview_report_document(
    request: ReportOverviewDocumentCreateRequest | None = Body(default=None),
) -> ReportDocumentCreateResponse:
    try:
        return ReportDocumentService().create_overview_document(request or ReportOverviewDocumentCreateRequest())
    except UnsupportedReportDocumentFormatError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ReportDocumentAuditTrackingUnavailableError as exc:
        # CR-009: audit tracking could not be durably prepared, so no document
        # was written. The structured detail is deliberately fixed text — no
        # SQLite message, stack trace or SQL fragment reaches the user.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": ReportDocumentAuditTrackingUnavailableError.code,
                "message": ReportDocumentAuditTrackingUnavailableError.message,
                "next_action": ReportDocumentAuditTrackingUnavailableError.next_action,
            },
        ) from exc
    except ReportDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
