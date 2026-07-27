"""Canonical filename reason segments for local backup and export artifacts.

This module owns exactly one narrow rule: how the human backup/export reason
becomes the reason segment of a newly generated backup or export filename
(CR-005). It is deliberately not applied to backup source database stems,
report-document reasons or filenames, uploaded filenames, or any other domain
value; those keep their own separate contracts.
"""

DEFAULT_ARTIFACT_REASON = "manual"
NUMERIC_ARTIFACT_REASON_PREFIX = "reason_"


def normalize_artifact_reason(value: str | None) -> str:
    """Return the human backup/export reason with the accepted default/trim rule.

    This is the reason a person typed. It keeps hyphens, spaces, punctuation and
    case, and it is what the export manifest preserves.
    """
    text = (value or DEFAULT_ARTIFACT_REASON).strip()
    return text or DEFAULT_ARTIFACT_REASON


def normalize_artifact_reason_segment(value: str | None) -> str:
    """Return the canonical filename reason segment for a new backup or export.

    Unicode alphanumeric characters are preserved exactly. Every other
    character, including the underscore, is a separator; each maximal run of
    separators collapses to a single underscore and edge separators are
    removed. An empty result becomes ``manual``. A digits-only result receives
    the ``reason_`` prefix so it can never be confused with the ``-N``
    uniqueness suffix. Case is preserved; nothing is lowercased, transliterated
    or truncated.

    Separator classification uses ``str.isalnum()`` character semantics on
    purpose. A ``\\w``-style regular expression would treat ``_`` and other
    Unicode connector punctuation as word characters and would not collapse the
    runs the accepted contract requires.
    """
    words: list[str] = []
    current: list[str] = []
    for character in normalize_artifact_reason(value):
        if character.isalnum():
            current.append(character)
            continue
        if current:
            words.append("".join(current))
            current = []
    if current:
        words.append("".join(current))

    segment = "_".join(words)
    if not segment:
        return DEFAULT_ARTIFACT_REASON
    if segment.isdigit():
        return f"{NUMERIC_ARTIFACT_REASON_PREFIX}{segment}"
    return segment
