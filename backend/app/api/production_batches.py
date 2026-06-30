from fastapi import APIRouter, HTTPException, Query

from app.repositories.orders import OrderNotFoundError, OrderRepository
from app.repositories.production_batches import ProductionBatchNotFoundError, ProductionBatchRepository
from app.schemas.production_batches import ProductionBatchDetailResponse, ProductionBatchIngredientResponse, ProductionBatchListItemResponse, ProductionBatchListResponse, ProductionBatchPackagingResponse

router = APIRouter(tags=["production-batches"])


@router.get("/production-batches", response_model=ProductionBatchListResponse)
def list_production_batches(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    batches = ProductionBatchRepository().list_batches(limit=limit, offset=offset)
    return ProductionBatchListResponse(
        production_batches=[_list_item_response(item) for item in batches],
        limit=limit,
        offset=offset,
    )


@router.get("/production-batches/{batch_id}", response_model=ProductionBatchDetailResponse)
def get_production_batch(batch_id: int):
    try:
        return _detail_response(ProductionBatchRepository().get_detail(batch_id))
    except ProductionBatchNotFoundError as exc:
        raise HTTPException(404, detail="Production batch was not found.") from exc


@router.get("/orders/{order_id}/production-batch", response_model=ProductionBatchDetailResponse)
def get_order_production_batch(order_id: int):
    try:
        OrderRepository().get_by_id(order_id)
        return _detail_response(ProductionBatchRepository().get_detail_by_order_id(order_id))
    except OrderNotFoundError as exc:
        raise HTTPException(404, detail="Order was not found.") from exc
    except ProductionBatchNotFoundError as exc:
        raise HTTPException(404, detail="Production batch for this order was not found.") from exc


def _s(v): return None if v is None else str(v)


def _list_item_response(item) -> ProductionBatchListItemResponse:
    return ProductionBatchListItemResponse(
        id=item.id, order_id=item.order_id, product_name=item.product_name, client_id=item.client_id, client_name=item.client_name,
        recipe_version_id=item.recipe_version_id, client_recipe_id=item.client_recipe_id,
        final_batch_value=str(item.final_batch_value), final_batch_unit=item.final_batch_unit.value,
        total_cost=_s(item.total_cost), sale_price=_s(item.sale_price), tax=_s(item.tax), margin=_s(item.margin), margin_percent=_s(item.margin_percent),
        produced_at=item.produced_at, ingredient_line_count=item.ingredient_line_count, packaging_line_count=item.packaging_line_count, notes=item.notes,
    )


def _detail_response(detail) -> ProductionBatchDetailResponse:
    b = detail.batch
    return ProductionBatchDetailResponse(
        id=b.id, order_id=b.order_id, product_name=detail.product_name, client_id=detail.client_id, client_name=detail.client_name,
        recipe_version_id=b.recipe_version_id, client_recipe_id=b.client_recipe_id,
        final_batch_value=str(b.final_batch_value), final_batch_unit=b.final_batch_unit.value,
        component_cost=_s(b.component_cost), packaging_cost=_s(b.packaging_cost), other_cost=str(b.other_cost), total_cost=_s(b.total_cost), sale_price=_s(b.sale_price), tax=_s(b.tax), margin=_s(b.margin), margin_percent=_s(b.margin_percent), produced_at=b.produced_at, notes=b.notes, created_at=b.created_at,
        ingredients=[ProductionBatchIngredientResponse(id=i.id, production_batch_id=i.production_batch_id, ingredient_id=i.ingredient_id, ingredient_lot_id=i.ingredient_lot_id, ingredient_name_snapshot=i.ingredient_name_snapshot, lot_code_snapshot=i.lot_code_snapshot, required_quantity=str(i.required_quantity), consumed_quantity=str(i.consumed_quantity), unit=i.unit.value, unit_cost_snapshot=_s(i.unit_cost_snapshot), total_cost_snapshot=_s(i.total_cost_snapshot), expiration_date_snapshot=i.expiration_date_snapshot, created_at=i.created_at) for i in detail.ingredients],
        packaging=[ProductionBatchPackagingResponse(id=p.id, production_batch_id=p.production_batch_id, packaging_item_id=p.packaging_item_id, packaging_name_snapshot=p.packaging_name_snapshot, quantity=str(p.quantity), unit=p.unit.value, unit_cost_snapshot=_s(p.unit_cost_snapshot), total_cost_snapshot=_s(p.total_cost_snapshot), created_at=p.created_at) for p in detail.packaging],
    )
