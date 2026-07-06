from fastapi import APIRouter, Body, HTTPException, Query, status

from app.schemas.report_documents import (
    ReportDocumentCreateResponse,
    ReportDocumentListResponse,
    ReportDocumentStatusResponse,
    ReportOverviewDocumentCreateRequest,
)
from app.services.report_documents import ReportDocumentError, ReportDocumentService, UnsupportedReportDocumentFormatError

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


@router.post("/reports/overview", response_model=ReportDocumentCreateResponse, status_code=status.HTTP_201_CREATED)
def create_overview_report_document(
    request: ReportOverviewDocumentCreateRequest | None = Body(default=None),
) -> ReportDocumentCreateResponse:
    try:
        return ReportDocumentService().create_overview_document(request or ReportOverviewDocumentCreateRequest())
    except UnsupportedReportDocumentFormatError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ReportDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
