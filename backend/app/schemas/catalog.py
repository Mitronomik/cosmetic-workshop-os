from pydantic import BaseModel


class CatalogCategoryCreateRequest(BaseModel):
    scope: str
    name: str
    slug: str | None = None
    parent_id: int | None = None
    sort_order: int = 0


class CatalogCategoryUpdateRequest(CatalogCategoryCreateRequest):
    pass


class CatalogCategoryResponse(BaseModel):
    id: int
    scope: str
    parent_id: int | None
    name: str
    slug: str
    sort_order: int
    is_system: bool
    is_active: bool
    created_at: str
    updated_at: str


class CatalogCategoriesResponse(BaseModel):
    categories: list[CatalogCategoryResponse]


class CatalogTagCreateRequest(BaseModel):
    scope: str
    name: str
    slug: str | None = None
    color: str = ""


class CatalogTagUpdateRequest(CatalogTagCreateRequest):
    pass


class CatalogTagResponse(BaseModel):
    id: int
    scope: str
    name: str
    slug: str
    color: str
    is_active: bool
    created_at: str
    updated_at: str


class CatalogTagsResponse(BaseModel):
    tags: list[CatalogTagResponse]


class CatalogCategoryAssignmentRequest(BaseModel):
    catalog_category_id: int | None


class CatalogTagsAssignmentRequest(BaseModel):
    tag_ids: list[int]


class AssignmentResponse(BaseModel):
    ok: bool = True
