from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.packaging_stock_movements import PackagingMovementDirection
from app.domain.stock_movements import MovementDirection
from app.repositories.inventory import InventoryRepository, packaging_kind_label
from app.schemas.inventory import IngredientLotBalanceRead, InventoryOverviewResponse, PackagingBalanceRead

DEFAULT_EXPIRATION_WINDOW_DAYS = 30


class InventoryService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.repository = InventoryRepository(config)

    def list_ingredient_lot_balances(self, *, include_inactive: bool = False, only_positive: bool = False, expires_within_days: int = DEFAULT_EXPIRATION_WINDOW_DAYS, today: date | None = None) -> list[IngredientLotBalanceRead]:
        balances_by_lot: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
        for movement in self.repository.list_stock_movement_quantities():
            quantity = Decimal(movement["quantity"])
            balances_by_lot[movement["ingredient_lot_id"]] += quantity if movement["direction"] == MovementDirection.IN.value else -quantity
        current_day = today or date.today()
        result: list[IngredientLotBalanceRead] = []
        for row in self.repository.list_ingredient_lots():
            balance = balances_by_lot[row["lot_id"]]
            if not include_inactive and not bool(row["is_active"]):
                continue
            if only_positive and balance <= 0:
                continue
            days, is_expired, expires_soon = _expiration_flags(row["expiration_date"], current_day, expires_within_days)
            result.append(
                IngredientLotBalanceRead(
                    lot_id=row["lot_id"], ingredient_id=row["ingredient_id"], ingredient_name=row["ingredient_name"], lot_code=row["lot_code"], supplier=row["supplier"], unit=row["unit"], balance_quantity=str(balance), purchase_date=row["purchase_date"], expiration_date=row["expiration_date"], is_expired=is_expired, expires_soon=expires_soon, days_until_expiration=days, is_active=bool(row["is_active"]), has_positive_balance=balance > 0, created_at=row["created_at"], updated_at=row["updated_at"], cost_per_unit=row["cost_per_unit"], density_value=row["density_value"], density_unit="g/ml" if row["density_value"] is not None else None
                )
            )
        return result

    def list_packaging_balances(self, *, include_inactive: bool = False, only_positive: bool = False) -> list[PackagingBalanceRead]:
        balances_by_item: dict[int, Decimal] = defaultdict(lambda: Decimal("0"))
        for movement in self.repository.list_packaging_movement_quantities():
            quantity = Decimal(movement["quantity"])
            balances_by_item[movement["packaging_item_id"]] += quantity if movement["direction"] == PackagingMovementDirection.IN.value else -quantity
        result: list[PackagingBalanceRead] = []
        for row in self.repository.list_packaging_items():
            balance = balances_by_item[row["packaging_item_id"]]
            if not include_inactive and not bool(row["is_active"]):
                continue
            if only_positive and balance <= 0:
                continue
            result.append(
                PackagingBalanceRead(
                    packaging_item_id=row["packaging_item_id"], name=row["name"], kind=row["kind"], kind_label=packaging_kind_label(row["kind"]), unit=row["unit"], balance_quantity=str(balance), capacity_value=row["capacity_value"], capacity_unit=row["capacity_unit"], material=row["material"], supplier_hint=row["supplier_hint"], is_active=bool(row["is_active"]), has_positive_balance=balance > 0, created_at=row["created_at"], updated_at=row["updated_at"], unit_cost=row["unit_cost"], notes=row["notes"]
                )
            )
        return result

    def get_overview(self, *, expires_within_days: int = DEFAULT_EXPIRATION_WINDOW_DAYS) -> InventoryOverviewResponse:
        ingredient_lots = self.list_ingredient_lot_balances(include_inactive=True, expires_within_days=expires_within_days)
        packaging_items = self.list_packaging_balances(include_inactive=True)
        return InventoryOverviewResponse(
            ingredient_lots_total=len(ingredient_lots),
            ingredient_lots_with_positive_balance=sum(1 for row in ingredient_lots if row.has_positive_balance),
            ingredient_lots_zero_balance=sum(1 for row in ingredient_lots if Decimal(row.balance_quantity) == 0),
            ingredient_lots_expired=sum(1 for row in ingredient_lots if row.is_expired),
            ingredient_lots_expiring_soon=sum(1 for row in ingredient_lots if row.expires_soon),
            active_ingredient_lots_total=sum(1 for row in ingredient_lots if row.is_active),
            packaging_items_total=len(packaging_items),
            packaging_items_with_positive_balance=sum(1 for row in packaging_items if row.has_positive_balance),
            packaging_items_zero_balance=sum(1 for row in packaging_items if Decimal(row.balance_quantity) == 0),
            active_packaging_items_total=sum(1 for row in packaging_items if row.is_active),
            generated_at=datetime.now(UTC).isoformat(),
        )


def _expiration_flags(value: str | None, today: date, window_days: int) -> tuple[int | None, bool, bool]:
    if value is None:
        return None, False, False
    expiration = date.fromisoformat(value)
    days = (expiration - today).days
    return days, days < 0, 0 <= days <= window_days
