"""The single canonical conversion boundary for C2 tax-rate timestamps.

Durable contract: ``docs/decisions/0012-c2-financial-calculation-snapshots.md``.

Two representations exist and only two:

============================= ==========================
surface                       canonical format
============================= ==========================
SQLite persistence            ``YYYY-MM-DD HH:MM:SS``
API and confirmation context  ``YYYY-MM-DDTHH:MM:SSZ``
============================= ==========================

Both are UTC with second precision. Storage carries no ``T``, no ``Z``, and no
offset; the API form carries a literal ``T`` and a literal ``Z``. Every
conversion between them goes through this module, so no service, repository, or
route re-implements the string handling and the API can never leak the raw
stored representation.
"""

import re
from datetime import datetime
from typing import Final

STORAGE_TIMESTAMP_FORMAT: Final = "%Y-%m-%d %H:%M:%S"
API_TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"

API_TIMESTAMP_PATTERN: Final = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# The only persisted forms that may be read back. The first is the documented
# storage convention; the other two are the exact legacy shapes some existing
# local rows carry. Every one of them is unambiguously UTC at second precision.
STORAGE_TIMESTAMP_FORMATS: Final = (
    STORAGE_TIMESTAMP_FORMAT,
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
)


def parse_storage_timestamp(stored: str | None) -> datetime | None:
    """Read a persisted UTC timestamp, accepting only exact supported forms.

    Deliberately unforgiving. This value becomes an immutable production
    snapshot, so anything whose meaning is not certain must be rejected rather
    than coerced: an arbitrary offset such as `+03:00` would otherwise have its
    zone silently dropped and be reinterpreted as UTC, and fractional seconds,
    impossible calendar dates, missing seconds, and arbitrary text would be
    quietly reshaped into a value the user never stored.

    Returning `None` is the safe outcome — the caller reduces it to the
    no-valid-rate context instead of inventing an instant.
    """
    if not isinstance(stored, str):
        return None
    text = stored.strip()
    if not text:
        return None
    for candidate in STORAGE_TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(text, candidate)
        except ValueError:
            continue
    return None


def api_timestamp(stored: str | None) -> str | None:
    """Normalize persisted SQLite UTC text into the ISO-8601 UTC API form."""
    parsed = parse_storage_timestamp(stored)
    return parsed.strftime(API_TIMESTAMP_FORMAT) if parsed else None


def storage_timestamp(api_value: str | None) -> str | None:
    """Normalize a canonical API timestamp into the persisted SQLite UTC text."""
    parsed = parse_api_timestamp(api_value)
    return parsed.strftime(STORAGE_TIMESTAMP_FORMAT) if parsed else None


def parse_api_timestamp(value: object) -> datetime | None:
    """Return the instant for a strictly canonical API timestamp, else `None`.

    Unlike the storage reader this is deliberately unforgiving: it is the gate
    for client-supplied values, so an arbitrary offset, fractional seconds, a
    space separator, a missing `Z`, or an impossible calendar date all fail.
    """
    if not isinstance(value, str) or not API_TIMESTAMP_PATTERN.match(value):
        return None
    try:
        return datetime.strptime(value, API_TIMESTAMP_FORMAT)
    except ValueError:
        return None


def is_canonical_api_timestamp(value: object) -> bool:
    """Whether `value` is exactly one canonical `YYYY-MM-DDTHH:MM:SSZ` instant."""
    return parse_api_timestamp(value) is not None


def is_readable_storage_timestamp(value: object) -> bool:
    """Whether a persisted value can be read back as a certain UTC instant."""
    return parse_storage_timestamp(value if isinstance(value, str) else None) is not None


__all__ = [
    "API_TIMESTAMP_FORMAT",
    "API_TIMESTAMP_PATTERN",
    "STORAGE_TIMESTAMP_FORMAT",
    "STORAGE_TIMESTAMP_FORMATS",
    "is_readable_storage_timestamp",
    "api_timestamp",
    "is_canonical_api_timestamp",
    "parse_api_timestamp",
    "parse_storage_timestamp",
    "storage_timestamp",
]
