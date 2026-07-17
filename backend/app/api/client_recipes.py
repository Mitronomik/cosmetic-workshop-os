from dataclasses import replace

from fastapi import APIRouter, HTTPException, status

from app.domain.client_recipes import ClientRecipeDraft, ClientRecipeIngredientUpdateDraft
from app.domain.errors import DomainValidationError
from app.models.client_recipe import ClientRecipe, ClientRecipeDetail, ClientRecipeIngredient
from app.repositories.client_recipes import ClientRecipeNotFoundError
from app.repositories.clients import ClientNotFoundError
from app.repositories.ingredients import IngredientNotFoundError
from app.repositories.recipes import RecipeVersionNotFoundError
from app.schemas.client_recipes import ClientRecipeCreateRequest, ClientRecipeDetailResponse, ClientRecipeIngredientResponse, ClientRecipeIngredientUpdateRequest, ClientRecipeIngredientsUpdateRequest, ClientRecipeResponse, ClientRecipesResponse
from app.services.client_recipes import ClientInactiveError, ClientRecipeArchivedError, ClientRecipeIngredientInactiveError, ClientRecipeIngredientLineOwnershipError, ClientRecipeRestoreClientInactiveError, ClientRecipeService, SourceRecipeVersionEmptyError

router = APIRouter(tags=["client-recipes"])


@router.post("/client-recipes", response_model=ClientRecipeDetailResponse, status_code=status.HTTP_201_CREATED)
def create_client_recipe(payload: ClientRecipeCreateRequest):
    try:
        draft = ClientRecipeDraft.create(**payload.model_dump())
        return _detail(ClientRecipeService().create_from_recipe_version(draft))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client was not found.") from exc
    except RecipeVersionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source recipe version was not found.") from exc
    except IngredientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ingredient was not found.") from exc
    except (ClientInactiveError, SourceRecipeVersionEmptyError, ClientRecipeIngredientInactiveError) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/client-recipes", response_model=ClientRecipesResponse)
def list_client_recipes(include_inactive: bool = True):
    return ClientRecipesResponse(client_recipes=[_recipe(r) for r in ClientRecipeService().list_recipes(include_inactive=include_inactive)])


@router.get("/client-recipes/{client_recipe_id}", response_model=ClientRecipeDetailResponse)
def get_client_recipe(client_recipe_id: int):
    try:
        return _detail(ClientRecipeService().get_detail(client_recipe_id))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientRecipeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client recipe was not found.") from exc


@router.put("/client-recipes/{client_recipe_id}/ingredients", response_model=ClientRecipeDetailResponse)
def update_client_recipe_ingredients(client_recipe_id: int, payload: ClientRecipeIngredientsUpdateRequest):
    try:
        drafts = _ingredient_update_drafts_with_context(payload.ingredients)
        return _detail(ClientRecipeService().update_composition(client_recipe_id, drafts))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientRecipeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client recipe was not found.") from exc
    except IngredientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Ingredient was not found.") from exc
    except (ClientRecipeArchivedError, ClientRecipeIngredientInactiveError) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ClientRecipeIngredientLineOwnershipError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/clients/{client_id}/recipes", response_model=ClientRecipesResponse)
def list_client_recipes_for_client(client_id: int, include_inactive: bool = True):
    try:
        return ClientRecipesResponse(client_recipes=[_recipe(r) for r in ClientRecipeService().list_for_client(client_id, include_inactive=include_inactive)])
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client was not found.") from exc


@router.post("/client-recipes/{client_recipe_id}/deactivate", response_model=ClientRecipeResponse)
def deactivate_client_recipe(client_recipe_id: int):
    try:
        return _recipe(ClientRecipeService().deactivate(client_recipe_id))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientRecipeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client recipe was not found.") from exc


@router.post("/client-recipes/{client_recipe_id}/restore", response_model=ClientRecipeResponse)
def restore_client_recipe(client_recipe_id: int):
    try:
        return _recipe(ClientRecipeService().restore(client_recipe_id))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientRecipeNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client recipe was not found.") from exc
    except ClientRecipeRestoreClientInactiveError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc



CLIENT_RECIPE_INGREDIENT_UPDATE_FIELDS = {"id", "ingredient_id", "position", "phase", "amount_value", "amount_unit", "personalization_note", "notes"}


def _ingredient_update_drafts_with_context(items: list[ClientRecipeIngredientUpdateRequest]) -> list[ClientRecipeIngredientUpdateDraft]:
    drafts: list[ClientRecipeIngredientUpdateDraft] = []
    for index, line in enumerate(items):
        try:
            drafts.append(ClientRecipeIngredientUpdateDraft.create(**line.model_dump()))
        except DomainValidationError as exc:
            issue = exc.issue
            if issue.field in CLIENT_RECIPE_INGREDIENT_UPDATE_FIELDS:
                raise DomainValidationError(replace(issue, field=f"ingredients.{index}.{issue.field}")) from exc
            raise
    return drafts

def _recipe(recipe: ClientRecipe) -> ClientRecipeResponse:
    return ClientRecipeResponse(**{**recipe.__dict__, "target_batch_size_value": None if recipe.target_batch_size_value is None else str(recipe.target_batch_size_value)})


def _ingredient(ingredient: ClientRecipeIngredient) -> ClientRecipeIngredientResponse:
    return ClientRecipeIngredientResponse(**{**ingredient.__dict__, "amount_value": str(ingredient.amount_value)})


def _detail(detail: ClientRecipeDetail) -> ClientRecipeDetailResponse:
    return ClientRecipeDetailResponse(client_recipe=_recipe(detail.client_recipe), ingredients=[_ingredient(i) for i in detail.ingredients])
