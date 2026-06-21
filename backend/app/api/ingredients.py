from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.domain.ingredients import IngredientDraft
from app.models.ingredient import Ingredient
from app.repositories.ingredients import IngredientNotFoundError
from app.schemas.ingredients import (
    IngredientCreateRequest,
    IngredientResponse,
    IngredientsResponse,
    IngredientUpdateRequest,
)
from app.services.ingredients import IngredientService

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.post("", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
def create_ingredient(payload: IngredientCreateRequest) -> IngredientResponse:
    try:
        draft = _draft_from_payload(payload)
        ingredient = IngredientService().create_ingredient(draft)
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    return _ingredient_response(ingredient)


@router.get("", response_model=IngredientsResponse)
def list_active_ingredients() -> IngredientsResponse:
    ingredients = IngredientService().list_active_ingredients()
    return IngredientsResponse(ingredients=[_ingredient_response(ingredient) for ingredient in ingredients])


@router.get("/{ingredient_id}", response_model=IngredientResponse)
def get_ingredient(ingredient_id: int) -> IngredientResponse:
    try:
        ingredient = IngredientService().get_ingredient(ingredient_id)
    except IngredientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient was not found.") from exc
    return _ingredient_response(ingredient)


@router.patch("/{ingredient_id}", response_model=IngredientResponse)
def update_ingredient(ingredient_id: int, payload: IngredientUpdateRequest) -> IngredientResponse:
    try:
        ingredient = IngredientService().update_ingredient(ingredient_id, _draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except IngredientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient was not found.") from exc
    return _ingredient_response(ingredient)


@router.post("/{ingredient_id}/deactivate", response_model=IngredientResponse)
def deactivate_ingredient(ingredient_id: int) -> IngredientResponse:
    try:
        ingredient = IngredientService().deactivate_ingredient(ingredient_id)
    except IngredientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient was not found.") from exc
    return _ingredient_response(ingredient)


def _draft_from_payload(payload: IngredientCreateRequest) -> IngredientDraft:
    return IngredientDraft.create(
        name=payload.name,
        category=payload.category,
        default_unit=payload.default_unit,
        density_g_per_ml=payload.density_g_per_ml,
        notes=payload.notes,
        inci_name=payload.inci_name,
        supplier_hint=payload.supplier_hint,
        allergen_note=payload.allergen_note,
        usage_note=payload.usage_note,
    )


def _ingredient_response(ingredient: Ingredient) -> IngredientResponse:
    return IngredientResponse(
        id=ingredient.id,
        name=ingredient.name,
        category=ingredient.category,
        default_unit=ingredient.default_unit,
        density_g_per_ml=None if ingredient.density_g_per_ml is None else str(ingredient.density_g_per_ml),
        is_active=ingredient.is_active,
        notes=ingredient.notes,
        inci_name=ingredient.inci_name,
        supplier_hint=ingredient.supplier_hint,
        allergen_note=ingredient.allergen_note,
        usage_note=ingredient.usage_note,
        created_at=ingredient.created_at,
        updated_at=ingredient.updated_at,
    )
