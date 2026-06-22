from fastapi import APIRouter, HTTPException, status

from app.domain.errors import DomainValidationError
from app.domain.recipes import RecipeIngredientDraft, RecipeTemplateDraft, RecipeVersionDraft
from app.models.recipe import RecipeIngredient, RecipeTemplate, RecipeVersion, RecipeVersionDetail
from app.repositories.ingredients import IngredientNotFoundError
from app.repositories.recipes import RecipeTemplateNotFoundError, RecipeVersionNotFoundError
from app.schemas.recipes import *
from app.services.recipes import RecipeIngredientInactiveError, RecipeService, RecipeTemplateInactiveError

router = APIRouter(tags=["recipes"])

@router.post("/recipe-templates", response_model=RecipeTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(payload: RecipeTemplateCreateRequest):
    try:
        return _template(RecipeService().create_template(RecipeTemplateDraft.create(name=payload.name, product_type=payload.product_type, description=payload.description, notes=payload.notes)))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc

@router.get("/recipe-templates", response_model=RecipeTemplatesResponse)
def list_templates():
    return RecipeTemplatesResponse(recipe_templates=[_template(t) for t in RecipeService().list_templates()])

@router.get("/recipe-templates/{template_id}", response_model=RecipeTemplateResponse)
def get_template(template_id: int):
    try: return _template(RecipeService().get_template(template_id))
    except RecipeTemplateNotFoundError as exc: raise HTTPException(404, detail="Recipe template was not found.") from exc

@router.post("/recipe-templates/{template_id}/deactivate", response_model=RecipeTemplateResponse)
def deactivate_template(template_id: int):
    try: return _template(RecipeService().deactivate_template(template_id))
    except RecipeTemplateNotFoundError as exc: raise HTTPException(404, detail="Recipe template was not found.") from exc

@router.post("/recipe-templates/{template_id}/versions", response_model=RecipeVersionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_version(template_id: int, payload: RecipeVersionCreateRequest):
    try:
        draft = RecipeVersionDraft.create(status=payload.status, title=payload.title, target_batch_size_value=payload.target_batch_size_value, target_batch_size_unit=payload.target_batch_size_unit, notes=payload.notes, change_note=payload.change_note, created_from_version_id=payload.created_from_version_id, ingredients=[RecipeIngredientDraft.create(ingredient_id=i.ingredient_id, position=i.position, amount_value=i.amount_value, amount_unit=i.amount_unit, phase=i.phase, notes=i.notes) for i in payload.ingredients])
        return _detail(RecipeService().create_version(template_id, draft))
    except DomainValidationError as exc: raise HTTPException(422, detail=exc.issue.__dict__) from exc
    except RecipeTemplateNotFoundError as exc: raise HTTPException(404, detail="Recipe template was not found.") from exc
    except RecipeVersionNotFoundError as exc: raise HTTPException(404, detail="Source recipe version was not found.") from exc
    except IngredientNotFoundError as exc: raise HTTPException(404, detail="Ingredient was not found.") from exc
    except (RecipeTemplateInactiveError, RecipeIngredientInactiveError) as exc: raise HTTPException(409, detail=str(exc)) from exc

@router.get("/recipe-templates/{template_id}/versions", response_model=RecipeVersionsResponse)
def list_versions(template_id: int):
    return RecipeVersionsResponse(recipe_versions=[_version(v) for v in RecipeService().list_versions_for_template(template_id)])

@router.get("/recipe-versions/{version_id}", response_model=RecipeVersionDetailResponse)
def get_version_detail(version_id: int):
    try: return _detail(RecipeService().get_version_detail(version_id))
    except RecipeVersionNotFoundError as exc: raise HTTPException(404, detail="Recipe version was not found.") from exc

def _template(t: RecipeTemplate):
    return RecipeTemplateResponse(**t.__dict__)

def _version(v: RecipeVersion):
    return RecipeVersionResponse(**{**v.__dict__, "target_batch_size_value": None if v.target_batch_size_value is None else str(v.target_batch_size_value)})

def _ingredient(i: RecipeIngredient):
    return RecipeIngredientResponse(**{**i.__dict__, "amount_value": str(i.amount_value)})

def _detail(d: RecipeVersionDetail):
    return RecipeVersionDetailResponse(version=_version(d.version), ingredients=[_ingredient(i) for i in d.ingredients])
