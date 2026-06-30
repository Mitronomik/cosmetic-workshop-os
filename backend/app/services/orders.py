from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.orders import OrderDraft
from app.domain.recipes import require_positive_id
from app.models.client_recipe import ClientRecipeStatus
from app.models.order import Order, OrderStatus
from app.repositories.audit import AuditLogRepository
from app.repositories.client_recipes import ClientRecipeNotFoundError, ClientRecipeRepository
from app.repositories.clients import ClientNotFoundError, ClientRepository
from app.repositories.packaging_items import PackagingItemNotFoundError, PackagingItemRepository
from app.repositories.recipes import RecipeRepository, RecipeVersionNotFoundError
from app.repositories.orders import OrderNotFoundError, OrderRepository


class OrderClientInactiveError(ValueError): pass
class OrderClientRecipeMismatchError(ValueError): pass
class OrderClientRecipeInactiveError(ValueError): pass
class OrderPackagingInactiveError(ValueError): pass
class OrderLifecycleError(ValueError): pass


class OrderService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config=config; self.repository=OrderRepository(config); self.clients=ClientRepository(config); self.recipes=RecipeRepository(config); self.client_recipes=ClientRecipeRepository(config); self.packaging=PackagingItemRepository(config); self.audit=AuditLogRepository(config)

    def create(self, draft: OrderDraft) -> Order:
        self._validate_refs(draft, require_active=True)
        with transaction(self.config) as connection:
            order=self.repository.create(draft, connection=connection)
            self.audit.create_log(action="order.created", entity_type="order", entity_id=str(order.id), summary=f"Order created: {order.product_name}", metadata=self._metadata(order), connection=connection)
        return order

    def get_by_id(self, order_id:int) -> Order:
        return self.repository.get_by_id(require_positive_id(order_id, field="order_id", label="Заказ"))

    def list_orders(self, *, include_inactive: bool=True, status: OrderStatus | str | None=None, client_id:int | None=None) -> list[Order]:
        if status is not None: status = status if isinstance(status, OrderStatus) else OrderStatus(status)
        if client_id is not None: require_positive_id(client_id, field="client_id", label="Клиент")
        return self.repository.list_orders(include_inactive=include_inactive, status=status, client_id=client_id)

    def update(self, order_id:int, draft: OrderDraft) -> Order:
        order_id=require_positive_id(order_id, field="order_id", label="Заказ")
        current=self.repository.get_by_id(order_id)
        if current.status == OrderStatus.ARCHIVED or not current.is_active: raise OrderLifecycleError("Archived order cannot be updated.")
        if current.status == OrderStatus.CANCELLED: raise OrderLifecycleError("Cancelled order cannot be updated.")
        self._validate_refs(draft, require_active=True)
        with transaction(self.config) as connection:
            order=self.repository.update(order_id, draft, connection=connection)
            self.audit.create_log(action="order.updated", entity_type="order", entity_id=str(order.id), summary=f"Order updated: {order.product_name}", metadata=self._metadata(order), connection=connection)
        return order

    def cancel(self, order_id:int) -> Order:
        order_id=require_positive_id(order_id, field="order_id", label="Заказ")
        current=self.repository.get_by_id(order_id)
        if current.status == OrderStatus.ARCHIVED or not current.is_active: raise OrderLifecycleError("Archived order cannot be cancelled.")
        if current.status == OrderStatus.CANCELLED: return current
        with transaction(self.config) as connection:
            order=self.repository.cancel(order_id, connection=connection)
            self.audit.create_log(action="order.cancelled", entity_type="order", entity_id=str(order.id), summary=f"Order cancelled: {order.product_name}", metadata=self._metadata(order), connection=connection)
        return order

    def archive(self, order_id:int) -> Order:
        order_id=require_positive_id(order_id, field="order_id", label="Заказ")
        current=self.repository.get_by_id(order_id)
        if current.status == OrderStatus.ARCHIVED and not current.is_active: return current
        with transaction(self.config) as connection:
            order=self.repository.archive(order_id, connection=connection)
            self.audit.create_log(action="order.archived", entity_type="order", entity_id=str(order.id), summary=f"Order archived: {order.product_name}", metadata=self._metadata(order), connection=connection)
        return order

    def _validate_refs(self, draft: OrderDraft, *, require_active: bool) -> None:
        client=self.clients.get_by_id(draft.client_id)
        if require_active and not client.is_active: raise OrderClientInactiveError("Client is inactive.")
        if draft.recipe_version_id is not None: self.recipes.get_version(draft.recipe_version_id)
        if draft.client_recipe_id is not None:
            detail=self.client_recipes.get_detail(draft.client_recipe_id); cr=detail.client_recipe
            if cr.client_id != draft.client_id: raise OrderClientRecipeMismatchError("Client recipe belongs to a different client.")
            if require_active and (not cr.is_active or cr.status == ClientRecipeStatus.ARCHIVED): raise OrderClientRecipeInactiveError("Client recipe is inactive or archived.")
        if draft.packaging_item_id is not None:
            packaging=self.packaging.get_by_id(draft.packaging_item_id)
            if require_active and not packaging.is_active: raise OrderPackagingInactiveError("Packaging item is inactive.")

    def _metadata(self, order: Order) -> dict:
        return {"client_id": order.client_id, "recipe_version_id": order.recipe_version_id, "client_recipe_id": order.client_recipe_id, "status": order.status.value}


__all__=["OrderService","OrderNotFoundError","ClientNotFoundError","RecipeVersionNotFoundError","ClientRecipeNotFoundError","PackagingItemNotFoundError","OrderClientInactiveError","OrderClientRecipeMismatchError","OrderClientRecipeInactiveError","OrderPackagingInactiveError","OrderLifecycleError"]
