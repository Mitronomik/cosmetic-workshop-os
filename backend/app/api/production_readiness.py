from fastapi import APIRouter, HTTPException

from app.domain.errors import DomainValidationError
from app.repositories.client_recipes import ClientRecipeNotFoundError
from app.repositories.orders import OrderNotFoundError
from app.repositories.recipes import RecipeVersionNotFoundError
from app.schemas.production_readiness import ProductionReadinessResponse
from app.services.production_readiness import ProductionReadinessLifecycleError, ProductionReadinessService

router = APIRouter(tags=["production-readiness"])


@router.post("/orders/{order_id}/check-production-readiness", response_model=ProductionReadinessResponse)
def check_order_production_readiness(order_id: int):
    try:
        return ProductionReadinessService().check_order(order_id)
    except DomainValidationError as exc:
        raise HTTPException(422, detail=exc.issue.__dict__) from exc
    except OrderNotFoundError as exc:
        raise HTTPException(404, detail="Order was not found.") from exc
    except (RecipeVersionNotFoundError, ClientRecipeNotFoundError) as exc:
        raise HTTPException(404, detail="Linked recipe record was not found.") from exc
    except ProductionReadinessLifecycleError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
