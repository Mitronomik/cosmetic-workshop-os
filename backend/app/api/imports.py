from email.parser import BytesParser
from email.policy import default

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.schemas.imports import (
    ImportDraftCancelResponse,
    ImportDraftCreateResponse,
    ImportDraftDetailResponse,
    ImportDraftListResponse,
    ImportTargetsResponse,
)
from app.services.imports import (
    ImportFileTooLargeError,
    ImportParseError,
    ImportServiceError,
    UnsupportedImportFileError,
    UploadedFileData,
    create_import_draft,
    cancel_import_draft,
    get_import_draft,
    list_import_drafts,
    target_definitions,
)

router = APIRouter(prefix="/imports", tags=["imports"])


def _parse_multipart(content_type: str, body: bytes) -> tuple[UploadedFileData, str]:
    if "multipart/form-data" not in content_type or "boundary=" not in content_type:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Нужно отправить multipart/form-data с файлом и типом импорта.")
    message = BytesParser(policy=default).parsebytes((f"Content-Type: {content_type}\r\n\r\n").encode() + body)
    file_data: UploadedFileData | None = None
    target_type: str | None = None
    for part in message.iter_parts():
        disposition = part.get("Content-Disposition", "")
        params = dict(part.get_params(header="content-disposition"))
        name = params.get("name")
        if name == "target_type":
            payload = part.get_payload(decode=True) or b""
            target_type = payload.decode(part.get_content_charset() or "utf-8", errors="replace").strip()
        elif name == "file":
            filename = params.get("filename") or "import"
            payload = part.get_payload(decode=True) or b""
            file_data = UploadedFileData(filename=filename, content_type=part.get_content_type() or "", content=payload)
    if file_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Файл импорта не найден.")
    if not target_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не выбран тип импорта.")
    return file_data, target_type


@router.get("/targets", response_model=ImportTargetsResponse)
def get_import_targets() -> ImportTargetsResponse:
    return ImportTargetsResponse(targets=target_definitions())


@router.post("/drafts", response_model=ImportDraftCreateResponse, status_code=status.HTTP_201_CREATED)
async def post_import_draft(request: Request) -> ImportDraftCreateResponse:
    upload, target_type = _parse_multipart(request.headers.get("content-type", ""), await request.body())
    try:
        return ImportDraftCreateResponse(**create_import_draft(upload, target_type))
    except UnsupportedImportFileError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc) or UnsupportedImportFileError.message) from exc
    except ImportFileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc) or ImportFileTooLargeError.message) from exc
    except ImportParseError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc) or ImportParseError.message) from exc
    except ImportServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/drafts", response_model=ImportDraftListResponse)
def get_import_drafts(
    status_filter: str | None = Query(default=None, alias="status"),
    target_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ImportDraftListResponse:
    return ImportDraftListResponse(**list_import_drafts(status=status_filter, target_type=target_type, limit=limit, offset=offset))


@router.get("/drafts/{draft_id}", response_model=ImportDraftDetailResponse)
def get_import_draft_details(draft_id: int, limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> ImportDraftDetailResponse:
    result = get_import_draft(draft_id, limit=limit, offset=offset)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Черновик импорта не найден.")
    return ImportDraftDetailResponse(**result)


@router.post("/drafts/{draft_id}/cancel", response_model=ImportDraftCancelResponse)
def post_import_draft_cancel(draft_id: int) -> ImportDraftCancelResponse:
    result = cancel_import_draft(draft_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Черновик импорта не найден.")
    return ImportDraftCancelResponse(**result)
