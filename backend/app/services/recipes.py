from app.db.config import DatabaseConfig
from app.db.transactions import transaction
from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.recipes import RecipeTemplateDraft, RecipeVersionDraft, require_positive_id
from app.models.recipe import RecipeTemplate, RecipeVersion, RecipeVersionDetail
from app.repositories.audit import AuditLogRepository
from app.repositories.ingredients import IngredientNotFoundError, IngredientRepository
from app.repositories.recipes import RecipeRepository, RecipeTemplateNotFoundError, RecipeVersionNotFoundError


class RecipeTemplateInactiveError(ValueError): pass
class RecipeIngredientInactiveError(ValueError): pass


class RecipeService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config
        self.repository = RecipeRepository(config)
        self.ingredients = IngredientRepository(config)
        self.audit = AuditLogRepository(config)

    def create_template(self, draft: RecipeTemplateDraft) -> RecipeTemplate:
        with transaction(self.config) as connection:
            template = self.repository.create_template(draft, connection=connection)
            self.audit.create_log(action="recipe_template.created", entity_type="recipe_template", entity_id=str(template.id), summary=f"Recipe template created: {template.name}", connection=connection)
        return template

    def get_template(self, template_id: int) -> RecipeTemplate:
        return self.repository.get_template(template_id)

    def list_templates(self) -> list[RecipeTemplate]:
        return self.repository.list_templates()

    def deactivate_template(self, template_id: int) -> RecipeTemplate:
        with transaction(self.config) as connection:
            template = self.repository.deactivate_template(template_id, connection=connection)
            self.audit.create_log(action="recipe_template.deactivated", entity_type="recipe_template", entity_id=str(template.id), summary=f"Recipe template deactivated: {template.name}", connection=connection)
        return template

    def create_version(self, template_id: int, draft: RecipeVersionDraft) -> RecipeVersionDetail:
        template_id = require_positive_id(template_id, field="recipe_template_id", label="Шаблон рецепта")
        with transaction(self.config) as connection:
            template = self.repository.get_template(template_id, connection=connection)
            if not template.is_active:
                raise RecipeTemplateInactiveError("Recipe template is inactive.")
            if draft.created_from_version_id is not None:
                source_version = self.repository.get_version(draft.created_from_version_id, connection=connection)
                if source_version.recipe_template_id != template_id:
                    raise DomainValidationError(
                        DomainIssue(
                            code=DomainIssueCode.REQUIRED_FIELD,
                            message="Исходная версия должна относиться к этому же рецепту.",
                            field="created_from_version_id",
                            value=str(draft.created_from_version_id),
                            next_action="Выберите версию этого же рецепта или оставьте поле пустым.",
                        )
                    )
            for line in draft.ingredients:
                try:
                    ingredient = self.ingredients.get_by_id(line.ingredient_id)
                except IngredientNotFoundError:
                    raise
                if not ingredient.is_active:
                    raise RecipeIngredientInactiveError("Ingredient is inactive.")
            version_number = self.repository.next_version_number(template_id, connection=connection)
            version = self.repository.create_version(template_id, version_number, draft, connection=connection)
            for line in draft.ingredients:
                self.repository.create_ingredient_line(version.id, line, connection=connection)
            self.audit.create_log(action="recipe_version.created", entity_type="recipe_version", entity_id=str(version.id), summary=f"Recipe version created: template {template.id} v{version.version_number}", metadata={"recipe_template_id": template.id, "version_number": version.version_number}, connection=connection)
        return self.repository.get_version_detail(version.id)

    def get_version(self, version_id: int) -> RecipeVersion:
        return self.repository.get_version(version_id)

    def list_versions_for_template(self, template_id: int) -> list[RecipeVersion]:
        return self.repository.list_versions_for_template(template_id)

    def get_version_detail(self, version_id: int) -> RecipeVersionDetail:
        return self.repository.get_version_detail(version_id)


__all__ = ["RecipeService", "RecipeTemplateNotFoundError", "RecipeVersionNotFoundError", "RecipeTemplateInactiveError", "RecipeIngredientInactiveError"]
