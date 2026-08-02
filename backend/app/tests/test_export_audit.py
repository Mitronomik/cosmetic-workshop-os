"""The CR-009 B2 JSON-export ledger, verifier, finalizer and reconciliation.

The behaviour under test is the accepted artifact-primary rule applied to a
single-file artifact: the export is the authoritative result once it is written
and verified, its Journal event is secondary, and a secondary failure never
deletes the export, never reports total failure, and is never silently
forgotten.

The report-document slice (B1) proved the same rule for a two-file artifact.
These tests deliberately re-prove it for exports rather than assuming the shared
ledger carries the guarantee across, because the reservation boundary and the
verification contract are genuinely different here.
"""

from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
import threading

import pytest

from app.db.config import DatabaseConfig
from app.domain.artifact_audit_operations import ARTIFACT_KIND_JSON_EXPORT
from app.repositories.artifact_audit_operations import ArtifactAuditOperationRepository
from app.repositories.audit import AuditLogRepository
from app.services.database import initialize_database
from app.services import export_audit as audit_module
from app.services.export import (
    EXPORT_SCHEMA_VERSION,
    EXPORT_SOURCE,
    _export_filename,
    create_json_export,
    is_generated_export_filename,
    list_export_files,
    parse_export_reason,
    parse_generated_export_filename,
    reserve_export_path,
)
from app.services.local_artifact_filenames import normalize_artifact_reason_segment
from app.services.export_audit import ExportAuditService, ExportAuditTrackingUnavailableError

FROZEN = datetime(2026, 8, 1, 10, 11, 12, 131415, tzinfo=UTC)


def setup(tmp_path):
    config = DatabaseConfig(path=tmp_path / "export-audit.sqlite")
    initialize_database(config)
    export_dir = tmp_path / "exports"
    export_dir.mkdir(parents=True)
    return config, export_dir, ExportAuditService(export_dir, config)


def write_export(export_dir: Path, *, reason="manual", suffix=None, **manifest_overrides) -> Path:
    """Write a genuine export file the verifier should accept."""
    path = reserve_export_path(export_dir, FROZEN, reason) if suffix is None else export_dir / suffix
    data = {"ingredients": [{"id": 1}, {"id": 2}], "clients": []}
    manifest = {
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "created_at": "2026-08-01T10:11:12Z",
        "reason": reason,
        "source": EXPORT_SOURCE,
        "database_filename": "cosmetic_workshop.sqlite",
        "database_location_kind": "user_data",
        "tables": {name: len(rows) for name, rows in data.items()},
    }
    manifest.update(manifest_overrides)
    path.write_text(json.dumps({"manifest": manifest, "data": data}, ensure_ascii=False), encoding="utf-8")
    return path


def prepare(service, path: Path) -> str:
    return service.prepare_operation(primary_filename=path.name)


def audit_rows(config):
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT id, action, entity_type, entity_id, summary, actor_type, metadata_json FROM audit_logs ORDER BY id"
        ).fetchall()


# --------------------------------------------------------------------------
# Exact filename reservation
# --------------------------------------------------------------------------


def test_the_reserved_name_matches_the_accepted_grammar_and_canonical_reason(tmp_path):
    _config, export_dir, _service = setup(tmp_path)

    path = reserve_export_path(export_dir, FROZEN, "before-update ../unsafe")

    assert path.parent == export_dir
    assert path.name == "20260801T101112131415Z-cosmetic_workshop-export-before_update_unsafe.json"
    # The human reason stays human; only the filename carries the canonical slug.
    assert parse_export_reason(path) == "before_update_unsafe"


def test_an_existing_file_makes_an_identity_occupied(tmp_path):
    _config, export_dir, _service = setup(tmp_path)
    first = reserve_export_path(export_dir, FROZEN, "manual")
    first.write_text("{}", encoding="utf-8")

    second = reserve_export_path(export_dir, FROZEN, "manual")

    assert second != first
    assert second.name.endswith("-manual-1.json")
    assert parse_export_reason(second) == "manual"


def test_an_active_ledger_identity_makes_an_identity_occupied(tmp_path):
    """A `prepared` operation owns its name before that file exists.

    File existence alone therefore cannot decide whether a candidate is free,
    and two operations claiming one export identity would break the exactly-once
    guarantee the ledger is for.
    """
    _config, export_dir, service = setup(tmp_path)
    first = reserve_export_path(export_dir, FROZEN, "manual")
    prepare(service, first)
    assert not first.exists()

    second = reserve_export_path(export_dir, FROZEN, "manual", is_identity_active=service.is_identity_active)

    assert second.name.endswith("-manual-1.json")


def test_the_uniqueness_suffix_advances_past_every_taken_identity(tmp_path):
    _config, export_dir, service = setup(tmp_path)
    taken = reserve_export_path(export_dir, FROZEN, "manual")
    taken.write_text("{}", encoding="utf-8")
    prepare(service, export_dir / taken.name.replace(".json", "-1.json"))

    third = reserve_export_path(export_dir, FROZEN, "manual", is_identity_active=service.is_identity_active)

    assert third.name.endswith("-manual-2.json")
    assert parse_export_reason(third) == "manual"


def test_the_writer_uses_the_reserved_path_and_never_picks_another(tmp_path):
    config, export_dir, _service = setup(tmp_path)
    reserved = reserve_export_path(export_dir, FROZEN, "manual")

    result = create_json_export(config.path, export_dir, reason="manual", reserved_export_path=reserved)

    assert result.export_path == reserved
    assert sorted(item.name for item in export_dir.iterdir()) == [reserved.name]
    # The filename timestamp and the manifest timestamp describe one instant.
    manifest = json.loads(reserved.read_text(encoding="utf-8"))["manifest"]
    assert manifest["created_at"] == result.created_at.isoformat().replace("+00:00", "Z")


def test_the_writer_never_overwrites_a_reserved_path_that_is_already_taken(tmp_path):
    config, export_dir, _service = setup(tmp_path)
    reserved = reserve_export_path(export_dir, FROZEN, "manual")
    reserved.write_text("original", encoding="utf-8")

    with pytest.raises(Exception) as failure:
        create_json_export(config.path, export_dir, reason="manual", reserved_export_path=reserved)

    assert "already exists" in str(failure.value)
    assert reserved.read_text(encoding="utf-8") == "original"


@pytest.mark.parametrize(
    "name",
    ["20260801T101112131415Z-cosmetic_workshop-export-manual.txt", "not-an-export.json", "manual.json"],
)
def test_a_reserved_path_outside_the_accepted_grammar_is_refused(tmp_path, name):
    config, export_dir, _service = setup(tmp_path)

    with pytest.raises(Exception) as failure:
        create_json_export(config.path, export_dir, reason="manual", reserved_export_path=export_dir / name)

    assert "grammar" in str(failure.value)
    assert list(export_dir.iterdir()) == []


def test_a_reserved_path_outside_the_export_directory_is_refused(tmp_path):
    config, export_dir, _service = setup(tmp_path)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    stray = outside / "20260801T101112131415Z-cosmetic_workshop-export-manual.json"

    with pytest.raises(Exception) as failure:
        create_json_export(config.path, export_dir, reason="manual", reserved_export_path=stray)

    assert "export directory" in str(failure.value)
    assert not stray.exists()


def test_the_human_reason_stays_in_the_manifest_and_the_slug_stays_in_the_filename(tmp_path):
    config, export_dir, _service = setup(tmp_path)

    result = create_json_export(config.path, export_dir, reason="before-update ../unsafe")

    manifest = json.loads(result.export_path.read_text(encoding="utf-8"))["manifest"]
    assert manifest["reason"] == "before-update ../unsafe"
    assert result.reason == "before-update ../unsafe"
    assert parse_export_reason(result.export_path) == "before_update_unsafe"


def test_the_prepared_row_is_committed_and_visible_before_the_export_is_written(tmp_path):
    """A row that is only committed after the write could never recover a crash.

    The row is read back on a *separate* connection so that "committed" means
    durable rather than merely pending in the writer's own transaction.
    """
    config, export_dir, service = setup(tmp_path)
    reserved = reserve_export_path(export_dir, FROZEN, "manual")

    operation_id = prepare(service, reserved)

    assert not reserved.exists()
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM artifact_audit_operations WHERE operation_id = ?", (operation_id,)
        ).fetchone()
    assert row["status"] == "prepared"
    assert row["artifact_kind"] == "json_export"
    assert row["audit_action"] == "export.created"
    assert row["primary_filename"] == reserved.name
    # An export is one file: there is deliberately no companion.
    assert row["companion_filename"] is None
    assert row["audit_log_id"] is None


def test_an_unsafe_filename_never_reaches_the_ledger(tmp_path):
    _config, _export_dir, service = setup(tmp_path)

    for unsafe in ["../escape.json", "a/b.json", "", "with\x00nul.json"]:
        with pytest.raises(ExportAuditTrackingUnavailableError):
            service.prepare_operation(primary_filename=unsafe)

    assert service.pending_count() == 0


# --------------------------------------------------------------------------
# Exact-path verification
# --------------------------------------------------------------------------


def verify_name(service, name: str):
    repository = ArtifactAuditOperationRepository(service.config)
    operation_id = service.prepare_operation(primary_filename=name)
    return service.verify(repository.get_operation(operation_id))


def test_a_valid_export_verifies_and_is_left_byte_identical(tmp_path):
    _config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    before = path.read_bytes()

    verification = verify_name(service, path.name)

    assert verification.outcome == "valid"
    assert verification.export_schema_version == EXPORT_SCHEMA_VERSION
    assert path.read_bytes() == before


def test_a_missing_export_is_definitely_absent(tmp_path):
    _config, export_dir, service = setup(tmp_path)
    reserved = reserve_export_path(export_dir, FROZEN, "manual")

    assert verify_name(service, reserved.name).outcome == "definitely_absent"


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("{ not json", "export-unreadable"),
        ('"a string"', "payload-not-object"),
        ('{"manifest": {}}', "unexpected-top-level-keys"),
        ('{"manifest": {}, "data": {}, "extra": 1}', "unexpected-top-level-keys"),
        ('{"manifest": [], "data": {}}', "unexpected-top-level-shape"),
    ],
)
def test_a_malformed_or_wrongly_shaped_export_is_ambiguous(tmp_path, body, expected):
    _config, export_dir, service = setup(tmp_path)
    path = reserve_export_path(export_dir, FROZEN, "manual")
    path.write_text(body, encoding="utf-8")
    before = path.read_bytes()

    verification = verify_name(service, path.name)

    assert verification.outcome == "ambiguous"
    assert verification.reason == expected
    # Ambiguous is never repaired, never rewritten and never deleted.
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"export_schema_version": 99}, "unsupported-schema-version"),
        ({"export_schema_version": "1"}, "schema-version-missing"),
        ({"export_schema_version": True}, "schema-version-missing"),
        ({"source": "someone-else"}, "unexpected-source"),
        ({"tables": {"ingredients": 99, "clients": 0}}, "table-counts-mismatch"),
        ({"tables": {"ingredients": 2}}, "table-counts-mismatch"),
        ({"tables": {"ingredients": 2, "clients": 0, "ghost": 0}}, "table-counts-mismatch"),
    ],
)
def test_a_manifest_that_disagrees_with_the_contract_is_ambiguous(tmp_path, overrides, expected):
    _config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir, **overrides)

    verification = verify_name(service, path.name)

    assert verification.outcome == "ambiguous"
    assert verification.reason == expected


def test_a_non_string_manifest_reason_is_ambiguous(tmp_path):
    _config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["manifest"]["reason"] = 7
    path.write_text(json.dumps(payload), encoding="utf-8")

    verification = verify_name(service, path.name)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "manifest-reason-missing"


def test_a_human_manifest_reason_is_accepted_and_never_forced_to_equal_the_slug(tmp_path):
    """CR-005 keeps the two reason representations distinct on purpose."""
    _config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir, reason="before-update ../unsafe")

    assert parse_export_reason(path) == "before_update_unsafe"
    assert json.loads(path.read_text(encoding="utf-8"))["manifest"]["reason"] == "before-update ../unsafe"
    assert verify_name(service, path.name).outcome == "valid"


def test_a_uniqueness_suffix_is_stripped_from_the_parsed_reason_and_still_verifies(tmp_path):
    _config, export_dir, service = setup(tmp_path)
    first = write_export(export_dir, reason="before_import")
    second_name = first.name.replace(".json", "-1.json")
    write_export(export_dir, reason="before_import", suffix=second_name)

    assert parse_export_reason(Path(second_name)) == "before_import"
    assert verify_name(service, second_name).outcome == "valid"


def test_a_directory_in_place_of_the_export_is_ambiguous(tmp_path):
    _config, export_dir, service = setup(tmp_path)
    reserved = reserve_export_path(export_dir, FROZEN, "manual")
    reserved.mkdir()

    verification = verify_name(service, reserved.name)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "export-not-regular-file"
    assert reserved.is_dir()


@pytest.mark.parametrize("unsafe", ["../outside.json", "nested/export.json", ".", ".."])
def test_an_unsafe_stored_filename_is_ambiguous_on_read(tmp_path, unsafe):
    """Validated on write *and* again on read.

    A stored name is only ever as trustworthy as the moment it is used, and
    reconciliation joins it onto a real directory long after it was persisted.
    """
    _config, export_dir, service = setup(tmp_path)
    repository = ArtifactAuditOperationRepository(service.config)
    operation_id = prepare(service, write_export(export_dir))
    with sqlite3.connect(service.config.path) as connection:
        connection.execute(
            "UPDATE artifact_audit_operations SET primary_filename = ? WHERE operation_id = ?",
            (unsafe, operation_id),
        )

    verification = service.verify(repository.get_operation(operation_id))

    assert verification.outcome == "ambiguous"
    assert verification.reason == "unsafe-filename"


def test_a_symlink_leaving_the_export_directory_is_refused(tmp_path):
    _config, export_dir, service = setup(tmp_path)
    foreign = tmp_path / "foreign.json"
    write_export(tmp_path, suffix="foreign.json")
    link = reserve_export_path(export_dir, FROZEN, "manual")
    try:
        link.symlink_to(foreign)
    except (OSError, NotImplementedError):  # pragma: no cover - platform dependent
        pytest.skip("This platform does not support creating symlinks in the test environment.")

    verification = verify_name(service, link.name)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "path-outside-export-directory"
    assert foreign.exists()


@pytest.mark.parametrize("name", ["notes.json", "20260801T101112131415Z-cosmetic_workshop-backup-manual.json"])
def test_a_filename_outside_the_export_grammar_is_ambiguous(tmp_path, name):
    _config, export_dir, service = setup(tmp_path)
    write_export(export_dir, suffix=name)

    verification = verify_name(service, name)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "filename-grammar-mismatch"


# --------------------------------------------------------------------------
# Strict generated-filename grammar
#
# The boundary these cover is narrow and load-bearing: a name that merely looks
# export-shaped — right marker, right extension, a reason that happens to parse
# — is not proof this application generated it. Every malformed name below is
# written with **valid** export JSON inside, so a verifier that trusted contents
# would audit it.
# --------------------------------------------------------------------------

VALID_STEM = "20260801T101112131415Z" + "-cosmetic_workshop-export-"

MALFORMED_NAMES = [
    # malformed timestamp, correct marker, correct suffix
    ("wrong-timestamp-cosmetic_workshop-export-manual-1.json", "malformed-timestamp"),
    # missing timestamp entirely
    ("-cosmetic_workshop-export-manual.json", "missing-timestamp"),
    # truncated timestamp the generator never emits
    ("20260801T101112Z-cosmetic_workshop-export-manual.json", "timestamp-without-microseconds"),
    # human, noncanonical reason containing a hyphen
    (f"{VALID_STEM}before-update.json", "hyphen-in-reason"),
    # repeated separators the canonical form collapses
    (f"{VALID_STEM}__manual__.json", "repeated-separators"),
    (f"{VALID_STEM}before__import.json", "repeated-inner-separator"),
    # malformed uniqueness suffix
    (f"{VALID_STEM}manual-invalid.json", "non-numeric-suffix"),
    (f"{VALID_STEM}manual-1-2.json", "double-suffix"),
    (f"{VALID_STEM}manual-.json", "empty-suffix"),
    # leading zero: the generator emits `-1`, never `-01`
    (f"{VALID_STEM}manual-01.json", "leading-zero-suffix"),
    # extra trailing filename segments
    (f"{VALID_STEM}manual.json.json", "double-extension"),
    (f"{VALID_STEM}manual.backup.json", "extra-segment"),
    # digits-only reason: a canonical segment is always `reason_`-prefixed
    (f"{VALID_STEM}123.json", "digits-only-reason"),
]


@pytest.mark.parametrize(("name", "label"), MALFORMED_NAMES, ids=[label for _n, label in MALFORMED_NAMES])
def test_a_filename_the_generator_could_never_produce_is_ambiguous(tmp_path, name, label):
    """Valid contents must never rescue an invalid filename."""
    _config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir, suffix=name)
    assert json.loads(path.read_text(encoding="utf-8"))["manifest"]["source"] == EXPORT_SOURCE

    verification = verify_name(service, name)

    assert verification.outcome == "ambiguous", label
    assert verification.reason == "filename-grammar-mismatch", label
    # Never audited and never deleted.
    assert path.exists()
    assert audit_rows(service.config) == []


@pytest.mark.parametrize(("name", "label"), MALFORMED_NAMES, ids=[label for _n, label in MALFORMED_NAMES])
def test_the_writer_refuses_a_reserved_path_the_generator_could_never_produce(tmp_path, name, label):
    config, export_dir, _service = setup(tmp_path)

    with pytest.raises(Exception) as failure:
        create_json_export(config.path, export_dir, reason="manual", reserved_export_path=export_dir / name)

    assert "grammar" in str(failure.value), label
    assert list(export_dir.iterdir()) == [], label


@pytest.mark.parametrize(
    ("name", "label"),
    [
        (f"{VALID_STEM}manual.json", "ordinary"),
        (f"{VALID_STEM}manual-1.json", "numeric-suffix"),
        (f"{VALID_STEM}manual-12.json", "multi-digit-suffix"),
        (f"{VALID_STEM}reason_123.json", "reason_123"),
        (f"{VALID_STEM}перед_обновлением.json", "unicode-reason"),
        (f"{VALID_STEM}before_update_unsafe.json", "canonicalized-human-reason"),
        (f"{VALID_STEM}before_update_unsafe-2.json", "canonicalized-with-suffix"),
    ],
    ids=lambda value: value if isinstance(value, str) and not value.endswith(".json") else "",
)
def test_a_filename_the_generator_does_produce_stays_valid(tmp_path, name, label):
    _config, export_dir, service = setup(tmp_path)
    write_export(export_dir, suffix=name)

    assert verify_name(service, name).outcome == "valid", label


@pytest.mark.parametrize(
    "name",
    [
        f"{VALID_STEM}manual-01.json",
        f"{VALID_STEM}manual-invalid.json",
        f"{VALID_STEM}before-update.json",
        "wrong-timestamp-cosmetic_workshop-export-manual-1.json",
    ],
)
def test_partially_parsable_names_are_still_refused_by_the_strict_grammar(name):
    """`parse_export_reason` is lenient by design; the strict parser is not.

    The lenient parser exists for the best-effort legacy listing and will happily
    return something for all of these. Only the round trip through the one
    generator decides whether this application produced the name.
    """
    assert parse_export_reason(Path(name)) is not None
    assert parse_generated_export_filename(name) is None
    assert is_generated_export_filename(name) is False


def test_the_strict_parser_round_trips_every_name_the_generator_emits(tmp_path):
    """Whatever `reserve_export_path` chooses must satisfy the strict parser."""
    _config, export_dir, _service = setup(tmp_path)
    for reason in ["manual", "before-update ../unsafe", "перед обновлением", "123", "___", "a-b-c"]:
        for suffix in [None, 1, 2, 17]:
            name = _export_filename(FROZEN, reason, suffix)
            parsed = parse_generated_export_filename(name)
            assert parsed is not None, name
            assert parsed.suffix == suffix
            assert parsed.created_at == FROZEN
            # The parsed reason is canonical and matches what the API reports.
            assert parsed.reason == parse_export_reason(Path(name))
            assert normalize_artifact_reason_segment(parsed.reason) == parsed.reason


def test_legacy_listing_stays_best_effort_and_is_not_tightened(tmp_path):
    """Old files must not vanish from the user's history.

    CR-005 accepted best-effort legacy listing. The strict grammar governs what
    may be *reserved* and *audited*, not what may be *listed*.
    """
    _config, export_dir, _service = setup(tmp_path)
    legacy = [
        "20250101T000000Z-cosmetic_workshop-export-before-update.json",
        "cosmetic_workshop-export-manual.json",
        "manual-export.json",
        "20250101T000000000000Z-cosmetic_workshop-export-manual-01.json",
    ]
    for name in legacy:
        (export_dir / name).write_text('{"legacy": true}', encoding="utf-8")

    listed = {item.filename for item in list_export_files(export_dir)}

    assert listed == set(legacy)
    # None of them would be accepted for reservation or auditing.
    for name in legacy:
        assert is_generated_export_filename(name) is False


def test_verification_never_reads_or_compares_the_current_database(tmp_path, monkeypatch):
    """A snapshot is supposed to disagree with a database that has moved on."""
    _config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)

    def forbidden(*_args, **_kwargs):  # pragma: no cover - the assertion is that this never runs
        raise AssertionError("Verification must not read the current database.")

    monkeypatch.setattr(audit_module, "transaction", forbidden)

    assert verify_name(service, path.name).outcome == "valid"


# --------------------------------------------------------------------------
# Exactly-once finalization
# --------------------------------------------------------------------------


def test_finalization_creates_exactly_one_event_with_the_accepted_contract(tmp_path):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    operation_id = prepare(service, path)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "recorded"
    assert finalization.is_recorded is True
    assert finalization.artifact_is_authoritative is True
    assert finalization.verification.is_valid is True
    # The schema version the event carries comes from the verified artifact.
    assert finalization.verification.export_schema_version == EXPORT_SCHEMA_VERSION
    audit_log_id = finalization.audit_log_id

    rows = audit_rows(config)
    assert len(rows) == 1
    row = rows[0]
    assert audit_log_id == row["id"]
    assert row["action"] == "export.created"
    assert row["entity_type"] == "export_file"
    assert row["entity_id"] == operation_id
    assert row["actor_type"] == "user"
    assert row["summary"] == "JSON export created"
    assert json.loads(row["metadata_json"]) == {
        "operation_id": operation_id,
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "reconciled_after_failure": False,
    }
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    assert operation.status == "audited"
    assert operation.audit_log_id == audit_log_id
    assert service.pending_count() == 0


def test_the_event_leaks_no_filename_path_reason_manifest_or_entity_count(tmp_path):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir, reason="before-update ../unsafe")
    operation_id = prepare(service, path)

    service.finalize(operation_id, reconciled_after_failure=False)

    row = audit_rows(config)[0]
    serialized = f"{row['summary']}{row['metadata_json']}{row['entity_id']}{row['entity_type']}"
    for forbidden in [
        path.name,
        str(path),
        str(export_dir),
        "before_update_unsafe",
        "before-update ../unsafe",
        "cosmetic_workshop.sqlite",
        "ingredients",
        "manifest",
    ]:
        assert forbidden not in serialized
    assert set(json.loads(row["metadata_json"])) == {
        "operation_id",
        "export_schema_version",
        "reconciled_after_failure",
    }


def test_repeated_sequential_finalization_creates_exactly_one_event(tmp_path):
    config, export_dir, service = setup(tmp_path)
    operation_id = prepare(service, write_export(export_dir))

    first = service.finalize(operation_id, reconciled_after_failure=False)
    second = service.finalize(operation_id, reconciled_after_failure=True)

    assert first.outcome == second.outcome == "recorded"
    assert first.audit_log_id == second.audit_log_id
    assert len(audit_rows(config)) == 1


def test_an_already_audited_operation_returns_the_existing_audit_log_id(tmp_path):
    config, export_dir, service = setup(tmp_path)
    operation_id = prepare(service, write_export(export_dir))
    first = service.finalize(operation_id, reconciled_after_failure=False)

    again = service.finalize(operation_id, reconciled_after_failure=True)
    # The already-audited branch reuses the committed ID and reports `recorded`.
    assert again.outcome == "recorded"
    assert again.audit_log_id == first.audit_log_id
    assert audit_rows(config)[0]["id"] == first.audit_log_id


def test_startup_then_pre_create_reconciliation_creates_exactly_one_event(tmp_path):
    config, export_dir, service = setup(tmp_path)
    prepare(service, write_export(export_dir))

    service.reconcile()
    service.reconcile()

    assert len(audit_rows(config)) == 1


def test_two_concurrent_finalizers_create_exactly_one_event(tmp_path):
    """Concurrency is the case a sequential test cannot reach.

    `BEGIN IMMEDIATE` orders the two writers; the loser re-reads inside its own
    transaction, sees `audited`, and resolves the existing ID instead of
    inserting a second event.
    """
    config, export_dir, service = setup(tmp_path)
    operation_id = prepare(service, write_export(export_dir))

    barrier = threading.Barrier(2)
    results: list[int | None] = []
    lock = threading.Lock()

    def run():
        worker = ExportAuditService(export_dir, config)
        barrier.wait()
        outcome = worker.finalize(operation_id, reconciled_after_failure=False)
        with lock:
            results.append(outcome.audit_log_id if outcome.is_recorded else None)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    rows = audit_rows(config)
    assert len(rows) == 1
    assert len(results) == 2
    assert set(results) == {rows[0]["id"]}


def test_an_audit_insert_failure_leaves_the_operation_unresolved_and_the_export_intact(tmp_path, monkeypatch):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    before = path.read_bytes()
    operation_id = prepare(service, path)

    def failing_create_log(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected AuditLog failure")

    monkeypatch.setattr(AuditLogRepository, "create_log", failing_create_log)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    # The export is verified, so this is a pending Journal entry and never an
    # invalid artifact: the export itself is still authoritative.
    assert finalization.outcome == "audit_pending"
    assert finalization.artifact_is_authoritative is True
    assert finalization.audit_log_id is None

    assert audit_rows(config) == []
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    assert operation.status == "pending_audit"
    assert operation.audit_log_id is None
    assert service.pending_count() == 1
    # The primary result is untouched: never deleted, never rewritten.
    assert path.read_bytes() == before


def test_a_ledger_update_failure_rolls_back_the_audit_insert(tmp_path, monkeypatch):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    operation_id = prepare(service, path)

    monkeypatch.setattr(ArtifactAuditOperationRepository, "mark_audited", lambda *_a, **_k: False)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "audit_pending"
    assert finalization.artifact_is_authoritative is True

    # Neither half committed: the event and the transition are one transaction.
    assert audit_rows(config) == []
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == "pending_audit"
    assert path.exists()


def test_no_second_sqlite_connection_participates_in_the_finalizer(tmp_path, monkeypatch):
    config, export_dir, service = setup(tmp_path)
    operation_id = prepare(service, write_export(export_dir))

    opened: list[int] = []
    real_connect = sqlite3.connect
    inside = {"active": False}

    def counting_connect(*args, **kwargs):
        if inside["active"]:
            opened.append(1)
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", counting_connect)

    real_commit = audit_module.ExportAuditService._commit_finalization

    def traced(self, *args, **kwargs):
        inside["active"] = True
        try:
            return real_commit(self, *args, **kwargs)
        finally:
            inside["active"] = False

    monkeypatch.setattr(audit_module.ExportAuditService, "_commit_finalization", traced)

    assert service.finalize(operation_id, reconciled_after_failure=False).is_recorded
    assert sum(opened) == 1


def test_an_unexpected_verifier_defect_is_artifact_invalid_and_destroys_nothing(tmp_path, monkeypatch):
    """A verifier defect proves nothing about the export, so it cannot be trusted.

    `finalize` runs after the export exists, so it must still not raise and must
    not delete the file. But a defect that prevented verification is not evidence
    the artifact is good: reporting `audit_pending` here would let an unverified
    export reach the user as a created export with a merely pending Journal
    entry. The outcome is `artifact_invalid`, and the file, the unresolved
    operation and the pending count all survive for bounded reconciliation.
    """
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    before = path.read_bytes()
    operation_id = prepare(service, path)

    def defective(*_args, **_kwargs):
        raise TypeError("injected programming defect")

    monkeypatch.setattr(audit_module.ExportAuditService, "verify", defective)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.artifact_is_authoritative is False
    assert finalization.is_recorded is False
    assert finalization.audit_log_id is None
    assert path.exists()
    assert path.read_bytes() == before
    assert audit_rows(config) == []
    assert service.pending_count() == 1


# --------------------------------------------------------------------------
# Reconciliation
# --------------------------------------------------------------------------


def test_reconciliation_finalizes_a_valid_export_exactly_once_and_marks_it_recovered(tmp_path):
    config, export_dir, service = setup(tmp_path)
    operation_id = prepare(service, write_export(export_dir))

    result = service.reconcile()

    assert (result.examined, result.audited, result.abandoned) == (1, 1, 0)
    rows = audit_rows(config)
    assert len(rows) == 1
    assert json.loads(rows[0]["metadata_json"])["reconciled_after_failure"] is True
    assert rows[0]["entity_id"] == operation_id
    assert service.pending_count() == 0


def test_reconciliation_abandons_an_operation_whose_export_was_never_written(tmp_path):
    config, export_dir, service = setup(tmp_path)
    operation_id = prepare(service, reserve_export_path(export_dir, FROZEN, "manual"))

    result = service.reconcile()

    assert (result.abandoned, result.audited) == (1, 0)
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == "abandoned"
    assert audit_rows(config) == []
    assert service.pending_count() == 0


def test_reconciliation_leaves_an_ambiguous_export_unresolved_and_counted(tmp_path):
    config, export_dir, service = setup(tmp_path)
    path = reserve_export_path(export_dir, FROZEN, "manual")
    path.write_text("{ not json", encoding="utf-8")
    operation_id = prepare(service, path)

    result = service.reconcile()

    assert (result.unresolved, result.audited, result.abandoned) == (1, 0, 0)
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == "pending_audit"
    assert audit_rows(config) == []
    assert service.pending_count() == 1
    assert path.read_text(encoding="utf-8") == "{ not json"


def test_reconciliation_never_touches_another_artifact_kind(tmp_path):
    config, export_dir, service = setup(tmp_path)
    repository = ArtifactAuditOperationRepository(config)
    repository.prepare_operation(
        operation_id="11111111-2222-3333-4444-555555555555",
        artifact_kind="report_document",
        primary_filename="workshop-overview-20260801-101112.md",
        companion_filename="workshop-overview-20260801-101112.json",
        audit_action="report_document.created",
    )
    repository.prepare_operation(
        operation_id="66666666-7777-8888-9999-aaaaaaaaaaaa",
        artifact_kind="manual_backup",
        primary_filename="20260801T101112131415Z-cosmetic_workshop-backup-manual.sqlite",
        companion_filename=None,
        audit_action="backup.created",
    )
    prepare(service, write_export(export_dir))

    result = service.reconcile()

    assert result.examined == 1
    assert [row["action"] for row in audit_rows(config)] == ["export.created"]
    assert repository.get_operation("11111111-2222-3333-4444-555555555555").status == "prepared"
    assert repository.get_operation("66666666-7777-8888-9999-aaaaaaaaaaaa").status == "prepared"
    assert repository.count_unresolved("report_document") == 1
    assert repository.count_unresolved("manual_backup") == 1


def test_one_broken_operation_does_not_block_the_others(tmp_path):
    config, export_dir, service = setup(tmp_path)
    broken = reserve_export_path(export_dir, FROZEN, "manual")
    broken.write_text("{ not json", encoding="utf-8")
    broken_id = prepare(service, broken)
    healthy = write_export(export_dir, reason="before_import")
    healthy_id = prepare(service, healthy)

    result = service.reconcile()

    assert result.examined == 2
    assert result.audited == 1
    assert result.unresolved == 1
    repository = ArtifactAuditOperationRepository(config)
    assert repository.get_operation(healthy_id).status == "audited"
    assert repository.get_operation(broken_id).status == "pending_audit"


def test_reconciliation_never_scans_arbitrary_legacy_exports(tmp_path):
    """Only the filenames the ledger recorded are ever inspected."""
    config, export_dir, service = setup(tmp_path)
    legacy_one = write_export(export_dir, reason="legacy_one")
    legacy_two = write_export(export_dir, reason="legacy_two", suffix="20250101T000000000000Z-cosmetic_workshop-export-legacy_two.json")
    before = {path: path.read_bytes() for path in (legacy_one, legacy_two)}

    result = service.reconcile()

    assert (result.examined, result.audited, result.abandoned, result.unresolved) == (0, 0, 0, 0)
    assert audit_rows(config) == []
    for path, content in before.items():
        assert path.read_bytes() == content


def test_reconciliation_survives_an_unreadable_ledger_without_raising(tmp_path, monkeypatch):
    _config, _export_dir, service = setup(tmp_path)

    def failing_list(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger read failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "list_unresolved", failing_list)

    result = service.reconcile()

    assert result.failed == 1
    assert result.audited == 0


def test_a_post_write_final_stat_failure_is_recovered_by_a_later_reconciliation(tmp_path, monkeypatch):
    """The adjacent path ADR 0014 records as 8.8, proved end to end.

    `create_json_export` reads `export_path.stat().st_size` *outside* the `try`
    that maps `OSError` to `ExportError`, so a failure there escapes as a raw
    `OSError` after a complete export is already on disk. The committed
    `prepared` row is what makes that export recoverable rather than orphaned.
    """
    config, export_dir, service = setup(tmp_path)
    reserved = reserve_export_path(export_dir, FROZEN, "manual")
    operation_id = prepare(service, reserved)

    real_stat = Path.stat
    # The writer stats the reserved path twice: once before the write, to refuse
    # an overwrite, and once after it, to read the finished size. Only the
    # second one is the 8.8 boundary, so only the second one fails.
    stats_on_reserved = {"count": 0}

    def failing_stat(self, *args, **kwargs):
        if self == reserved:
            stats_on_reserved["count"] += 1
            if stats_on_reserved["count"] > 1:
                raise OSError(5, "injected post-write stat failure")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", failing_stat)
    with pytest.raises(OSError):
        create_json_export(config.path, export_dir, reason="manual", reserved_export_path=reserved)
    monkeypatch.undo()

    # The export is complete on disk and the operation is still unresolved.
    assert reserved.exists()
    assert json.loads(reserved.read_text(encoding="utf-8"))["manifest"]["source"] == EXPORT_SOURCE
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == "prepared"
    assert audit_rows(config) == []
    assert service.pending_count() == 1

    first = service.reconcile()
    second = service.reconcile()

    assert first.audited == 1
    assert second.examined == 0
    rows = audit_rows(config)
    assert len(rows) == 1
    assert rows[0]["entity_id"] == operation_id
    assert json.loads(rows[0]["metadata_json"])["reconciled_after_failure"] is True
    assert service.pending_count() == 0


def test_the_pending_count_counts_only_unresolved_json_export_rows(tmp_path):
    config, export_dir, service = setup(tmp_path)
    repository = ArtifactAuditOperationRepository(config)

    audited_id = prepare(service, write_export(export_dir, reason="audited_one"))
    service.finalize(audited_id, reconciled_after_failure=False)
    abandoned_id = prepare(service, reserve_export_path(export_dir, FROZEN, "gone"))
    repository.mark_abandoned(abandoned_id)
    prepare(service, write_export(export_dir, reason="still_prepared"))
    pending_id = prepare(service, write_export(export_dir, reason="still_pending"))
    repository.mark_pending_audit(pending_id)
    repository.prepare_operation(
        operation_id="cccccccc-dddd-eeee-ffff-000000000000",
        artifact_kind="report_document",
        primary_filename="workshop-overview-20260801-101112.md",
        companion_filename="workshop-overview-20260801-101112.json",
        audit_action="report_document.created",
    )

    assert service.pending_count() == 2


def test_a_ledger_read_failure_is_raised_rather_than_reported_as_zero(tmp_path, monkeypatch):
    """`0` is a factual claim the frontend clears a standing warning on."""
    _config, _export_dir, service = setup(tmp_path)

    def failing_count(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger read failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "count_unresolved", failing_count)

    with pytest.raises(sqlite3.Error):
        service.pending_count()


def test_the_reserved_export_vocabulary_matches_the_accepted_decision():
    """ADR 0013 reserved this vocabulary for B2; nothing here may drift from it."""
    assert ARTIFACT_KIND_JSON_EXPORT == "json_export"
    assert audit_module.AUDIT_ENTITY_TYPE == "export_file"
    assert audit_module.AUDIT_SUMMARY == "JSON export created"
    assert audit_module.PENDING_AUDIT_MESSAGE == (
        "Экспорт создан, но запись в журнал действий пока не добавлена. "
        "Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта."
    )
    # The warning names the two bounded triggers and implies no background retry.
    for forbidden in ["автоматически", "фон", "повторяет каждые"]:
        assert forbidden not in audit_module.PENDING_AUDIT_MESSAGE


# --------------------------------------------------------------------------
# Typed finalization: verification failure is not a pending Journal entry
#
# The load-bearing distinction of this slice. A single `int | None` could not
# tell "the export did not verify" apart from "the export verified but its
# Journal entry did not commit", and the create path mapped both to `201
# pending` — so an export that failed mandatory verification was reported to the
# user as created. These pin the three outcomes apart.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("outcome", ["ambiguous", "definitely_absent"])
def test_a_non_valid_verification_is_artifact_invalid_and_writes_no_event(tmp_path, monkeypatch, outcome):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    before = path.read_bytes()
    operation_id = prepare(service, path)

    monkeypatch.setattr(
        audit_module.ExportAuditService,
        "verify",
        lambda self, operation: audit_module.ExportVerification(outcome, "injected"),
    )

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.artifact_is_authoritative is False
    assert finalization.is_recorded is False
    assert finalization.audit_log_id is None
    assert audit_rows(config) == []
    # Unresolved and counted — never abandoned on the immediate create path.
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    assert operation.status in ("prepared", "pending_audit")
    assert service.pending_count() == 1
    # Left exactly as it is: this operation could not prove it owns that path.
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "corrupt, expected_reason",
    [
        (lambda path: path.write_text("{not json", encoding="utf-8"), "export-unreadable"),
        (
            lambda path: path.write_text(
                json.dumps({"manifest": {}, "data": {}}), encoding="utf-8"
            ),
            "schema-version-missing",
        ),
    ],
)
def test_a_real_manifest_defect_is_artifact_invalid(tmp_path, corrupt, expected_reason):
    """Genuine verifier verdicts, not injected ones, reach the same outcome."""
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    operation_id = prepare(service, path)
    corrupt(path)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.verification.outcome == "ambiguous"
    assert finalization.verification.reason == expected_reason
    assert audit_rows(config) == []
    assert service.pending_count() == 1


def test_a_real_entity_count_mismatch_is_artifact_invalid(tmp_path):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    operation_id = prepare(service, path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["manifest"]["tables"]["ingredients"] = 99
    path.write_text(json.dumps(payload), encoding="utf-8")

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.verification.reason == "table-counts-mismatch"
    assert audit_rows(config) == []


def test_a_real_unsupported_schema_version_is_artifact_invalid(tmp_path):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir, export_schema_version=EXPORT_SCHEMA_VERSION + 999)
    operation_id = prepare(service, path)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.verification.reason == "unsupported-schema-version"
    assert audit_rows(config) == []


def test_a_malformed_filename_is_artifact_invalid(tmp_path):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir, suffix="not-a-generated-export-name.json")
    operation_id = prepare(service, path)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.verification.reason == "filename-grammar-mismatch"
    assert audit_rows(config) == []
    assert path.exists()


def test_an_unreadable_ledger_is_artifact_invalid_rather_than_a_guess(tmp_path, monkeypatch):
    """Authority was never established, so the export must not be called valid."""
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    operation_id = prepare(service, path)

    def failing_get(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger read failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "get_operation", failing_get)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.artifact_is_authoritative is False
    assert finalization.verification is None
    assert path.exists()


def test_a_transient_verifier_fault_still_reconciles_exactly_once_afterwards(tmp_path, monkeypatch):
    config, export_dir, service = setup(tmp_path)
    path = write_export(export_dir)
    operation_id = prepare(service, path)

    def defective(*_args, **_kwargs):
        raise TypeError("injected transient verifier fault")

    monkeypatch.setattr(audit_module.ExportAuditService, "verify", defective)
    assert service.finalize(operation_id, reconciled_after_failure=False).outcome == "artifact_invalid"
    assert audit_rows(config) == []
    monkeypatch.undo()

    first = service.reconcile()
    second = service.reconcile()

    assert first.audited == 1
    assert second.examined == 0
    rows = audit_rows(config)
    assert len(rows) == 1
    assert json.loads(rows[0]["metadata_json"])["reconciled_after_failure"] is True
    assert service.pending_count() == 0


def test_reconciliation_leaves_an_ambiguous_operation_unresolved_and_abandons_an_absent_one(tmp_path):
    """The two reconciliation verdicts stay distinct under typed finalization."""
    config, export_dir, service = setup(tmp_path)
    ambiguous_path = write_export(export_dir, reason="ambiguous")
    ambiguous_id = prepare(service, ambiguous_path)
    ambiguous_path.write_text("{not json", encoding="utf-8")
    absent_id = prepare(service, write_export(export_dir, reason="absent"))
    (export_dir / ArtifactAuditOperationRepository(config).get_operation(absent_id).primary_filename).unlink()

    result = service.reconcile()

    assert result.abandoned == 1
    assert result.unresolved == 1
    assert result.audited == 0
    repository = ArtifactAuditOperationRepository(config)
    assert repository.get_operation(absent_id).status == "abandoned"
    assert repository.get_operation(ambiguous_id).status == "pending_audit"
    assert audit_rows(config) == []
    # The ambiguous file is never deleted by reconciliation.
    assert ambiguous_path.exists()


# --------------------------------------------------------------------------
# Mutation protection for the typed outcome vocabulary
# --------------------------------------------------------------------------


def test_only_recorded_and_audit_pending_are_authoritative():
    """Renaming `artifact_invalid` into a success would defeat the whole slice."""
    Finalization = audit_module.ExportFinalization
    assert Finalization("recorded", audit_log_id=1).artifact_is_authoritative is True
    assert Finalization("audit_pending").artifact_is_authoritative is True
    assert Finalization("artifact_invalid").artifact_is_authoritative is False
    assert Finalization("recorded", audit_log_id=1).is_recorded is True
    assert Finalization("audit_pending").is_recorded is False
    assert Finalization("artifact_invalid").is_recorded is False


def test_the_create_path_refuses_an_invalid_artifact_and_keeps_the_file(tmp_path, monkeypatch):
    """The create orchestration, not just the finalizer, must enforce the boundary."""
    from app.services.export import ExportPaths
    from app.services.export_creation import create_audited_json_export

    config, export_dir, _service = setup(tmp_path)
    monkeypatch.setattr(
        audit_module.ExportAuditService,
        "finalize",
        lambda self, operation_id, *, reconciled_after_failure: audit_module.ExportFinalization(
            "artifact_invalid"
        ),
    )

    with pytest.raises(audit_module.ExportArtifactUnverifiedError):
        create_audited_json_export(
            ExportPaths(database_path=config.path, export_dir=export_dir), "manual", config=config
        )

    # The file survives the refusal: ownership is exactly what failed to verify.
    assert len(list(export_dir.glob("*.json"))) == 1
    assert audit_rows(config) == []


def test_the_create_path_still_accepts_a_verified_export_with_a_pending_journal(tmp_path, monkeypatch):
    from app.services.export import ExportPaths
    from app.services.export_creation import create_audited_json_export

    config, export_dir, _service = setup(tmp_path)
    monkeypatch.setattr(
        audit_module.ExportAuditService,
        "finalize",
        lambda self, operation_id, *, reconciled_after_failure: audit_module.ExportFinalization(
            "audit_pending"
        ),
    )

    created = create_audited_json_export(
        ExportPaths(database_path=config.path, export_dir=export_dir), "manual", config=config
    )

    assert created.audit_status == "pending"
    assert created.audit_message == audit_module.PENDING_AUDIT_MESSAGE
    # CR-006 is untouched: the response still describes the exact ExportResult.
    assert created.result.export_path.exists()
    assert created.canonical_reason == "manual"
