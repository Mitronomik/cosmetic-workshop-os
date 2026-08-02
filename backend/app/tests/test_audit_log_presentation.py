"""Label resolution and the `display_summary` presenter for `C3-I`.

Durable contract: ``docs/audit-log.md`` § 5.4, § 6 and § 11.

These tests are the privacy boundary of the AuditLog workspace: they prove that
no internal ID, English technical prefix, wish title or individual-recipe title
can leave the backend, and that a row the presenter does not recognize degrades
to safe Russian text rather than leaking its raw contents.
"""

import inspect

import pytest

from app.domain import audit_log_presentation
from app.domain.audit_log_presentation import (
    ACTION_LABELS,
    ACTOR_LABELS,
    ENTITY_LABELS,
    GENERIC_SUMMARIES,
    SUFFIX_PREFIXES,
    UNKNOWN_ACTION_LABEL,
    UNKNOWN_ACTOR_LABEL,
    UNKNOWN_ENTITY_LABEL,
    action_label,
    actor_label,
    display_summary,
    entity_label,
)

# `docs/audit-log.md` § 11.5 — one realistic persisted summary per action, as the
# merged-`main` write call sites actually build them. Several deliberately carry
# an internal record ID or user-authored text so the presenter can be proven to
# drop them.
PERSISTED_SUMMARIES = {
    "catalog_category.created": "Catalog category created: Базовые масла",
    "catalog_category.updated": "Catalog category updated: Базовые масла",
    "catalog_category.archived": "Catalog category archived: Базовые масла",
    "catalog_tag.created": "Catalog tag created: Веган",
    "catalog_tag.updated": "Catalog tag updated: Веган",
    "catalog_tag.archived": "Catalog tag archived: Веган",
    "ingredient.catalog_category.assigned": "Catalog category assigned",
    "ingredient.catalog_tags.updated": "Catalog tags updated",
    "packaging_item.catalog_category.assigned": "Catalog category assigned",
    "packaging_item.catalog_tags.updated": "Catalog tags updated",
    "recipe_template.catalog_category.assigned": "Catalog category assigned",
    "recipe_template.catalog_tags.updated": "Catalog tags updated",
    # CR-009 B3 persists this fixed English string and nothing else. There is no
    # filename, path, reason, database size or migration list in it to leak.
    "backup.created": "Backup created",
    "client.created": "Client created: Анна Иванова",
    "client.updated": "Client updated: Анна Иванова",
    "client.deactivated": "Client deactivated: Анна Иванова",
    "client_recipe.created": "Client recipe created: Крем от розацеа для Анны",
    "client_recipe.composition_updated": "Client recipe composition updated: Крем от розацеа для Анны",
    "client_recipe.deactivated": "Client recipe deactivated: Крем от розацеа для Анны",
    "client_recipe.restored": "Client recipe restored: Крем от розацеа для Анны",
    "client_wish.created": "Client wish created: Убрать компонент X",
    "client_wish.status_changed": "Client wish status changed: Убрать компонент X",
    "client_wish.archived": "Client wish archived: Убрать компонент X",
    "client_feedback.created": "Client feedback created for client #3",
    "demo_data.installed": "Демонстрационные данные установлены",
    "demo_data.cleared": "Демонстрационные данные удалены",
    # CR-009 B2 persists this fixed English string and nothing else. There is no
    # filename, path, reason, manifest or entity count in it to leak.
    "export.created": "JSON export created",
    "import_draft_applied": "Import draft 7 applied",
    "ingredient.created": "Ingredient created: Масло ши",
    "ingredient.updated": "Ingredient updated: Масло ши",
    "ingredient.deactivated": "Ingredient deactivated: Масло ши",
    "ingredient_lot.created": "Ingredient lot created for ingredient #12",
    "ingredient_lot.updated": "Ingredient lot updated for ingredient #12",
    "ingredient_lot.deactivated": "Ingredient lot deactivated for ingredient #12",
    "onboarding.started": "Первичная настройка начата",
    "onboarding.step_completed": "Шаг первичной настройки выполнен",
    "onboarding.skipped": "Первичная настройка отложена",
    "onboarding.completed": "Первичная настройка завершена",
    "order.created": "Order created: Дневной крем",
    "order.updated": "Order updated: Дневной крем",
    "order.cancelled": "Order cancelled: Дневной крем",
    "order.archived": "Order archived: Дневной крем",
    "packaging_item.created": "Packaging item created: Баночка 50 мл",
    "packaging_item.updated": "Packaging item updated: Баночка 50 мл",
    "packaging_item.deactivated": "Packaging item deactivated: Баночка 50 мл",
    "packaging_stock_movement.created": "Packaging movement created for packaging item #9",
    "production_confirmed": "Order #4 produced as batch #7",
    "recipe_template.created": "Recipe template created: Дневной крем",
    "recipe_template.deactivated": "Recipe template deactivated: Дневной крем",
    "recipe_version.created": "Recipe version created: template 3 v2",
    # CR-009 B1 persists this fixed English string and nothing else. There is no
    # filename, path, reason or document ID in it to leak.
    "report_document.created": "Report document created",
    "stock_movement.created": "Stock movement created for lot #5",
    "tax_rate_setting_changed": "Налоговая ставка изменена на 6.00%",
    "workshop_profile.updated": "Workshop profile updated",
}

# The persisted business name each allowlisted action is authorized to retain.
ALLOWLISTED_NAMES = {
    "catalog_category.created": "Базовые масла",
    "catalog_category.updated": "Базовые масла",
    "catalog_category.archived": "Базовые масла",
    "catalog_tag.created": "Веган",
    "catalog_tag.updated": "Веган",
    "catalog_tag.archived": "Веган",
    "client.created": "Анна Иванова",
    "client.updated": "Анна Иванова",
    "client.deactivated": "Анна Иванова",
    "ingredient.created": "Масло ши",
    "ingredient.updated": "Масло ши",
    "ingredient.deactivated": "Масло ши",
    "order.created": "Дневной крем",
    "order.updated": "Дневной крем",
    "order.cancelled": "Дневной крем",
    "order.archived": "Дневной крем",
    "packaging_item.created": "Баночка 50 мл",
    "packaging_item.updated": "Баночка 50 мл",
    "packaging_item.deactivated": "Баночка 50 мл",
    "recipe_template.created": "Дневной крем",
    "recipe_template.deactivated": "Дневной крем",
}

WISH_TITLE = "Убрать компонент X"
CLIENT_RECIPE_TITLE = "Крем от розацеа для Анны"

LATIN_LETTERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


# --------------------------------------------------------------------------
# The vocabulary tables themselves
# --------------------------------------------------------------------------

def test_action_vocabulary_is_the_documented_fifty_codes():
    # 51 + `report_document.created` (B1) + `export.created` (B2) +
    # `backup.created` (B3) — the complete CR-009 artifact vocabulary.
    assert len(ACTION_LABELS) == 54
    assert set(GENERIC_SUMMARIES) == set(ACTION_LABELS)
    assert set(PERSISTED_SUMMARIES) == set(ACTION_LABELS)


def test_entity_and_actor_vocabularies_match_the_contract():
    # 19 + `report_document` (B1) + `export_file` (B2) + `backup_file` (B3).
    assert len(ENTITY_LABELS) == 22
    assert ENTITY_LABELS["report_document"] == "Документ отчёта"
    assert ENTITY_LABELS["export_file"] == "Экспорт"
    assert ENTITY_LABELS["backup_file"] == "Резервная копия"
    assert ENTITY_LABELS["app_setting"] == "Настройка приложения"
    assert ACTOR_LABELS == {"system": "Система", "user": "Пользователь"}


def test_suffix_allowlist_is_exactly_the_twenty_one_documented_actions():
    assert len(SUFFIX_PREFIXES) == 21
    assert set(SUFFIX_PREFIXES) <= set(ACTION_LABELS)
    assert set(SUFFIX_PREFIXES) == set(ALLOWLISTED_NAMES)


def test_every_allowlisted_prefix_ends_with_a_colon_and_a_space():
    for action, prefix in SUFFIX_PREFIXES.items():
        assert prefix.endswith(": "), action


@pytest.mark.parametrize("action", sorted(ACTION_LABELS))
def test_every_known_action_has_a_russian_label(action):
    label = ACTION_LABELS[action]
    assert label and not LATIN_LETTERS.intersection(label)


@pytest.mark.parametrize("entity_type", sorted(ENTITY_LABELS))
def test_every_known_entity_type_has_a_russian_label(entity_type):
    label = ENTITY_LABELS[entity_type]
    assert label and not LATIN_LETTERS.intersection(label)


def test_import_draft_entity_type_is_matched_exactly_as_persisted():
    """`ImportDraft` is PascalCase persisted history and is never normalized."""
    assert entity_label("ImportDraft") == "Черновик импорта"
    assert entity_label("import_draft") == UNKNOWN_ENTITY_LABEL
    assert entity_label("importdraft") == UNKNOWN_ENTITY_LABEL


# --------------------------------------------------------------------------
# Label resolution and its fallbacks
# --------------------------------------------------------------------------

def test_known_labels_resolve():
    assert action_label("client.created") == "Клиент создан"
    assert action_label("workshop_profile.updated") == "Профиль мастерской изменён"
    assert entity_label("client") == "Клиент"
    assert entity_label("app_setting") == "Настройка приложения"
    assert actor_label("system") == "Система"
    assert actor_label("user") == "Пользователь"


def test_unknown_codes_resolve_to_the_safe_fallback_labels():
    assert action_label("future.action") == UNKNOWN_ACTION_LABEL
    assert entity_label("future_entity") == UNKNOWN_ENTITY_LABEL
    assert actor_label("migration") == UNKNOWN_ACTOR_LABEL


def test_null_entity_type_resolves_to_the_unknown_entity_label():
    assert entity_label(None) == UNKNOWN_ENTITY_LABEL


def test_non_string_codes_never_raise_and_stay_safe():
    for value in (None, 7, object()):
        assert action_label(value) == UNKNOWN_ACTION_LABEL
        assert actor_label(value) == UNKNOWN_ACTOR_LABEL


# --------------------------------------------------------------------------
# `display_summary`
# --------------------------------------------------------------------------

@pytest.mark.parametrize("action", sorted(ACTION_LABELS))
def test_every_known_action_produces_safe_russian_display_summary(action):
    """No English technical prefix survives for any action in the vocabulary."""
    value = display_summary(action, PERSISTED_SUMMARIES[action])
    assert value
    for prefix in SUFFIX_PREFIXES.values():
        assert prefix not in value
    assert "#" not in value
    latin = LATIN_LETTERS.intersection(value)
    assert not latin, f"{action} leaked Latin text {sorted(latin)}"


@pytest.mark.parametrize("action", sorted(ACTION_LABELS))
def test_display_summary_is_derived_from_the_action_not_copied_from_the_summary(action):
    """A poisoned persisted summary changes nothing outside the allowlist.

    The only text a persisted summary may ever contribute is an allowlisted
    business name, so replacing the stored text with something sensitive must
    leave every non-allowlisted action's output byte-identical.
    """
    poisoned = display_summary(action, "Секретная заметка клиента об аллергии #99")
    if action in SUFFIX_PREFIXES:
        assert poisoned == GENERIC_SUMMARIES[action]
    else:
        assert poisoned == display_summary(action, PERSISTED_SUMMARIES[action])


@pytest.mark.parametrize("action", sorted(SUFFIX_PREFIXES))
def test_each_allowlisted_prefix_retains_its_business_name(action):
    value = display_summary(action, PERSISTED_SUMMARIES[action])
    assert value == f"{GENERIC_SUMMARIES[action]}: {ALLOWLISTED_NAMES[action]}"


@pytest.mark.parametrize("action", sorted(SUFFIX_PREFIXES))
def test_prefix_mismatch_falls_back_to_the_generic_phrase(action):
    for summary in ("Unexpected shape: Анна Иванова", SUFFIX_PREFIXES[action].strip(), ""):
        assert display_summary(action, summary) == GENERIC_SUMMARIES[action]


@pytest.mark.parametrize("action", sorted(SUFFIX_PREFIXES))
def test_empty_suffix_falls_back_to_the_generic_phrase(action):
    prefix = SUFFIX_PREFIXES[action]
    assert display_summary(action, prefix) == GENERIC_SUMMARIES[action]
    assert display_summary(action, f"{prefix}   ") == GENERIC_SUMMARIES[action]


@pytest.mark.parametrize(
    "action",
    sorted(set(ACTION_LABELS) - set(SUFFIX_PREFIXES)),
)
def test_actions_absent_from_the_allowlist_can_never_retain_a_suffix(action):
    """A non-allowlisted action stays generic even when its summary looks retainable."""
    assert display_summary(action, PERSISTED_SUMMARIES[action]) == GENERIC_SUMMARIES[action]
    assert display_summary(action, "Client created: Анна Иванова") == GENERIC_SUMMARIES[action]


@pytest.mark.parametrize(
    "action",
    [
        "ingredient.catalog_category.assigned",
        "ingredient.catalog_tags.updated",
        "packaging_item.catalog_category.assigned",
        "packaging_item.catalog_tags.updated",
        "recipe_template.catalog_category.assigned",
        "recipe_template.catalog_tags.updated",
    ],
)
def test_catalog_assignment_actions_are_not_reachable_through_a_prefix_glob(action):
    """They share a dotted namespace with allowlisted groups but are excluded."""
    assert action not in SUFFIX_PREFIXES
    assert display_summary(action, "Catalog category assigned") == GENERIC_SUMMARIES[action]


@pytest.mark.parametrize("action", ["client_wish.created", "client_wish.status_changed", "client_wish.archived"])
def test_client_wish_never_exposes_the_user_authored_wish_title(action):
    assert WISH_TITLE not in display_summary(action, PERSISTED_SUMMARIES[action])


@pytest.mark.parametrize(
    "action",
    ["client_recipe.created", "client_recipe.composition_updated", "client_recipe.deactivated", "client_recipe.restored"],
)
def test_client_recipe_never_exposes_the_individual_formula_title(action):
    assert CLIENT_RECIPE_TITLE not in display_summary(action, PERSISTED_SUMMARIES[action])


@pytest.mark.parametrize(
    "action",
    [
        "ingredient_lot.created",
        "ingredient_lot.updated",
        "ingredient_lot.deactivated",
        "stock_movement.created",
        "packaging_stock_movement.created",
        "production_confirmed",
        "recipe_version.created",
    ],
)
def test_id_bearing_summaries_never_expose_the_internal_id(action):
    value = display_summary(action, PERSISTED_SUMMARIES[action])
    assert "#" not in value
    assert not any(character.isdigit() for character in value)


def test_the_three_required_contract_examples():
    """`docs/audit-log.md` § 6.5 — these exact transformations are the contract."""
    assert display_summary("ingredient_lot.created", "Ingredient lot created for ingredient #12") == "Создана партия компонента"
    assert display_summary("production_confirmed", "Order #4 produced as batch #7") == "Производство заказа подтверждено"
    assert display_summary("client_wish.created", "Client wish created: Убрать компонент X") == "Пожелание клиента добавлено"
    assert display_summary("workshop_profile.updated", "Workshop profile updated") == "Профиль мастерской обновлён"
    assert "workshop_profile.updated" not in SUFFIX_PREFIXES


def test_unknown_action_falls_back_to_the_unknown_action_label():
    assert display_summary("future.action", "Anything at all: secret") == UNKNOWN_ACTION_LABEL
    assert display_summary("future.action", "Client created: Анна Иванова") == UNKNOWN_ACTION_LABEL


def test_malformed_persisted_summaries_are_not_repaired():
    """No trimming, casing fix or partial credit — only the exact prefix counts."""
    assert display_summary("client.created", "client created: Анна") == "Клиент создан"
    assert display_summary("client.created", "Client created:Анна") == "Клиент создан"
    assert display_summary("client.created", " Client created: Анна") == "Клиент создан"
    assert display_summary("client.created", None) == "Клиент создан"


def test_presenter_imports_no_database_framework_or_repository():
    """Structural proof of § 6.2: the presenter is pure by construction."""
    imports = [
        line.strip()
        for line in inspect.getsource(audit_log_presentation).splitlines()
        if line.startswith(("import ", "from "))
    ]
    assert imports == ["from typing import Final"]


def test_presenter_reads_only_its_two_arguments_and_is_deterministic():
    """No metadata lookup and no business-table lookup is even reachable."""
    assert list(inspect.signature(display_summary).parameters) == ["action", "summary"]
    first = display_summary("client.created", "Client created: Анна")
    assert first == display_summary("client.created", "Client created: Анна")
