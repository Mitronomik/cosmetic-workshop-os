from fastapi import APIRouter, HTTPException, status
from app.domain.errors import DomainValidationError
from app.schemas.catalog import (
    AssignmentResponse,
    CatalogCategoryAssignmentRequest,
    CatalogTagsAssignmentRequest,
)
from app.services.catalog import CatalogService

router = APIRouter(tags=["catalog-assignments"])


def _wrap(fn):
    try:
        fn()
        return AssignmentResponse()
    except DomainValidationError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__
        ) from exc


@router.put(
    "/ingredients/{ingredient_id}/catalog-category", response_model=AssignmentResponse
)
def ingredient_category(ingredient_id: int, p: CatalogCategoryAssignmentRequest):
    return _wrap(
        lambda: CatalogService().assign_category(
            "ingredient", ingredient_id, p.catalog_category_id
        )
    )


@router.put(
    "/ingredients/{ingredient_id}/catalog-tags", response_model=AssignmentResponse
)
def ingredient_tags(ingredient_id: int, p: CatalogTagsAssignmentRequest):
    return _wrap(
        lambda: CatalogService().replace_tags("ingredient", ingredient_id, p.tag_ids)
    )


@router.put(
    "/packaging-items/{packaging_item_id}/catalog-category",
    response_model=AssignmentResponse,
)
def packaging_category(packaging_item_id: int, p: CatalogCategoryAssignmentRequest):
    return _wrap(
        lambda: CatalogService().assign_category(
            "packaging", packaging_item_id, p.catalog_category_id
        )
    )


@router.put(
    "/packaging-items/{packaging_item_id}/catalog-tags",
    response_model=AssignmentResponse,
)
def packaging_tags(packaging_item_id: int, p: CatalogTagsAssignmentRequest):
    return _wrap(
        lambda: CatalogService().replace_tags("packaging", packaging_item_id, p.tag_ids)
    )


@router.put(
    "/recipe-templates/{recipe_template_id}/catalog-category",
    response_model=AssignmentResponse,
)
def recipe_category(recipe_template_id: int, p: CatalogCategoryAssignmentRequest):
    return _wrap(
        lambda: CatalogService().assign_category(
            "recipe", recipe_template_id, p.catalog_category_id
        )
    )


@router.put(
    "/recipe-templates/{recipe_template_id}/catalog-tags",
    response_model=AssignmentResponse,
)
def recipe_tags(recipe_template_id: int, p: CatalogTagsAssignmentRequest):
    return _wrap(
        lambda: CatalogService().replace_tags("recipe", recipe_template_id, p.tag_ids)
    )
