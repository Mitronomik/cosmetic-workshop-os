from collections.abc import Callable

from fastapi import APIRouter, HTTPException, status
from app.domain.errors import DomainValidationError
from app.repositories.catalog import (
    CatalogCategoryNotFoundError,
    CatalogTagNotFoundError,
)
from app.repositories.ingredients import IngredientNotFoundError
from app.repositories.packaging_items import PackagingItemNotFoundError
from app.repositories.recipes import RecipeTemplateNotFoundError
from app.schemas.catalog import (
    CatalogCategoryAssignmentRequest,
    CatalogCategoryAssignmentResponse,
    CatalogTagsAssignmentRequest,
    CatalogTagsAssignmentResponse,
)
from app.services.catalog import CatalogService

router = APIRouter(tags=["catalog-assignments"])


_ENTITY_TYPES = {
    "ingredient": "ingredient",
    "packaging": "packaging_item",
    "recipe": "recipe_template",
}


def _wrap(fn: Callable[[], object]):
    try:
        return fn()
    except DomainValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__
        ) from exc
    except (CatalogCategoryNotFoundError, CatalogTagNotFoundError) as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Catalog record was not found."
        ) from exc
    except (
        IngredientNotFoundError,
        PackagingItemNotFoundError,
        RecipeTemplateNotFoundError,
    ) as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Assignment target was not found."
        ) from exc


def _assign_category_response(
    *, kind: str, entity_id: int, catalog_category_id: int | None
) -> CatalogCategoryAssignmentResponse:
    CatalogService().assign_category(kind, entity_id, catalog_category_id)
    return CatalogCategoryAssignmentResponse(
        entity_type=_ENTITY_TYPES[kind],
        entity_id=entity_id,
        catalog_category_id=catalog_category_id,
    )


def _assign_tags_response(
    *, kind: str, entity_id: int, tag_ids: list[int]
) -> CatalogTagsAssignmentResponse:
    CatalogService().replace_tags(kind, entity_id, tag_ids)
    return CatalogTagsAssignmentResponse(
        entity_type=_ENTITY_TYPES[kind],
        entity_id=entity_id,
        tag_ids=sorted(set(tag_ids)),
    )


@router.put(
    "/ingredients/{ingredient_id}/catalog-category",
    response_model=CatalogCategoryAssignmentResponse,
)
def ingredient_category(ingredient_id: int, p: CatalogCategoryAssignmentRequest):
    return _wrap(
        lambda: _assign_category_response(
            kind="ingredient",
            entity_id=ingredient_id,
            catalog_category_id=p.catalog_category_id,
        )
    )


@router.put(
    "/ingredients/{ingredient_id}/catalog-tags",
    response_model=CatalogTagsAssignmentResponse,
)
def ingredient_tags(ingredient_id: int, p: CatalogTagsAssignmentRequest):
    return _wrap(
        lambda: _assign_tags_response(
            kind="ingredient", entity_id=ingredient_id, tag_ids=p.tag_ids
        )
    )


@router.put(
    "/packaging-items/{packaging_item_id}/catalog-category",
    response_model=CatalogCategoryAssignmentResponse,
)
def packaging_category(packaging_item_id: int, p: CatalogCategoryAssignmentRequest):
    return _wrap(
        lambda: _assign_category_response(
            kind="packaging",
            entity_id=packaging_item_id,
            catalog_category_id=p.catalog_category_id,
        )
    )


@router.put(
    "/packaging-items/{packaging_item_id}/catalog-tags",
    response_model=CatalogTagsAssignmentResponse,
)
def packaging_tags(packaging_item_id: int, p: CatalogTagsAssignmentRequest):
    return _wrap(
        lambda: _assign_tags_response(
            kind="packaging", entity_id=packaging_item_id, tag_ids=p.tag_ids
        )
    )


@router.put(
    "/recipe-templates/{recipe_template_id}/catalog-category",
    response_model=CatalogCategoryAssignmentResponse,
)
def recipe_category(recipe_template_id: int, p: CatalogCategoryAssignmentRequest):
    return _wrap(
        lambda: _assign_category_response(
            kind="recipe",
            entity_id=recipe_template_id,
            catalog_category_id=p.catalog_category_id,
        )
    )


@router.put(
    "/recipe-templates/{recipe_template_id}/catalog-tags",
    response_model=CatalogTagsAssignmentResponse,
)
def recipe_tags(recipe_template_id: int, p: CatalogTagsAssignmentRequest):
    return _wrap(
        lambda: _assign_tags_response(
            kind="recipe", entity_id=recipe_template_id, tag_ids=p.tag_ids
        )
    )
