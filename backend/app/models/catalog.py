from dataclasses import dataclass
from enum import StrEnum


class CatalogScope(StrEnum):
    INGREDIENT = "ingredient"
    PACKAGING = "packaging"
    RECIPE = "recipe"


@dataclass(frozen=True)
class CatalogCategory:
    id: int
    scope: CatalogScope
    parent_id: int | None
    name: str
    slug: str
    sort_order: int
    is_system: bool
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CatalogTag:
    id: int
    scope: CatalogScope
    name: str
    slug: str
    color: str
    is_active: bool
    created_at: str
    updated_at: str
