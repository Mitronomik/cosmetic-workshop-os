from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.domain.packaging_stock_movements import PackagingStockMovementDraft
from app.models.packaging_stock_movement import PackagingStockMovement
from app.schemas.packaging_stock_movements import (
    PackagingItemBalanceResponse,
    PackagingStockMovementCreateRequest,
    PackagingStockMovementResponse,
    PackagingStockMovementsResponse,
)
from app.services.packaging_stock_movements import (
    PackagingStockMovementInactiveItemError,
    PackagingStockMovementInsufficientBalanceError,
    PackagingStockMovementItemMissingError,
    PackagingStockMovementNotFoundError,
    PackagingStockMovementService,
)

router = APIRouter(tags=["packaging-stock-movements"])


@router.post("/packaging-stock-movements", response_model=PackagingStockMovementResponse, status_code=status.HTTP_201_CREATED)
def create_packaging_stock_movement(payload: PackagingStockMovementCreateRequest) -> PackagingStockMovementResponse:
    try:
        movement = PackagingStockMovementService().create_movement(_draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except PackagingStockMovementItemMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item was not found.") from exc
    except PackagingStockMovementInactiveItemError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Packaging item is inactive.") from exc
    except PackagingStockMovementInsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Outgoing packaging movement would make item balance negative.") from exc
    return _movement_response(movement)


@router.get("/packaging-stock-movements", response_model=PackagingStockMovementsResponse)
def list_packaging_stock_movements() -> PackagingStockMovementsResponse:
    movements = PackagingStockMovementService().list_movements()
    return PackagingStockMovementsResponse(movements=[_movement_response(movement) for movement in movements])


@router.get("/packaging-stock-movements/{movement_id}", response_model=PackagingStockMovementResponse)
def get_packaging_stock_movement(movement_id: int) -> PackagingStockMovementResponse:
    try:
        movement = PackagingStockMovementService().get_movement(movement_id)
    except PackagingStockMovementNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging stock movement was not found.") from exc
    return _movement_response(movement)


@router.get("/packaging-items/{packaging_item_id}/stock-movements", response_model=PackagingStockMovementsResponse)
def list_packaging_stock_movements_by_item(packaging_item_id: int) -> PackagingStockMovementsResponse:
    try:
        movements = PackagingStockMovementService().list_movements_by_packaging_item(packaging_item_id)
    except PackagingStockMovementItemMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item was not found.") from exc
    return PackagingStockMovementsResponse(movements=[_movement_response(movement) for movement in movements])


@router.get("/packaging-items/{packaging_item_id}/balance", response_model=PackagingItemBalanceResponse)
def get_packaging_item_balance(packaging_item_id: int) -> PackagingItemBalanceResponse:
    try:
        quantity = PackagingStockMovementService().calculate_packaging_item_quantity(packaging_item_id)
    except PackagingStockMovementItemMissingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item was not found.") from exc
    return PackagingItemBalanceResponse(packaging_item_id=packaging_item_id, quantity=str(quantity))


def _draft_from_payload(payload: PackagingStockMovementCreateRequest) -> PackagingStockMovementDraft:
    return PackagingStockMovementDraft.create(
        packaging_item_id=payload.packaging_item_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        unit=payload.unit,
        occurred_at=payload.occurred_at,
        reason=payload.reason,
        source=payload.source,
        notes=payload.notes,
    )


def _movement_response(movement: PackagingStockMovement) -> PackagingStockMovementResponse:
    return PackagingStockMovementResponse(
        id=movement.id,
        packaging_item_id=movement.packaging_item_id,
        movement_type=movement.movement_type,
        quantity=str(movement.quantity),
        unit=movement.unit,
        direction=movement.direction,
        occurred_at=movement.occurred_at,
        reason=movement.reason,
        source=movement.source,
        notes=movement.notes,
        created_at=movement.created_at,
    )
