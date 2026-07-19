from fastapi import APIRouter, HTTPException

from app.domain.errors import DomainValidationError
from app.repositories.client_recipes import ClientRecipeNotFoundError
from app.repositories.orders import OrderNotFoundError
from app.repositories.packaging_stock_movements import PackagingStockMovementInactiveItemError, PackagingStockMovementInsufficientBalanceError
from app.repositories.production_batches import ProductionBatchAlreadyExistsError
from app.repositories.recipes import RecipeVersionNotFoundError
from app.repositories.stock_movements import StockMovementInactiveLotError, StockMovementInsufficientBalanceError, StockMovementLotUnitMismatchError
from app.schemas.production_batches import ProductionBatchDetailResponse, ProductionBatchIngredientResponse, ProductionBatchPackagingResponse, ProductionConfirmRequest
from app.services.production_confirmation import ProductionConfirmationLifecycleError, ProductionConfirmationReadinessError, ProductionConfirmationRequiredError, ProductionConfirmationService
from app.services.production_readiness import ProductionReadinessLifecycleError

router = APIRouter(tags=["production-confirmation"])


def _error(code: str, message: str, *, next_action: str | None = None):
    detail = {"code": code, "message": message}
    if next_action:
        detail["next_action"] = next_action
    return detail


@router.post("/orders/{order_id}/produce", response_model=ProductionBatchDetailResponse)
def produce_order(order_id: int, payload: ProductionConfirmRequest):
    try:
        return _response(ProductionConfirmationService().produce_order(order_id, payload.confirm, payload.notes))
    except DomainValidationError as exc:
        raise HTTPException(422, detail={"code": str(exc.issue.code), "message": exc.issue.message, "field": exc.issue.field, "next_action": exc.issue.next_action}) from exc
    except ProductionConfirmationRequiredError as exc:
        raise HTTPException(422, detail=_error("explicit_confirmation_required", "Для изготовления нужно явно подтвердить действие.", next_action="Нажмите кнопку подтверждения изготовления ещё раз, если заказ всё ещё готов.")) from exc
    except OrderNotFoundError as exc:
        raise HTTPException(404, detail=_error("order_not_found", "Заказ больше не найден.", next_action="Обновите список заказов и откройте карточку снова.")) from exc
    except (RecipeVersionNotFoundError, ClientRecipeNotFoundError) as exc:
        raise HTTPException(404, detail=_error("linked_source_not_found", "Связанный рецепт или индивидуальная формула больше не доступны.", next_action="Обновите заказ и выберите доступную основу.")) from exc
    except ProductionConfirmationReadinessError as exc:
        raise HTTPException(409, detail=_error(getattr(exc, "code", "readiness_blocked"), str(exc), next_action="Запустите проверку готовности заново и устраните новые препятствия.")) from exc
    except (
        ProductionConfirmationLifecycleError,
        ProductionReadinessLifecycleError,
        ProductionBatchAlreadyExistsError,
        StockMovementInsufficientBalanceError,
        PackagingStockMovementInsufficientBalanceError,
        StockMovementInactiveLotError,
        PackagingStockMovementInactiveItemError,
        StockMovementLotUnitMismatchError,
    ) as exc:
        message = str(exc) if isinstance(exc, (ProductionConfirmationLifecycleError, ProductionReadinessLifecycleError)) else "Заказ нельзя изготовить сейчас: состояние заказа, склада или партии изменилось."
        raise HTTPException(409, detail=_error("production_conflict", message, next_action="Обновите заказ и запустите проверку готовности заново.")) from exc
    except Exception as exc:
        raise HTTPException(500, detail=_error("production_unexpected_failure", "Неожиданная ошибка локального приложения. Статус изготовления нужно проверить обновлением заказа.", next_action="Обновите заказ и историю производства перед повторной попыткой.")) from exc


def _s(v): return None if v is None else str(v)


def _response(detail) -> ProductionBatchDetailResponse:
    b = detail.batch
    return ProductionBatchDetailResponse(
        id=b.id, order_id=b.order_id, recipe_version_id=b.recipe_version_id, client_recipe_id=b.client_recipe_id,
        final_batch_value=str(b.final_batch_value), final_batch_unit=b.final_batch_unit.value,
        component_cost=_s(b.component_cost), packaging_cost=_s(b.packaging_cost), other_cost=str(b.other_cost), total_cost=_s(b.total_cost), sale_price=_s(b.sale_price), tax=_s(b.tax), margin=_s(b.margin), margin_percent=_s(b.margin_percent), produced_at=b.produced_at, notes=b.notes, created_at=b.created_at,
        ingredients=[ProductionBatchIngredientResponse(id=i.id, production_batch_id=i.production_batch_id, ingredient_id=i.ingredient_id, ingredient_lot_id=i.ingredient_lot_id, ingredient_name_snapshot=i.ingredient_name_snapshot, lot_code_snapshot=i.lot_code_snapshot, required_quantity=str(i.required_quantity), consumed_quantity=str(i.consumed_quantity), unit=i.unit.value, unit_cost_snapshot=_s(i.unit_cost_snapshot), total_cost_snapshot=_s(i.total_cost_snapshot), expiration_date_snapshot=i.expiration_date_snapshot, created_at=i.created_at) for i in detail.ingredients],
        packaging=[ProductionBatchPackagingResponse(id=p.id, production_batch_id=p.production_batch_id, packaging_item_id=p.packaging_item_id, packaging_name_snapshot=p.packaging_name_snapshot, quantity=str(p.quantity), unit=p.unit.value, unit_cost_snapshot=_s(p.unit_cost_snapshot), total_cost_snapshot=_s(p.total_cost_snapshot), created_at=p.created_at) for p in detail.packaging],
    )
