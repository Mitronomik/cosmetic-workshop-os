from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.domain.purchase_suggestions import PURCHASE_SUGGESTION_ITEM_TYPES, PURCHASE_SUGGESTION_REASONS
from app.repositories.purchase_suggestions import PurchaseSuggestionNotFoundError, PurchaseSuggestionRepository
from app.schemas.purchase_suggestions import (
    ManualPurchaseSuggestionRequest,
    PurchaseSuggestionGenerationResponse,
    PurchaseSuggestionListResponse,
    PurchaseSuggestionResponse,
    PurchaseSuggestionUpdateRequest,
)
from app.services.purchase_suggestions import PurchaseSuggestionCommandService, PurchaseSuggestionGenerationService, PurchaseSuggestionValidationError

router = APIRouter(tags=["purchase-suggestions"])
StatusQuery = Literal["open", "purchased", "dismissed", "archived", "all"]


@router.get("/purchase-suggestions", response_model=PurchaseSuggestionListResponse)
def list_purchase_suggestions(status: StatusQuery = "open", reason: str | None = None, item_type: str | None = None, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0)):
    if reason is not None and reason not in PURCHASE_SUGGESTION_REASONS:
        raise HTTPException(422, detail="Unknown purchase suggestion reason.")
    if item_type is not None and item_type not in PURCHASE_SUGGESTION_ITEM_TYPES:
        raise HTTPException(422, detail="Unknown purchase suggestion item type.")
    rows = PurchaseSuggestionRepository().list_suggestions(status=status, reason=reason, item_type=item_type, limit=limit, offset=offset)
    return PurchaseSuggestionListResponse(purchase_suggestions=[_response(s) for s in rows], limit=limit, offset=offset)


@router.post("/purchase-suggestions/regenerate", response_model=PurchaseSuggestionGenerationResponse)
def regenerate_purchase_suggestions():
    return PurchaseSuggestionGenerationResponse(**PurchaseSuggestionGenerationService().regenerate_suggestions().__dict__)


@router.post("/purchase-suggestions", response_model=PurchaseSuggestionResponse)
def create_manual_purchase_suggestion(request: ManualPurchaseSuggestionRequest):
    try:
        return _response(PurchaseSuggestionCommandService().create_manual(**request.model_dump()))
    except PurchaseSuggestionValidationError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@router.patch("/purchase-suggestions/{suggestion_id}", response_model=PurchaseSuggestionResponse)
def update_purchase_suggestion(suggestion_id: int, request: PurchaseSuggestionUpdateRequest):
    try:
        return _response(PurchaseSuggestionCommandService().update_open(suggestion_id, **request.model_dump()))
    except PurchaseSuggestionNotFoundError as exc:
        raise HTTPException(404, detail="Purchase suggestion was not found.") from exc
    except PurchaseSuggestionValidationError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@router.post("/purchase-suggestions/{suggestion_id}/mark-purchased", response_model=PurchaseSuggestionResponse)
def mark_purchase_suggestion_purchased(suggestion_id: int):
    try:
        return _response(PurchaseSuggestionRepository().mark_purchased(suggestion_id))
    except PurchaseSuggestionNotFoundError as exc:
        raise HTTPException(404, detail="Purchase suggestion was not found.") from exc


@router.post("/purchase-suggestions/{suggestion_id}/dismiss", response_model=PurchaseSuggestionResponse)
def dismiss_purchase_suggestion(suggestion_id: int):
    try:
        return _response(PurchaseSuggestionRepository().dismiss_suggestion(suggestion_id))
    except PurchaseSuggestionNotFoundError as exc:
        raise HTTPException(404, detail="Purchase suggestion was not found.") from exc


def _response(s) -> PurchaseSuggestionResponse:
    return PurchaseSuggestionResponse(**s.__dict__)
