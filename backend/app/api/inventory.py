from fastapi import APIRouter, Query

from app.schemas.inventory import IngredientLotBalancesResponse, InventoryOverviewResponse, PackagingBalancesResponse
from app.services.inventory import DEFAULT_EXPIRATION_WINDOW_DAYS, InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/ingredient-lot-balances", response_model=IngredientLotBalancesResponse)
def list_ingredient_lot_balances(
    include_inactive: bool = False,
    only_positive: bool = False,
    expires_within_days: int = Query(DEFAULT_EXPIRATION_WINDOW_DAYS, ge=0),
) -> IngredientLotBalancesResponse:
    balances = InventoryService().list_ingredient_lot_balances(include_inactive=include_inactive, only_positive=only_positive, expires_within_days=expires_within_days)
    return IngredientLotBalancesResponse(ingredient_lot_balances=balances)


@router.get("/packaging-balances", response_model=PackagingBalancesResponse)
def list_packaging_balances(include_inactive: bool = False, only_positive: bool = False) -> PackagingBalancesResponse:
    balances = InventoryService().list_packaging_balances(include_inactive=include_inactive, only_positive=only_positive)
    return PackagingBalancesResponse(packaging_balances=balances)


@router.get("/overview", response_model=InventoryOverviewResponse)
def get_inventory_overview(expires_within_days: int = Query(DEFAULT_EXPIRATION_WINDOW_DAYS, ge=0)) -> InventoryOverviewResponse:
    return InventoryService().get_overview(expires_within_days=expires_within_days)
