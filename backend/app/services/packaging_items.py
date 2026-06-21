from app.db.config import DatabaseConfig
from app.domain.packaging_items import PackagingItemDraft
from app.models.packaging_item import PackagingItem
from app.repositories.audit import AuditLogRepository
from app.repositories.packaging_items import PackagingItemNotFoundError, PackagingItemRepository


class PackagingItemService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.repository = PackagingItemRepository(config)
        self.audit = AuditLogRepository(config)

    def create_packaging_item(self, draft: PackagingItemDraft) -> PackagingItem:
        item = self.repository.create(draft)
        self.audit.create_log(action="packaging_item.created", entity_type="packaging_item", entity_id=str(item.id), summary=f"Packaging item created: {item.name}", metadata={"kind": item.kind.value})
        return item

    def get_packaging_item(self, packaging_item_id: int) -> PackagingItem:
        return self.repository.get_by_id(packaging_item_id)

    def list_active_packaging_items(self) -> list[PackagingItem]:
        return self.repository.list_active()

    def update_packaging_item(self, packaging_item_id: int, draft: PackagingItemDraft) -> PackagingItem:
        item = self.repository.update_basic(packaging_item_id, draft)
        self.audit.create_log(action="packaging_item.updated", entity_type="packaging_item", entity_id=str(item.id), summary=f"Packaging item updated: {item.name}", metadata={"kind": item.kind.value})
        return item

    def deactivate_packaging_item(self, packaging_item_id: int) -> PackagingItem:
        item = self.repository.deactivate(packaging_item_id)
        self.audit.create_log(action="packaging_item.deactivated", entity_type="packaging_item", entity_id=str(item.id), summary=f"Packaging item deactivated: {item.name}")
        return item


__all__ = ["PackagingItemNotFoundError", "PackagingItemService"]
