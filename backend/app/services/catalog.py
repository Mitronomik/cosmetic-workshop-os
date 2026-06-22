from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.catalog import CatalogCategoryDraft, CatalogTagDraft, parse_scope
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.models.catalog import CatalogScope
from app.repositories.audit import AuditLogRepository
from app.repositories.catalog import CatalogRepository
from app.repositories.ingredients import IngredientRepository
from app.repositories.packaging_items import PackagingItemRepository
from app.repositories.recipes import RecipeRepository

_ASSIGN = {
    "ingredient": (
        "ingredients",
        "ingredient_catalog_tags",
        "ingredient_id",
        IngredientRepository,
        "ingredient",
        "ingredient.catalog_category.assigned",
        "ingredient.catalog_tags.updated",
    ),
    "packaging": (
        "packaging_items",
        "packaging_item_catalog_tags",
        "packaging_item_id",
        PackagingItemRepository,
        "packaging_item",
        "packaging_item.catalog_category.assigned",
        "packaging_item.catalog_tags.updated",
    ),
    "recipe": (
        "recipe_templates",
        "recipe_template_catalog_tags",
        "recipe_template_id",
        RecipeRepository,
        "recipe_template",
        "recipe_template.catalog_category.assigned",
        "recipe_template.catalog_tags.updated",
    ),
}


class CatalogService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repo = CatalogRepository(config)
        self.audit = AuditLogRepository(config)

    def create_category(self, draft):
        with transaction(self.config) as c:
            self._validate_parent(draft, c)
            obj = self.repo.create_category(draft, connection=c)
            self.audit.create_log(
                action="catalog_category.created",
                entity_type="catalog_category",
                entity_id=str(obj.id),
                summary=f"Catalog category created: {obj.name}",
                metadata={"scope": obj.scope.value},
                connection=c,
            )
        return obj

    def list_categories(self, scope, include_inactive=False):
        return self.repo.list_categories(parse_scope(scope), include_inactive)

    def get_category(self, id):
        return self.repo.get_category(id)

    def update_category(self, id, draft):
        with transaction(self.config) as c:
            self._validate_parent(draft, c)
            obj = self.repo.update_category(id, draft, connection=c)
            self.audit.create_log(
                action="catalog_category.updated",
                entity_type="catalog_category",
                entity_id=str(obj.id),
                summary=f"Catalog category updated: {obj.name}",
                metadata={"scope": obj.scope.value},
                connection=c,
            )
        return obj

    def archive_category(self, id):
        with transaction(self.config) as c:
            obj = self.repo.archive_category(id, connection=c)
            self.audit.create_log(
                action="catalog_category.archived",
                entity_type="catalog_category",
                entity_id=str(obj.id),
                summary=f"Catalog category archived: {obj.name}",
                metadata={"scope": obj.scope.value},
                connection=c,
            )
        return obj

    def create_tag(self, draft):
        with transaction(self.config) as c:
            obj = self.repo.create_tag(draft, connection=c)
            self.audit.create_log(
                action="catalog_tag.created",
                entity_type="catalog_tag",
                entity_id=str(obj.id),
                summary=f"Catalog tag created: {obj.name}",
                metadata={"scope": obj.scope.value},
                connection=c,
            )
        return obj

    def list_tags(self, scope, include_inactive=False):
        return self.repo.list_tags(parse_scope(scope), include_inactive)

    def get_tag(self, id):
        return self.repo.get_tag(id)

    def update_tag(self, id, draft):
        with transaction(self.config) as c:
            obj = self.repo.update_tag(id, draft, connection=c)
            self.audit.create_log(
                action="catalog_tag.updated",
                entity_type="catalog_tag",
                entity_id=str(obj.id),
                summary=f"Catalog tag updated: {obj.name}",
                metadata={"scope": obj.scope.value},
                connection=c,
            )
        return obj

    def archive_tag(self, id):
        with transaction(self.config) as c:
            obj = self.repo.archive_tag(id, connection=c)
            self.audit.create_log(
                action="catalog_tag.archived",
                entity_type="catalog_tag",
                entity_id=str(obj.id),
                summary=f"Catalog tag archived: {obj.name}",
                metadata={"scope": obj.scope.value},
                connection=c,
            )
        return obj

    def assign_category(self, kind, item_id, category_id):
        table, _, _, repo_cls, entity, action, _ = _ASSIGN[kind]
        scope = parse_scope(kind)
        with transaction(self.config) as c:
            self._ensure_item(kind, item_id, c)
            if category_id is not None:
                cat = self.repo.get_category(category_id, connection=c)
                if cat.scope != scope or not cat.is_active:
                    raise DomainValidationError(
                        DomainIssue(
                            DomainIssueCode.INVALID_CATEGORY,
                            "Категория не подходит для этого раздела или архивирована.",
                            "catalog_category_id",
                            str(category_id),
                            "Выберите активную категорию того же раздела.",
                        )
                    )
            self.repo.assign_category(table, "id", item_id, category_id, connection=c)
            self.audit.create_log(
                action=action,
                entity_type=entity,
                entity_id=str(item_id),
                summary="Catalog category assigned",
                metadata={"catalog_category_id": category_id},
                connection=c,
            )

    def replace_tags(self, kind, item_id, tag_ids):
        _, table, id_col, _, entity, _, action = _ASSIGN[kind]
        scope = parse_scope(kind)
        unique = sorted(set(tag_ids))
        with transaction(self.config) as c:
            self._ensure_item(kind, item_id, c)
            for tid in unique:
                tag = self.repo.get_tag(tid, connection=c)
                if tag.scope != scope or not tag.is_active:
                    raise DomainValidationError(
                        DomainIssue(
                            DomainIssueCode.INVALID_CATEGORY,
                            "Тег не подходит для этого раздела или архивирован.",
                            "tag_ids",
                            str(tid),
                            "Выберите активные теги того же раздела.",
                        )
                    )
            self.repo.replace_tags(table, id_col, item_id, unique, connection=c)
            self.audit.create_log(
                action=action,
                entity_type=entity,
                entity_id=str(item_id),
                summary="Catalog tags updated",
                metadata={"tag_ids": unique},
                connection=c,
            )

    def _validate_parent(self, draft, connection):
        if draft.parent_id is not None:
            parent = self.repo.get_category(draft.parent_id, connection=connection)
            if parent.scope != draft.scope:
                raise DomainValidationError(
                    DomainIssue(
                        DomainIssueCode.INVALID_CATEGORY,
                        "Родительская категория должна быть из того же раздела.",
                        "parent_id",
                        str(draft.parent_id),
                        "Выберите родительскую категорию того же раздела.",
                    )
                )

    def _ensure_item(self, kind, item_id, connection):
        if kind == "ingredient":
            IngredientRepository(self.config).get_by_id_for_update(
                item_id, connection=connection
            )
        elif kind == "packaging":
            PackagingItemRepository(self.config).get_by_id_for_update(
                item_id, connection=connection
            )
        else:
            RecipeRepository(self.config).get_template(item_id, connection=connection)
