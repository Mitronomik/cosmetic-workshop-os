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


def parse_storage_timestamp(stored: str | None) -> datetime | None:
    """Read a persisted UTC timestamp, tolerating the historical `T`/`Z` forms.

    Rows written before the storage convention settled, or copied in by hand,
    may carry a `T` separator or a trailing `Z`. Reading stays lenient so an
    existing local database is never rejected; writing stays strict.
    """
    if not stored:
        return None
    text = stored.strip().replace("T", " ").removesuffix("Z")
    try:
        return datetime.strptime(text, STORAGE_TIMESTAMP_FORMAT)
    except ValueError:
        try:
            return datetime.fromisoformat(text).replace(tzinfo=None, microsecond=0)
        except ValueError:
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


__all__ = [
    "API_TIMESTAMP_FORMAT",
    "API_TIMESTAMP_PATTERN",
    "STORAGE_TIMESTAMP_FORMAT",
    "api_timestamp",
    "is_canonical_api_timestamp",
    "parse_api_timestamp",
    "parse_storage_timestamp",
    "storage_timestamp",
]
