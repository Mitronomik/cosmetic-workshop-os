import pytest

from app.services.local_artifact_filenames import (
    normalize_artifact_reason,
    normalize_artifact_reason_segment,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # Accepted CR-005 contract examples.
        ("before/update ../unsafe", "before_update_unsafe"),
        ("before-import", "before_import"),
        ("___before---import___", "before_import"),
        ("перед обновлением", "перед_обновлением"),
        ("123", "reason_123"),
        ("   ", "manual"),
        ("...///---", "manual"),
        # Default and already-canonical values.
        (None, "manual"),
        ("", "manual"),
        ("manual", "manual"),
        ("before_import", "before_import"),
        ("before_large_edit", "before_large_edit"),
        # Underscore is a separator, not an alphanumeric character.
        ("before__update", "before_update"),
        ("___", "manual"),
        ("__123__", "reason_123"),
        ("_before_", "before"),
        # Every non-alphanumeric character is a separator.
        ("before\\update", "before_update"),
        ("before.update", "before_update"),
        ("before:update", "before_update"),
        ("before\tupdate", "before_update"),
        ("before…update", "before_update"),
        ("before update", "before_update"),
        # Separator runs collapse to exactly one underscore.
        ("before -_. /update", "before_update"),
        ("  before   update  ", "before_update"),
        # Case is preserved; nothing is lowercased or transliterated.
        ("Before Update", "Before_Update"),
        ("BEFORE update", "BEFORE_update"),
        ("Перед Обновлением", "Перед_Обновлением"),
        # Unicode alphanumerics survive exactly.
        ("перед импортом 2", "перед_импортом_2"),
        ("提交 前", "提交_前"),
        # Only a fully numeric segment is disambiguated.
        ("0", "reason_0"),
        ("12 34", "12_34"),
        ("v2", "v2"),
        ("2 версия", "2_версия"),
    ],
)
def test_normalize_artifact_reason_segment_matrix(value, expected):
    assert normalize_artifact_reason_segment(value) == expected


def test_segment_never_contains_a_hyphen_or_leading_trailing_underscore():
    for value in ["before-import", "-a-b-", "--", "a - b", "before/update ../unsafe"]:
        segment = normalize_artifact_reason_segment(value)
        assert "-" not in segment
        assert not segment.startswith("_")
        assert not segment.endswith("_")
        assert "__" not in segment


def test_segment_is_never_purely_numeric_so_the_uniqueness_suffix_stays_unambiguous():
    for value in ["1", "123", " 42 ", "__7__", "0"]:
        assert not normalize_artifact_reason_segment(value).isdigit()


def test_segment_is_idempotent():
    for value in ["before/update ../unsafe", "перед обновлением", "123", "   ", "before-import"]:
        once = normalize_artifact_reason_segment(value)
        assert normalize_artifact_reason_segment(once) == once


def test_segment_does_not_truncate_long_reasons():
    value = "a" * 80
    assert normalize_artifact_reason_segment(value) == value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "manual"),
        ("", "manual"),
        ("   ", "manual"),
        ("  before-import  ", "before-import"),
        ("before/update ../unsafe", "before/update ../unsafe"),
        ("перед обновлением", "перед обновлением"),
    ],
)
def test_normalize_artifact_reason_keeps_the_human_text(value, expected):
    assert normalize_artifact_reason(value) == expected
