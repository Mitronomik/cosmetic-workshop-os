"""The backend-owned safe presentation of one persisted AuditLog row.

Durable contract: ``docs/audit-log.md`` § 5.4, § 6 and § 11.

This module is the single place that decides what a non-technical workshop user
is allowed to read about an audited action. It is deliberately pure: it opens no
connection, reads no repository, imports neither FastAPI nor Pydantic, performs
no metadata parsing, joins no business table and writes nothing. Everything it
returns is derived from the persisted ``action`` code plus — under the bounded
rule of :func:`display_summary` — a suffix of the persisted ``summary``.

Why the persisted summary cannot simply be returned: it is write-time technical
text. Most values are English, several embed internal record IDs
(``Ingredient lot created for ingredient #12``), and ``client_wish.*`` values
embed user-authored wish text. So the raw summary is never returned verbatim and
is never an unrestricted fallback; only an allowlisted suffix may contribute.

Nothing here modifies a persisted row. AuditLog stays append-only — this module
changes only what is *shown*, never what is *stored*.
"""

from typing import Final

UNKNOWN_ACTION_LABEL: Final = "Другое действие"
UNKNOWN_ENTITY_LABEL: Final = "Другая сущность"
UNKNOWN_ACTOR_LABEL: Final = "Другой инициатор"

# `docs/audit-log.md` § 11.1 — the 50 action codes the merged-`main` production
# write call sites can produce. Read from the code, not from a database, so an
# older local database may hold values absent here; those degrade to the safe
# unknown label rather than leaking a technical identifier.
ACTION_LABELS: Final[dict[str, str]] = {
    "catalog_category.created": "Категория справочника создана",
    "catalog_category.updated": "Категория справочника изменена",
    "catalog_category.archived": "Категория справочника архивирована",
    "catalog_tag.created": "Тег справочника создан",
    "catalog_tag.updated": "Тег справочника изменён",
    "catalog_tag.archived": "Тег справочника архивирован",
    "ingredient.catalog_category.assigned": "Компоненту назначена категория",
    "ingredient.catalog_tags.updated": "У компонента изменены теги",
    "packaging_item.catalog_category.assigned": "Таре назначена категория",
    "packaging_item.catalog_tags.updated": "У тары изменены теги",
    "recipe_template.catalog_category.assigned": "Рецепту назначена категория",
    "recipe_template.catalog_tags.updated": "У рецепта изменены теги",
    "client.created": "Клиент создан",
    "client.updated": "Клиент изменён",
    "client.deactivated": "Клиент архивирован",
    "client_recipe.created": "Индивидуальный рецепт создан",
    "client_recipe.composition_updated": "Состав индивидуального рецепта изменён",
    "client_recipe.deactivated": "Индивидуальный рецепт архивирован",
    "client_recipe.restored": "Индивидуальный рецепт восстановлен",
    "client_wish.created": "Пожелание клиента добавлено",
    "client_wish.status_changed": "Статус пожелания изменён",
    "client_wish.archived": "Пожелание клиента архивировано",
    "client_feedback.created": "Добавлена обратная связь клиента",
    "demo_data.installed": "Демонстрационные данные установлены",
    "demo_data.cleared": "Демонстрационные данные удалены",
    "import_draft_applied": "Импорт применён",
    "ingredient.created": "Компонент создан",
    "ingredient.updated": "Компонент изменён",
    "ingredient.deactivated": "Компонент архивирован",
    "ingredient_lot.created": "Партия компонента создана",
    "ingredient_lot.updated": "Партия компонента изменена",
    "ingredient_lot.deactivated": "Партия компонента архивирована",
    "onboarding.started": "Первичная настройка начата",
    "onboarding.step_completed": "Шаг первичной настройки выполнен",
    "onboarding.skipped": "Первичная настройка отложена",
    "onboarding.completed": "Первичная настройка завершена",
    "order.created": "Заказ создан",
    "order.updated": "Заказ изменён",
    "order.cancelled": "Заказ отменён",
    "order.archived": "Заказ архивирован",
    "packaging_item.created": "Тара создана",
    "packaging_item.updated": "Тара изменена",
    "packaging_item.deactivated": "Тара архивирована",
    "packaging_stock_movement.created": "Движение тары добавлено",
    "production_confirmed": "Производство подтверждено",
    "recipe_template.created": "Рецепт создан",
    "recipe_template.deactivated": "Рецепт архивирован",
    "recipe_version.created": "Версия рецепта создана",
    "stock_movement.created": "Движение сырья добавлено",
    "tax_rate_setting_changed": "Налоговая ставка изменена",
}

# `docs/audit-log.md` § 11.2 — 19 entity codes. `ImportDraft` is PascalCase while
# every other value is snake_case. That inconsistency is persisted history and is
# matched exactly as stored: it is never normalized, aliased or rewritten.
ENTITY_LABELS: Final[dict[str, str]] = {
    "app_setting": "Настройка",
    "catalog_category": "Категория справочника",
    "catalog_tag": "Тег справочника",
    "client": "Клиент",
    "client_feedback": "Обратная связь клиента",
    "client_recipe": "Индивидуальный рецепт",
    "client_wish": "Пожелание клиента",
    "demo_data_session": "Демонстрационные данные",
    "ImportDraft": "Черновик импорта",
    "ingredient": "Компонент",
    "ingredient_lot": "Партия компонента",
    "onboarding": "Первичная настройка",
    "order": "Заказ",
    "packaging_item": "Тара",
    "packaging_stock_movement": "Движение тары",
    "production_batch": "Производственная партия",
    "recipe_template": "Рецепт",
    "recipe_version": "Версия рецепта",
    "stock_movement": "Движение сырья",
}

# `docs/audit-log.md` § 3.5 and § 11.3. These are actor identities — who or what
# initiated the action — and deliberately *not* a process/source vocabulary. No
# write call site persists a process dimension, so no `source` field exists.
ACTOR_LABELS: Final[dict[str, str]] = {
    "system": "Система",
    "user": "Пользователь",
}

# `docs/audit-log.md` § 6.6 — the whole safe Russian phrase for every known
# action. For the allowlisted actions of `SUFFIX_PREFIXES` this is also the
# fallback used whenever the bounded suffix rule does not apply.
GENERIC_SUMMARIES: Final[dict[str, str]] = {
    "catalog_category.created": "Категория справочника создана",
    "catalog_category.updated": "Категория справочника изменена",
    "catalog_category.archived": "Категория справочника архивирована",
    "catalog_tag.created": "Тег справочника создан",
    "catalog_tag.updated": "Тег справочника изменён",
    "catalog_tag.archived": "Тег справочника архивирован",
    "ingredient.catalog_category.assigned": "Компоненту назначена категория",
    "ingredient.catalog_tags.updated": "У компонента изменены теги",
    "packaging_item.catalog_category.assigned": "Таре назначена категория",
    "packaging_item.catalog_tags.updated": "У тары изменены теги",
    "recipe_template.catalog_category.assigned": "Рецепту назначена категория",
    "recipe_template.catalog_tags.updated": "У рецепта изменены теги",
    "client.created": "Клиент создан",
    "client.updated": "Клиент изменён",
    "client.deactivated": "Клиент архивирован",
    "client_recipe.created": "Создан индивидуальный рецепт",
    "client_recipe.composition_updated": "Изменён состав индивидуального рецепта",
    "client_recipe.deactivated": "Индивидуальный рецепт архивирован",
    "client_recipe.restored": "Индивидуальный рецепт восстановлен",
    "client_wish.created": "Пожелание клиента добавлено",
    "client_wish.status_changed": "Статус пожелания клиента изменён",
    "client_wish.archived": "Пожелание клиента архивировано",
    "client_feedback.created": "Добавлена обратная связь клиента",
    "demo_data.installed": "Установлены демонстрационные данные",
    "demo_data.cleared": "Демонстрационные данные удалены",
    "import_draft_applied": "Импорт применён",
    "ingredient.created": "Компонент создан",
    "ingredient.updated": "Компонент изменён",
    "ingredient.deactivated": "Компонент архивирован",
    "ingredient_lot.created": "Создана партия компонента",
    "ingredient_lot.updated": "Изменена партия компонента",
    "ingredient_lot.deactivated": "Партия компонента архивирована",
    "onboarding.started": "Начата первичная настройка",
    "onboarding.step_completed": "Выполнен шаг первичной настройки",
    "onboarding.skipped": "Первичная настройка отложена",
    "onboarding.completed": "Первичная настройка завершена",
    "order.created": "Заказ создан",
    "order.updated": "Заказ изменён",
    "order.cancelled": "Заказ отменён",
    "order.archived": "Заказ архивирован",
    "packaging_item.created": "Тара создана",
    "packaging_item.updated": "Тара изменена",
    "packaging_item.deactivated": "Тара архивирована",
    "packaging_stock_movement.created": "Добавлено движение тары",
    "production_confirmed": "Производство заказа подтверждено",
    "recipe_template.created": "Рецепт создан",
    "recipe_template.deactivated": "Рецепт архивирован",
    "recipe_version.created": "Создана версия рецепта",
    "stock_movement.created": "Добавлено движение сырья",
    "tax_rate_setting_changed": "Изменена налоговая ставка для расчётов",
}

# `docs/audit-log.md` § 6.4.3 — the exhaustive 21-action allowlist. An action
# absent from this mapping can never retain a suffix, no matter what its
# persisted summary looks like.
#
# This is an exact table, **not** a prefix glob: `client.created` is allowlisted
# while `client_wish.created` and `client_recipe.created` are not, and no
# catalog-*assignment* action appears here because its persisted summary is a
# fixed string with no name to retain.
#
# Every prefix ends with a space after the colon; the retained suffix is
# everything after it.
SUFFIX_PREFIXES: Final[dict[str, str]] = {
    "client.created": "Client created: ",
    "client.updated": "Client updated: ",
    "client.deactivated": "Client deactivated: ",
    "ingredient.created": "Ingredient created: ",
    "ingredient.updated": "Ingredient updated: ",
    "ingredient.deactivated": "Ingredient deactivated: ",
    "packaging_item.created": "Packaging item created: ",
    "packaging_item.updated": "Packaging item updated: ",
    "packaging_item.deactivated": "Packaging item deactivated: ",
    "recipe_template.created": "Recipe template created: ",
    "recipe_template.deactivated": "Recipe template deactivated: ",
    "order.created": "Order created: ",
    "order.updated": "Order updated: ",
    "order.cancelled": "Order cancelled: ",
    "order.archived": "Order archived: ",
    "catalog_category.created": "Catalog category created: ",
    "catalog_category.updated": "Catalog category updated: ",
    "catalog_category.archived": "Catalog category archived: ",
    "catalog_tag.created": "Catalog tag created: ",
    "catalog_tag.updated": "Catalog tag updated: ",
    "catalog_tag.archived": "Catalog tag archived: ",
}


def action_label(action: object) -> str:
    """The Russian label for a persisted action code, or the safe fallback."""
    return ACTION_LABELS.get(action, UNKNOWN_ACTION_LABEL) if isinstance(action, str) else UNKNOWN_ACTION_LABEL


def entity_label(entity_type: object) -> str:
    """The Russian label for a persisted entity code.

    The column is nullable, so `None` is ordinary rather than exceptional and
    resolves to the same safe unknown-entity label as an unrecognized code.
    """
    return ENTITY_LABELS.get(entity_type, UNKNOWN_ENTITY_LABEL) if isinstance(entity_type, str) else UNKNOWN_ENTITY_LABEL


def actor_label(actor_type: object) -> str:
    """The Russian label for a persisted actor code, or the safe fallback."""
    return ACTOR_LABELS.get(actor_type, UNKNOWN_ACTOR_LABEL) if isinstance(actor_type, str) else UNKNOWN_ACTOR_LABEL


def display_summary(action: object, summary: object) -> str:
    """The safe Russian `display_summary` for one persisted row.

    Resolved from `action` first. A suffix of the persisted `summary` is appended
    only when every one of the seven conditions in `docs/audit-log.md` § 6.4.1
    holds — the action is allowlisted here, the summary starts with that action's
    exact prefix, and the remainder is non-blank. Conditions 4 to 7 are satisfied
    structurally: `SUFFIX_PREFIXES` contains only actions authorized to retain an
    ordinary business name, the suffix is returned as plain text, no identifier
    is added by this function, and no lookup of any kind is performed.

    There is no partial credit and no repair attempt. A prefix mismatch, a blank
    remainder, an unknown action or a non-allowlisted action all fall back to the
    generic action-specific phrase, so a malformed historical row degrades to
    safe text instead of leaking its raw contents.
    """
    generic = GENERIC_SUMMARIES.get(action, UNKNOWN_ACTION_LABEL) if isinstance(action, str) else UNKNOWN_ACTION_LABEL
    prefix = SUFFIX_PREFIXES.get(action) if isinstance(action, str) else None
    if prefix is None or not isinstance(summary, str) or not summary.startswith(prefix):
        return generic
    retained = summary[len(prefix):].strip()
    return f"{generic}: {retained}" if retained else generic


__all__ = [
    "ACTION_LABELS",
    "ACTOR_LABELS",
    "ENTITY_LABELS",
    "GENERIC_SUMMARIES",
    "SUFFIX_PREFIXES",
    "UNKNOWN_ACTION_LABEL",
    "UNKNOWN_ACTOR_LABEL",
    "UNKNOWN_ENTITY_LABEL",
    "action_label",
    "actor_label",
    "display_summary",
    "entity_label",
]
