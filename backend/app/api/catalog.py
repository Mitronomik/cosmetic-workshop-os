from fastapi import APIRouter, HTTPException, status
from app.domain.catalog import CatalogCategoryDraft, CatalogTagDraft
from app.domain.errors import DomainValidationError
from app.repositories.catalog import (
    CatalogCategoryNotFoundError,
    CatalogDuplicateSlugError,
    CatalogTagNotFoundError,
)
from app.schemas.catalog import *
from app.services.catalog import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])


def _err(exc):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__
    ) from exc


def _cat(o):
    return CatalogCategoryResponse(
        id=o.id,
        scope=o.scope.value,
        parent_id=o.parent_id,
        name=o.name,
        slug=o.slug,
        sort_order=o.sort_order,
        is_system=o.is_system,
        is_active=o.is_active,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


def _tag(o):
    return CatalogTagResponse(
        id=o.id,
        scope=o.scope.value,
        name=o.name,
        slug=o.slug,
        color=o.color,
        is_active=o.is_active,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


@router.post("/categories", response_model=CatalogCategoryResponse, status_code=201)
def create_category(p: CatalogCategoryCreateRequest):
    try:
        return _cat(
            CatalogService().create_category(
                CatalogCategoryDraft.create(**p.model_dump())
            )
        )
    except DomainValidationError as exc:
        _err(exc)
    except CatalogCategoryNotFoundError as exc:
        raise HTTPException(404, "Category was not found.") from exc
    except CatalogDuplicateSlugError as exc:
        raise HTTPException(409, "Category slug already exists in this scope.") from exc


@router.get("/categories", response_model=CatalogCategoriesResponse)
def list_categories(scope: str, include_inactive: bool = False):
    try:
        return CatalogCategoriesResponse(
            categories=[
                _cat(x)
                for x in CatalogService().list_categories(scope, include_inactive)
            ]
        )
    except DomainValidationError as exc:
        _err(exc)


@router.get("/categories/{category_id}", response_model=CatalogCategoryResponse)
def get_category(category_id: int):
    try:
        return _cat(CatalogService().get_category(category_id))
    except CatalogCategoryNotFoundError as exc:
        raise HTTPException(404, "Category was not found.") from exc


@router.put("/categories/{category_id}", response_model=CatalogCategoryResponse)
def update_category(category_id: int, p: CatalogCategoryUpdateRequest):
    try:
        return _cat(
            CatalogService().update_category(
                category_id, CatalogCategoryDraft.create(**p.model_dump())
            )
        )
    except DomainValidationError as exc:
        _err(exc)
    except CatalogCategoryNotFoundError as exc:
        raise HTTPException(404, "Category was not found.") from exc
    except CatalogDuplicateSlugError as exc:
        raise HTTPException(409, "Category slug already exists in this scope.") from exc


@router.post(
    "/categories/{category_id}/archive", response_model=CatalogCategoryResponse
)
def archive_category(category_id: int):
    try:
        return _cat(CatalogService().archive_category(category_id))
    except CatalogCategoryNotFoundError as exc:
        raise HTTPException(404, "Category was not found.") from exc


@router.post("/tags", response_model=CatalogTagResponse, status_code=201)
def create_tag(p: CatalogTagCreateRequest):
    try:
        return _tag(
            CatalogService().create_tag(CatalogTagDraft.create(**p.model_dump()))
        )
    except DomainValidationError as exc:
        _err(exc)
    except CatalogTagNotFoundError as exc:
        raise HTTPException(404, "Tag was not found.") from exc
    except CatalogDuplicateSlugError as exc:
        raise HTTPException(409, "Tag slug already exists in this scope.") from exc


@router.get("/tags", response_model=CatalogTagsResponse)
def list_tags(scope: str, include_inactive: bool = False):
    try:
        return CatalogTagsResponse(
            tags=[_tag(x) for x in CatalogService().list_tags(scope, include_inactive)]
        )
    except DomainValidationError as exc:
        _err(exc)


@router.get("/tags/{tag_id}", response_model=CatalogTagResponse)
def get_tag(tag_id: int):
    try:
        return _tag(CatalogService().get_tag(tag_id))
    except CatalogTagNotFoundError as exc:
        raise HTTPException(404, "Tag was not found.") from exc


@router.put("/tags/{tag_id}", response_model=CatalogTagResponse)
def update_tag(tag_id: int, p: CatalogTagUpdateRequest):
    try:
        return _tag(
            CatalogService().update_tag(
                tag_id, CatalogTagDraft.create(**p.model_dump())
            )
        )
    except DomainValidationError as exc:
        _err(exc)
    except CatalogTagNotFoundError as exc:
        raise HTTPException(404, "Tag was not found.") from exc
    except CatalogDuplicateSlugError as exc:
        raise HTTPException(409, "Tag slug already exists in this scope.") from exc


@router.post("/tags/{tag_id}/archive", response_model=CatalogTagResponse)
def archive_tag(tag_id: int):
    try:
        return _tag(CatalogService().archive_tag(tag_id))
    except CatalogTagNotFoundError as exc:
        raise HTTPException(404, "Tag was not found.") from exc
