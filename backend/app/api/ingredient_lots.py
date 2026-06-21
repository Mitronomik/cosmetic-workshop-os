from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.domain.ingredient_lots import IngredientLotDraft
from app.models.ingredient_lot import IngredientLot
from app.schemas.ingredient_lots import (
    IngredientLotCreateRequest,
    IngredientLotResponse,
    IngredientLotsResponse,
    IngredientLotUpdateRequest,
)
from app.services.ingredient_lots import (
    IngredientLotInactiveIngredientError,
    IngredientLotIngredientMissingError,
    IngredientLotNotFoundError,
    IngredientLotService,
)

router = APIRouter(tags=["ingredient-lots"])


@router.post("/ingredient-lots", response_model=IngredientLotResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient_lot(payload: IngredientLotCreateRequest) -> IngredientLotResponse:
    try:
        lot = IngredientLotService().create_lot(_draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except IngredientLotIngredientMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient was not found.") from exc
    except IngredientLotInactiveIngredientError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient is inactive.") from exc
    return _lot_response(lot)


@router.get("/ingredient-lots", response_model=IngredientLotsResponse)
def list_active_ingredient_lots() -> IngredientLotsResponse:
    lots = IngredientLotService().list_active_lots()
    return IngredientLotsResponse(lots=[_lot_response(lot) for lot in lots])


@router.get("/ingredient-lots/{lot_id}", response_model=IngredientLotResponse)
def get_ingredient_lot(lot_id: int) -> IngredientLotResponse:
    try:
        lot = IngredientLotService().get_lot(lot_id)
    except IngredientLotNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient lot was not found.") from exc
    return _lot_response(lot)


@router.get("/ingredients/{ingredient_id}/lots", response_model=IngredientLotsResponse)
def list_active_ingredient_lots_by_ingredient(ingredient_id: int) -> IngredientLotsResponse:
    lots = IngredientLotService().list_active_lots_by_ingredient(ingredient_id)
    return IngredientLotsResponse(lots=[_lot_response(lot) for lot in lots])


@router.put("/ingredient-lots/{lot_id}", response_model=IngredientLotResponse)
def update_ingredient_lot(lot_id: int, payload: IngredientLotUpdateRequest) -> IngredientLotResponse:
    try:
        lot = IngredientLotService().update_lot(lot_id, _draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except IngredientLotNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient lot was not found.") from exc
    except IngredientLotIngredientMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient was not found.") from exc
    except IngredientLotInactiveIngredientError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient is inactive.") from exc
    return _lot_response(lot)


@router.post("/ingredient-lots/{lot_id}/deactivate", response_model=IngredientLotResponse)
def deactivate_ingredient_lot(lot_id: int) -> IngredientLotResponse:
    try:
        lot = IngredientLotService().deactivate_lot(lot_id)
    except IngredientLotNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient lot was not found.") from exc
    return _lot_response(lot)


def _draft_from_payload(payload: IngredientLotCreateRequest) -> IngredientLotDraft:
    return IngredientLotDraft.create(
        ingredient_id=payload.ingredient_id,
        lot_code=payload.lot_code,
        supplier_name=payload.supplier_name,
        purchased_at=payload.purchased_at,
        expires_at=payload.expires_at,
        unit=payload.unit,
        unit_cost=payload.unit_cost,
        total_cost=payload.total_cost,
        density_g_per_ml=payload.density_g_per_ml,
        notes=payload.notes,
    )


def _lot_response(lot: IngredientLot) -> IngredientLotResponse:
    return IngredientLotResponse(
        id=lot.id,
        ingredient_id=lot.ingredient_id,
        lot_code=lot.lot_code,
        supplier_name=lot.supplier_name,
        purchased_at=lot.purchased_at,
        expires_at=lot.expires_at,
        unit=lot.unit,
        unit_cost=None if lot.unit_cost is None else str(lot.unit_cost),
        total_cost=None if lot.total_cost is None else str(lot.total_cost),
        density_g_per_ml=None if lot.density_g_per_ml is None else str(lot.density_g_per_ml),
        notes=lot.notes,
        is_active=lot.is_active,
        created_at=lot.created_at,
        updated_at=lot.updated_at,
    )
