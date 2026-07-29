"""Validation of the raw `GET /api/audit-logs` query string.

Durable contract: ``docs/audit-log.md`` § 7 and § 8.

The route hands this module the *raw* query representation rather than typed
FastAPI parameters, because typed parsing would answer a bad `limit` with
Pydantic's own validation body instead of the project's structured Russian
`DomainIssue`. Everything here is pure: no connection, no repository, no
FastAPI, no Pydantic, and no writes.

Two rules drive the whole module:

* **First match wins.** The pagination checks run in the fixed order of § 7.2.1,
  so every invalid input maps to exactly one code — `limit=-1` is only
  `negative_quantity`, and `limit=0` is only `pagination_out_of_range`.
* **Reject, never repair.** An explicitly supplied invalid value is never
  clamped, coerced, rounded or ignored. `limit=201` is an error, not a request
  for `200`.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.domain.tax_rate_timestamps import parse_api_timestamp, storage_timestamp

CREATED_FROM_FIELD: Final = "created_from"
CREATED_BEFORE_FIELD: Final = "created_before"
LIMIT_FIELD: Final = "limit"
OFFSET_FIELD: Final = "offset"

DEFAULT_LIMIT: Final = 50
MIN_LIMIT: Final = 1
MAX_LIMIT: Final = 200
DEFAULT_OFFSET: Final = 0

# An exact optionally-signed decimal integer and nothing else. `true`, `1.5`,
# `abc`, `+5`, `1e3`, an empty string and a padded ` 50 ` all fail, which is what
# routes step 2 of the ordered precedence to `non_integer_quantity`.
_INTEGER_SHAPE: Final = re.compile(r"^-?[0-9]+$")

# The longest rejected value echoed back to the user. A query parameter is
# attacker-influenced text, so `value` carries a bounded excerpt rather than an
# unbounded payload.
_MAX_ECHOED_VALUE: Final = 40


@dataclass(frozen=True)
class AuditLogQuery:
    """One validated, storage-ready AuditLog read request.

    The two timestamps are already converted to the SQLite `YYYY-MM-DD HH:MM:SS`
    comparison form, so the repository never re-implements the boundary and the
    raw stored representation never travels back out through the API.
    """

    created_from: str | None = None
    created_before: str | None = None
    action: str | None = None
    entity_type: str | None = None
    actor_type: str | None = None
    limit: int = DEFAULT_LIMIT
    offset: int = DEFAULT_OFFSET


def parse_audit_log_query(
    *,
    created_from: object = None,
    created_before: object = None,
    action: object = None,
    entity_type: object = None,
    actor_type: object = None,
    limit: object = None,
    offset: object = None,
) -> AuditLogQuery:
    """Validate the raw query parameters, or raise `DomainValidationError`.

    Parameter order of evaluation is fixed so a request with several problems
    always reports the same one: the date range first, then `limit`, then
    `offset`. Code filters are exact persisted codes and are never interpreted.
    """
    from_instant = _parse_timestamp(created_from, CREATED_FROM_FIELD)
    before_instant = _parse_timestamp(created_before, CREATED_BEFORE_FIELD)
    if from_instant is not None and before_instant is not None and before_instant <= from_instant:
        raise _issue(
            DomainIssueCode.INVALID_DATE,
            "Конец периода должен быть позже его начала.",
            CREATED_BEFORE_FIELD,
            created_before,
            "Выберите дату окончания позже даты начала.",
        )
    return AuditLogQuery(
        created_from=storage_timestamp(_text(created_from)),
        created_before=storage_timestamp(_text(created_before)),
        action=_text(action),
        entity_type=_text(entity_type),
        actor_type=_text(actor_type),
        limit=_parse_limit(limit),
        offset=_parse_offset(offset),
    )


def _parse_limit(value: object) -> int:
    """`limit` under the ordered precedence of `docs/audit-log.md` § 7.2.1."""
    parsed = _parse_integer(value, LIMIT_FIELD, DEFAULT_LIMIT, "Укажите целое число записей от 1 до 200.")
    if parsed is None:
        return DEFAULT_LIMIT
    # Reached only by a non-negative integer, because the negative check already
    # ran. That is what makes `limit=0` and `limit=201` exclusively
    # `pagination_out_of_range` and `limit=-1` exclusively `negative_quantity`.
    if parsed < MIN_LIMIT or parsed > MAX_LIMIT:
        raise _issue(
            DomainIssueCode.PAGINATION_OUT_OF_RANGE,
            f"Количество записей “{_echo(value)}” вне допустимого диапазона. Допустимо от 1 до 200.",
            LIMIT_FIELD,
            value,
            "Укажите количество записей от 1 до 200.",
        )
    return parsed


def _parse_offset(value: object) -> int:
    """`offset` — any non-negative integer; it has no upper bound of its own."""
    parsed = _parse_integer(value, OFFSET_FIELD, DEFAULT_OFFSET, "Укажите целое число, начиная с 0.")
    return DEFAULT_OFFSET if parsed is None else parsed


def _parse_integer(value: object, field: str, default: int, next_action: str) -> int | None:
    """Steps 1 to 3 of the precedence, shared by `limit` and `offset`.

    Returns `None` for an omitted value so the caller applies its own default,
    and otherwise a non-negative integer. The range check of step 4 belongs to
    the caller because only `limit` has one.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise _non_integer(value, field, next_action)
    text = value if isinstance(value, str) else str(value)
    if not _INTEGER_SHAPE.match(text):
        raise _non_integer(value, field, next_action)
    parsed = int(text)
    if parsed < 0:
        raise _issue(
            DomainIssueCode.NEGATIVE_QUANTITY,
            f"Значение “{_echo(value)}” не может быть отрицательным.",
            field,
            value,
            next_action,
        )
    return parsed


def _non_integer(value: object, field: str, next_action: str) -> DomainValidationError:
    return _issue(
        DomainIssueCode.NON_INTEGER_QUANTITY,
        f"Значение “{_echo(value)}” указано неверно. Нужно целое число.",
        field,
        value,
        next_action,
    )


def _parse_timestamp(value: object, field: str) -> datetime | None:
    """The instant for a canonical `YYYY-MM-DDTHH:MM:SSZ` value, or `None`.

    Delegates to the existing canonical boundary rather than adding a second
    timestamp policy, so an arbitrary offset, fractional seconds, a space
    separator, a missing `Z` and an impossible calendar date are all rejected
    here exactly as they are everywhere else in the project.
    """
    text = _text(value)
    if text is None:
        return None
    parsed = parse_api_timestamp(text)
    if parsed is None:
        raise _issue(
            DomainIssueCode.INVALID_DATE,
            f"Дата “{_echo(value)}” указана неверно. Нужны дата и время в формате 2026-07-29T10:00:00Z.",
            field,
            value,
            "Выберите дату и время ещё раз.",
        )
    return parsed


def _text(value: object) -> str | None:
    """A supplied non-blank filter value, or `None` when the filter is absent.

    A blank value is the "no filter selected" state of an empty select option, so
    it is treated as absent rather than as a request for rows whose code is the
    empty string — no persisted code is empty.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _echo(value: object) -> str:
    """The rejected input as bounded text — never a payload or a stack trace."""
    return str(value)[:_MAX_ECHOED_VALUE] if isinstance(value, (str, int, float, bool)) else type(value).__name__


def _issue(code: DomainIssueCode, message: str, field: str, value: object, next_action: str) -> DomainValidationError:
    return DomainValidationError(
        DomainIssue(code=code, message=message, field=field, value=_echo(value), next_action=next_action)
    )


__all__ = [
    "AuditLogQuery",
    "CREATED_BEFORE_FIELD",
    "CREATED_FROM_FIELD",
    "DEFAULT_LIMIT",
    "DEFAULT_OFFSET",
    "LIMIT_FIELD",
    "MAX_LIMIT",
    "MIN_LIMIT",
    "OFFSET_FIELD",
    "parse_audit_log_query",
]
