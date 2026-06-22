from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.domain.packaging_items import PackagingItemDraft
from app.models.packaging_item import PackagingItem
from app.repositories.packaging_items import PackagingItemNotFoundError
from app.schemas.packaging_items import PackagingItemCreateRequest, PackagingItemResponse, PackagingItemsResponse, PackagingItemUpdateRequest
from app.services.packaging_items import PackagingItemService

router = APIRouter(prefix="/packaging-items", tags=["packaging-items"])


@router.post("", response_model=PackagingItemResponse, status_code=status.HTTP_201_CREATED)
def create_packaging_item(payload: PackagingItemCreateRequest) -> PackagingItemResponse:
    try:
        item = PackagingItemService().create_packaging_item(_draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    return _response(item)


@router.get("", response_model=PackagingItemsResponse)
def list_active_packaging_items() -> PackagingItemsResponse:
    items = PackagingItemService().list_active_packaging_items()
    return PackagingItemsResponse(packaging_items=[_response(item) for item in items])


@router.get("/{packaging_item_id}", response_model=PackagingItemResponse)
def get_packaging_item(packaging_item_id: int) -> PackagingItemResponse:
    try:
        item = PackagingItemService().get_packaging_item(packaging_item_id)
    except PackagingItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item was not found.") from exc
    return _response(item)


@router.put("/{packaging_item_id}", response_model=PackagingItemResponse)
def update_packaging_item(packaging_item_id: int, payload: PackagingItemUpdateRequest) -> PackagingItemResponse:
    try:
        item = PackagingItemService().update_packaging_item(packaging_item_id, _draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except PackagingItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item was not found.") from exc
    return _response(item)


@router.post("/{packaging_item_id}/deactivate", response_model=PackagingItemResponse)
def deactivate_packaging_item(packaging_item_id: int) -> PackagingItemResponse:
    try:
        item = PackagingItemService().deactivate_packaging_item(packaging_item_id)
    except PackagingItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Packaging item was not found.") from exc
    return _response(item)


def _draft_from_payload(payload: PackagingItemCreateRequest) -> PackagingItemDraft:
    return PackagingItemDraft.create(**payload.model_dump())


def _response(item: PackagingItem) -> PackagingItemResponse:
    return PackagingItemResponse(
        id=item.id,
        name=item.name,
        kind=item.kind,
        unit=item.unit,
        capacity_value=None if item.capacity_value is None else str(item.capacity_value),
        capacity_unit=item.capacity_unit,
        material=item.material,
        supplier_hint=item.supplier_hint,
        unit_cost=None if item.unit_cost is None else str(item.unit_cost),
        notes=item.notes,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
        catalog_category_id=item.catalog_category_id,
        catalog_tag_ids=list(item.catalog_tag_ids),
    )
