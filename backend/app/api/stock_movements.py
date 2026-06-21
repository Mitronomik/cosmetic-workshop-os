from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.domain.stock_movements import StockMovementDraft
from app.models.stock_movement import StockMovement
from app.schemas.stock_movements import (
    IngredientLotBalanceResponse,
    StockMovementCreateRequest,
    StockMovementResponse,
    StockMovementsResponse,
)
from app.services.stock_movements import (
    StockMovementInactiveLotError,
    StockMovementInsufficientBalanceError,
    StockMovementLotMissingError,
    StockMovementLotUnitMismatchError,
    StockMovementNotFoundError,
    StockMovementService,
)

router = APIRouter(tags=["stock-movements"])


@router.post("/stock-movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
def create_stock_movement(payload: StockMovementCreateRequest) -> StockMovementResponse:
    try:
        movement = StockMovementService().create_movement(_draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except StockMovementLotMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient lot was not found.") from exc
    except StockMovementInactiveLotError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ingredient lot is inactive.") from exc
    except StockMovementLotUnitMismatchError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Movement unit must match ingredient lot unit.") from exc
    except StockMovementInsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Outgoing movement would make lot balance negative.") from exc
    return _movement_response(movement)


@router.get("/stock-movements", response_model=StockMovementsResponse)
def list_stock_movements() -> StockMovementsResponse:
    movements = StockMovementService().list_movements()
    return StockMovementsResponse(movements=[_movement_response(movement) for movement in movements])


@router.get("/stock-movements/{movement_id}", response_model=StockMovementResponse)
def get_stock_movement(movement_id: int) -> StockMovementResponse:
    try:
        movement = StockMovementService().get_movement(movement_id)
    except StockMovementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock movement was not found.") from exc
    return _movement_response(movement)


@router.get("/ingredient-lots/{lot_id}/movements", response_model=StockMovementsResponse)
def list_stock_movements_by_lot(lot_id: int) -> StockMovementsResponse:
    movements = StockMovementService().list_movements_by_lot(lot_id)
    return StockMovementsResponse(movements=[_movement_response(movement) for movement in movements])


@router.get("/ingredient-lots/{lot_id}/balance", response_model=IngredientLotBalanceResponse)
def get_ingredient_lot_balance(lot_id: int) -> IngredientLotBalanceResponse:
    try:
        quantity = StockMovementService().calculate_lot_quantity(lot_id)
    except StockMovementLotMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient lot was not found.") from exc
    return IngredientLotBalanceResponse(ingredient_lot_id=lot_id, quantity=str(quantity))


def _draft_from_payload(payload: StockMovementCreateRequest) -> StockMovementDraft:
    return StockMovementDraft.create(
        ingredient_lot_id=payload.ingredient_lot_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        unit=payload.unit,
        direction=payload.direction,
        reason=payload.reason,
        occurred_at=payload.occurred_at,
        note=payload.note,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        source=payload.source,
        correction_of_movement_id=payload.correction_of_movement_id,
    )


def _movement_response(movement: StockMovement) -> StockMovementResponse:
    return StockMovementResponse(
        id=movement.id,
        ingredient_lot_id=movement.ingredient_lot_id,
        ingredient_id=movement.ingredient_id,
        movement_type=movement.movement_type,
        quantity=str(movement.quantity),
        unit=movement.unit,
        direction=movement.direction,
        reason=movement.reason,
        occurred_at=movement.occurred_at,
        note=movement.note,
        reference_type=movement.reference_type,
        reference_id=movement.reference_id,
        source=movement.source,
        correction_of_movement_id=movement.correction_of_movement_id,
        created_at=movement.created_at,
    )
