"""Query validation, repository reads and filter options for `C3-I`.

Durable contract: ``docs/audit-log.md`` § 7 and § 8.

The pagination cases below are the binding examples of § 7.2.2 and exist to pin
the *ordered precedence*: because the negative check runs before the range
check, `limit=-1` must be `negative_quantity` only, and `limit=0` must be
`pagination_out_of_range` only.
"""

import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.domain.audit_log_query import DEFAULT_LIMIT, DEFAULT_OFFSET, MAX_SQLITE_OFFSET, parse_audit_log_query
from app.domain.errors import DomainIssueCode, DomainValidationError
from app.repositories.audit import AuditLogRepository
from app.services.audit_logs import AuditLogsService
from app.services.database import initialize_database

# Fixed-second history so ordering, tie-breaking and the exclusive/inclusive
# date boundaries are all deterministic rather than clock-dependent.
SEEDED_ROWS = [
    ("2026-07-01 10:00:00", "system", "client.created", "client", "7", "Client created: Анна Иванова"),
    ("2026-07-02 10:00:00", "system", "ingredient.created", "ingredient", "3", "Ingredient created: Масло ши"),
    ("2026-07-03 09:00:00", "system", "client_wish.created", "client_wish", "1", "Client wish created: Убрать компонент X"),
    ("2026-07-03 09:00:00", "user", "tax_rate_setting_changed", "app_setting", "default_tax_rate", "Налоговая ставка изменена"),
    ("2026-07-03 09:00:00", "system", "ingredient_lot.created", "ingredient_lot", "5", "Ingredient lot created for ingredient #12"),
    ("2026-07-04 10:00:00", "robot", "future.action", None, None, "Whatever the future writes"),
]


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "audit-logs.sqlite"
    initialize_database(DatabaseConfig(path=path))
    with sqlite3.connect(path) as connection:
        connection.executemany(
            "INSERT INTO audit_logs (created_at, actor_type, action, entity_type, entity_id, summary) VALUES (?, ?, ?, ?, ?, ?)",
            SEEDED_ROWS,
        )
    return DatabaseConfig(path=path)


@pytest.fixture
def empty_database(tmp_path):
    path = tmp_path / "empty-audit-logs.sqlite"
    initialize_database(DatabaseConfig(path=path))
    return DatabaseConfig(path=path)


def raises(**parameters) -> DomainValidationError:
    with pytest.raises(DomainValidationError) as caught:
        parse_audit_log_query(**parameters)
    return caught.value


def rows(config: DatabaseConfig, sql: str, parameters: tuple = ()) -> list[sqlite3.Row]:
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(sql, parameters).fetchall()


def audit_snapshot(config: DatabaseConfig) -> list[tuple]:
    return [tuple(row) for row in rows(config, "SELECT id, created_at, actor_type, action, entity_type, entity_id, summary, metadata_json FROM audit_logs ORDER BY id")]


# --------------------------------------------------------------------------
# Pagination validation — the ordered precedence of § 7.2.1
# --------------------------------------------------------------------------

def test_omitted_pagination_applies_the_documented_defaults():
    query = parse_audit_log_query()
    assert (query.limit, query.offset) == (DEFAULT_LIMIT, DEFAULT_OFFSET)
    assert (DEFAULT_LIMIT, DEFAULT_OFFSET) == (50, 0)


@pytest.mark.parametrize("value", ["true", "false", "1.5", "abc", "", "  ", "+5", "1e3", "5 5", "0x10"])
def test_wrong_representation_is_non_integer_quantity(value):
    assert raises(limit=value).issue.code is DomainIssueCode.NON_INTEGER_QUANTITY
    assert raises(offset=value).issue.code is DomainIssueCode.NON_INTEGER_QUANTITY


@pytest.mark.parametrize("value", ["-1", "-200", "-1000"])
def test_negative_integers_are_negative_quantity_and_never_out_of_range(value):
    """Step 3 precedes step 4, so a negative `limit` has exactly one code."""
    assert raises(limit=value).issue.code is DomainIssueCode.NEGATIVE_QUANTITY
    assert raises(offset=value).issue.code is DomainIssueCode.NEGATIVE_QUANTITY


@pytest.mark.parametrize("value", ["0", "201", "1000"])
def test_non_negative_limit_outside_the_range_is_pagination_out_of_range(value):
    issue = raises(limit=value).issue
    assert issue.code is DomainIssueCode.PAGINATION_OUT_OF_RANGE
    assert issue.field == "limit"
    assert issue.value == value


@pytest.mark.parametrize("value", ["1", "50", "200"])
def test_limits_inside_the_range_are_accepted(value):
    assert parse_audit_log_query(limit=value).limit == int(value)


@pytest.mark.parametrize("value", ["0", "1", "5000"])
def test_offset_has_no_upper_bound(value):
    assert parse_audit_log_query(offset=value).offset == int(value)


def test_the_offset_maximum_is_the_largest_value_sqlite_can_bind():
    assert MAX_SQLITE_OFFSET == 9_223_372_036_854_775_807
    assert parse_audit_log_query(offset=str(MAX_SQLITE_OFFSET)).offset == MAX_SQLITE_OFFSET


def test_an_offset_above_the_sqlite_maximum_is_rejected_rather_than_bound():
    issue = raises(offset=str(MAX_SQLITE_OFFSET + 1)).issue
    assert issue.code is DomainIssueCode.PAGINATION_OUT_OF_RANGE
    assert issue.field == "offset"


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("limit", "9" * 5000, DomainIssueCode.PAGINATION_OUT_OF_RANGE),
        ("limit", "-" + "9" * 5000, DomainIssueCode.NEGATIVE_QUANTITY),
        ("offset", "9" * 5000, DomainIssueCode.PAGINATION_OUT_OF_RANGE),
        ("offset", "-" + "9" * 5000, DomainIssueCode.NEGATIVE_QUANTITY),
    ],
)
def test_arbitrarily_long_pagination_input_is_classified_without_converting_it(field, value, expected):
    """A five-thousand-digit parameter is a range error, never an exception.

    Converting first and range-checking second is what would turn a hostile query
    string into an unhandled error, so the classification has to survive an input
    far larger than any integer the database could hold.
    """
    issue = raises(**{field: value}).issue
    assert issue.code is expected
    assert issue.field == field


@pytest.mark.parametrize("field", ["limit", "offset"])
def test_a_rejected_extreme_value_is_echoed_back_bounded(field):
    """The echoed value is a bounded excerpt, never the whole hostile payload."""
    issue = raises(**{field: "9" * 5000}).issue
    assert len(issue.value) <= 40
    assert len(issue.message) < 400


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("limit", "0001", 1),
        ("limit", "000200", 200),
        ("offset", "0000", 0),
        ("offset", "-0", 0),
        ("offset", "0000000000000000000000012", 12),
    ],
)
def test_leading_zeroes_and_negative_zero_normalize_without_changing_the_verdict(field, value, expected):
    assert getattr(parse_audit_log_query(**{field: value}), field) == expected


def test_negative_zero_limit_is_a_range_error_not_a_negative_quantity():
    """`-0` is zero, so it fails the `1..200` range rather than the sign check."""
    assert raises(limit="-0").issue.code is DomainIssueCode.PAGINATION_OUT_OF_RANGE
    assert raises(limit="000201").issue.code is DomainIssueCode.PAGINATION_OUT_OF_RANGE


def test_pagination_out_of_range_is_not_an_existing_reused_code():
    assert DomainIssueCode.PAGINATION_OUT_OF_RANGE.value == "pagination_out_of_range"
    assert DomainIssueCode.PAGINATION_OUT_OF_RANGE is not DomainIssueCode.PERCENTAGE_OUT_OF_RANGE


def test_invalid_pagination_carries_russian_guidance():
    issue = raises(limit="201").issue
    assert issue.message and issue.next_action
    assert "limit" not in issue.message


# --------------------------------------------------------------------------
# Date validation
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value",
    [
        "nope",
        "2026-07-01",
        "2026-07-01 00:00:00",
        "2026-07-01T00:00:00",
        "2026-07-01T00:00:00+03:00",
        "2026-07-01T00:00:00.500Z",
        "2026-02-30T00:00:00Z",
        "2026-13-01T00:00:00Z",
    ],
)
def test_malformed_timestamps_are_rejected_with_the_offending_field(value):
    for field in ("created_from", "created_before"):
        issue = raises(**{field: value}).issue
        assert issue.code is DomainIssueCode.INVALID_DATE
        assert issue.field == field
        assert issue.value == value


def test_a_valid_range_is_accepted_and_converted_to_the_storage_form():
    query = parse_audit_log_query(created_from="2026-07-01T00:00:00Z", created_before="2026-07-05T00:00:00Z")
    assert query.created_from == "2026-07-01 00:00:00"
    assert query.created_before == "2026-07-05 00:00:00"


@pytest.mark.parametrize(
    "created_from,created_before",
    [
        ("2026-07-05T00:00:00Z", "2026-07-01T00:00:00Z"),
        ("2026-07-05T00:00:00Z", "2026-07-05T00:00:00Z"),
    ],
)
def test_range_conflict_reports_the_end_date_field_exactly(created_from, created_before):
    """§ 8.2 — `field` is the real query parameter, never a synthetic `date_range`."""
    issue = raises(created_from=created_from, created_before=created_before).issue
    assert issue.code is DomainIssueCode.INVALID_DATE
    assert issue.field == "created_before"
    assert issue.value == created_before
    assert issue.message == "Конец периода должен быть позже его начала."
    assert issue.next_action == "Выберите дату окончания позже даты начала."


def test_blank_filters_mean_no_filter_rather_than_an_empty_code():
    query = parse_audit_log_query(action="", entity_type="   ", actor_type=None, created_from="")
    assert (query.action, query.entity_type, query.actor_type, query.created_from) == (None, None, None, None)


# --------------------------------------------------------------------------
# Repository reads
# --------------------------------------------------------------------------

def test_ordering_is_created_at_then_id_descending(database):
    found, total = AuditLogRepository(database).list_logs(parse_audit_log_query())
    assert total == 6
    assert [row["id"] for row in found] == [6, 5, 4, 3, 2, 1]


def test_equal_second_timestamps_are_ordered_by_descending_id(database):
    found, _ = AuditLogRepository(database).list_logs(parse_audit_log_query(created_from="2026-07-03T09:00:00Z", created_before="2026-07-03T09:00:01Z"))
    assert [row["id"] for row in found] == [5, 4, 3]


def test_total_is_counted_before_pagination(database):
    found, total = AuditLogRepository(database).list_logs(parse_audit_log_query(limit="2"))
    assert total == 6
    assert len(found) == 2


def test_explicit_limit_and_offset_page_without_duplicates(database):
    repository = AuditLogRepository(database)
    first, _ = repository.list_logs(parse_audit_log_query(limit="2", offset="0"))
    second, _ = repository.list_logs(parse_audit_log_query(limit="2", offset="2"))
    third, _ = repository.list_logs(parse_audit_log_query(limit="2", offset="4"))
    identities = [row["id"] for page in (first, second, third) for row in page]
    assert identities == [6, 5, 4, 3, 2, 1]
    assert len(set(identities)) == 6


def test_offset_past_the_end_returns_no_rows_with_the_full_total(database):
    found, total = AuditLogRepository(database).list_logs(parse_audit_log_query(offset="100"))
    assert found == []
    assert total == 6


def test_action_entity_and_actor_filters(database):
    repository = AuditLogRepository(database)
    for parameters, expected in (
        ({"action": "client.created"}, [1]),
        ({"entity_type": "client_wish"}, [3]),
        ({"actor_type": "user"}, [4]),
        ({"actor_type": "robot"}, [6]),
        ({"action": "future.action"}, [6]),
    ):
        found, total = repository.list_logs(parse_audit_log_query(**parameters))
        assert [row["id"] for row in found] == expected
        assert total == len(expected)


def test_created_from_is_inclusive_and_created_before_is_exclusive(database):
    repository = AuditLogRepository(database)
    found, _ = repository.list_logs(parse_audit_log_query(created_from="2026-07-03T09:00:00Z"))
    assert [row["id"] for row in found] == [6, 5, 4, 3]
    found, _ = repository.list_logs(parse_audit_log_query(created_before="2026-07-03T09:00:00Z"))
    assert [row["id"] for row in found] == [2, 1]


def test_filters_combine_with_logical_and(database):
    found, total = AuditLogRepository(database).list_logs(
        parse_audit_log_query(created_from="2026-07-03T00:00:00Z", created_before="2026-07-04T00:00:00Z", actor_type="system")
    )
    assert [row["id"] for row in found] == [5, 3]
    assert total == 2


def test_an_empty_database_returns_no_rows_and_no_options(empty_database):
    found, total = AuditLogRepository(empty_database).list_logs(parse_audit_log_query())
    assert (found, total) == ([], 0)
    assert AuditLogRepository(empty_database).distinct_filter_values() == {"action": [], "entity_type": [], "actor_type": []}


def test_reads_never_return_forbidden_columns(database):
    found, _ = AuditLogRepository(database).list_logs(parse_audit_log_query())
    for row in found:
        assert set(row.keys()) == {"id", "created_at", "action", "entity_type", "summary", "actor_type"}


# --------------------------------------------------------------------------
# Filter options
# --------------------------------------------------------------------------

def test_filter_options_come_from_actual_rows_only(database):
    options = AuditLogsService(database).list_audit_logs().filter_options
    assert [option.value for option in options.actions] == [
        "client.created",
        "client_wish.created",
        "future.action",
        "ingredient.created",
        "ingredient_lot.created",
        "tax_rate_setting_changed",
    ]
    assert [option.value for option in options.actor_types] == ["robot", "system", "user"]


def test_filter_options_do_not_change_when_the_result_filters_change(database):
    service = AuditLogsService(database)
    unfiltered = service.list_audit_logs().filter_options
    narrowed = service.list_audit_logs(action="client.created")
    assert narrowed.total == 1
    assert narrowed.filter_options == unfiltered


def test_unknown_persisted_codes_stay_selectable_under_a_safe_label(database):
    options = AuditLogsService(database).list_audit_logs().filter_options
    assert {"value": "future.action", "label": "Другое действие"} in [option.model_dump() for option in options.actions]
    assert {"value": "robot", "label": "Другой инициатор"} in [option.model_dump() for option in options.actor_types]


def test_null_entity_type_is_omitted_from_options_but_rendered_safely_as_an_item(database):
    """`null` is not a query code, so it cannot be offered without a sentinel."""
    response = AuditLogsService(database).list_audit_logs()
    assert None not in [option.value for option in response.filter_options.entity_types]
    unlabelled = next(item for item in response.items if item.entity_type is None)
    assert unlabelled.entity_label == "Другая сущность"


def test_filter_option_ordering_is_deterministic_by_raw_value(database):
    service = AuditLogsService(database)
    assert service.list_audit_logs().filter_options == service.list_audit_logs().filter_options
    values = [option.value for option in service.list_audit_logs().filter_options.entity_types]
    assert values == sorted(values)


# --------------------------------------------------------------------------
# Read-only guarantees
# --------------------------------------------------------------------------

def test_reads_do_not_write_an_audit_row_or_change_existing_history(database):
    before = audit_snapshot(database)
    service = AuditLogsService(database)
    service.list_audit_logs()
    service.list_audit_logs(action="client.created", limit="2", offset="1")
    service.list_audit_logs(created_from="2026-07-01T00:00:00Z", created_before="2026-07-09T00:00:00Z")
    assert audit_snapshot(database) == before
    assert len(before) == 6


def test_rejected_requests_write_nothing(database):
    before = audit_snapshot(database)
    for parameters in ({"limit": "0"}, {"limit": "abc"}, {"created_from": "nope"}):
        with pytest.raises(DomainValidationError):
            AuditLogsService(database).list_audit_logs(**parameters)
    assert audit_snapshot(database) == before


def test_reads_create_no_table_and_leave_business_tables_untouched(database):
    def tables() -> list[str]:
        return [row["name"] for row in rows(database, "SELECT name FROM sqlite_master ORDER BY name")]

    before = tables()
    AuditLogsService(database).list_audit_logs()
    assert tables() == before
