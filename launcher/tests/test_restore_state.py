"""The durable operation record and its crash-safe publication boundary.

Two things are proved here, and they are the reason `CR-010` § 7.3 refuses an
in-place rewrite:

1. **The record carries only what recovery needs.** No database contents, no
   business data, no raw source path, and — critically — no independent
   `replacement_happened` / `rollback_completed` booleans that could contradict
   `phase`.
2. **After interruption at any publication boundary, the file on disk is either
   the complete old record or the complete new one.** Faults are injected at
   every step: scratch creation, write, file fsync, the atomic `os.replace`, and
   the parent-directory fsync.
"""

from pathlib import Path
import json

import pytest

from launcher.restore import state as state_module
from launcher.restore.phases import PhaseTransitionError, RestorePhase
from launcher.restore.state import (
    ALLOWED_RECORD_FIELDS,
    RestoreOperationRecord,
    RestoreOperationStateStore,
    RestoreStateError,
)
from launcher.restore.workspace import OWNED_TEMP_PREFIX, RestoreWorkspace, new_operation_id


@pytest.fixture
def store(tmp_path):
    workspace = RestoreWorkspace(
        restore_dir=tmp_path / "restore", database_path=tmp_path / "data" / "workshop.sqlite"
    )
    return RestoreOperationStateStore(workspace)


def read_raw(store) -> dict:
    return json.loads(store.record_path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# What may be persisted
# --------------------------------------------------------------------------

def test_only_the_allowed_recovery_fields_are_serialized(store):
    record = store.create(new_operation_id())

    assert set(read_raw(store)) == set(ALLOWED_RECORD_FIELDS)
    assert set(ALLOWED_RECORD_FIELDS) == {
        "operation_id",
        "phase",
        "created_at",
        "updated_at",
        "staged_candidate_filename",
        "safety_copy_filename",
    }
    assert record.phase is RestorePhase.PREPARED


def test_no_independent_replacement_or_rollback_booleans_exist(store):
    """`phase` is the sole authoritative lifecycle field."""
    store.create(new_operation_id())
    payload = read_raw(store)

    for forbidden in ("replacement_happened", "rollback_completed", "restore_succeeded"):
        assert forbidden not in payload
    assert not any(isinstance(value, bool) for value in payload.values())


def test_no_raw_source_path_is_persisted(store, tmp_path):
    """A staged relative identity is sufficient, so the absolute path is not kept."""
    record = store.create(new_operation_id())
    record = store.transition(
        record, RestorePhase.SOURCE_STAGED, staged_candidate_filename="candidate.sqlite"
    )

    serialized = store.record_path.read_text(encoding="utf-8")
    assert "candidate.sqlite" in serialized
    assert str(tmp_path) not in serialized
    assert "/" not in record.staged_candidate_filename


def test_no_business_data_can_reach_the_record(store):
    """The dataclass has no field a client name or SQL error could ride in on."""
    fields = {field for field in RestoreOperationRecord.__dataclass_fields__}
    assert fields == set(ALLOWED_RECORD_FIELDS)


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def test_no_record_reads_as_none(store):
    assert store.read() is None
    assert store.has_record() is False


def test_a_malformed_record_is_never_ignored(store):
    store.workspace.ensure_restore_dir()
    store.record_path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(RestoreStateError):
        store.read()


def test_a_record_with_unexpected_extra_fields_is_rejected(store):
    record = store.create(new_operation_id())
    payload = record.to_json_object()
    payload["replacement_happened"] = True
    store.record_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RestoreStateError):
        store.read()


def test_a_record_with_a_missing_field_is_rejected(store):
    record = store.create(new_operation_id())
    payload = record.to_json_object()
    del payload["safety_copy_filename"]
    store.record_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RestoreStateError):
        store.read()


def test_an_unknown_phase_is_rejected(store):
    record = store.create(new_operation_id())
    payload = record.to_json_object()
    payload["phase"] = "almost_completed"
    store.record_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RestoreStateError):
        store.read()


def test_an_unsafe_filename_in_a_record_is_rejected(store):
    record = store.create(new_operation_id())
    payload = record.to_json_object()
    payload["safety_copy_filename"] = "../../escape.sqlite"
    store.record_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RestoreStateError):
        store.read()


def test_an_unsafe_operation_identity_in_a_record_is_rejected(store):
    record = store.create(new_operation_id())
    payload = record.to_json_object()
    payload["operation_id"] = "../elsewhere"
    store.record_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RestoreStateError):
        store.read()


# --------------------------------------------------------------------------
# Transitions through the store
# --------------------------------------------------------------------------

def test_the_store_refuses_an_unauthorized_transition(store):
    record = store.create(new_operation_id())

    with pytest.raises(PhaseTransitionError):
        store.transition(record, RestorePhase.COMPLETED)
    # Nothing was published, so the durable phase is unchanged.
    assert store.read().phase is RestorePhase.PREPARED


def test_a_second_attempt_needs_a_new_operation_id(store):
    first = store.create(new_operation_id())
    store.transition(first, RestorePhase.ABORTED)

    second_id = new_operation_id()
    assert second_id != first.operation_id
    second = store.create(second_id)
    assert second.operation_id == second_id


def test_a_terminal_record_is_never_reactivated_under_the_same_id(store):
    record = store.create(new_operation_id())
    store.transition(record, RestorePhase.ABORTED)

    with pytest.raises(RestoreStateError):
        store.create(record.operation_id)


def test_a_live_operation_blocks_a_new_attempt(store):
    store.create(new_operation_id())

    with pytest.raises(RestoreStateError):
        store.create(new_operation_id())


def test_recorded_filenames_are_additive_and_cannot_be_blanked(store):
    record = store.create(new_operation_id())
    record = store.transition(
        record, RestorePhase.SOURCE_STAGED, staged_candidate_filename="candidate.sqlite"
    )
    record = store.transition(record, RestorePhase.CANDIDATE_VALIDATED)

    assert record.staged_candidate_filename == "candidate.sqlite"


# --------------------------------------------------------------------------
# Fault injection at every publication boundary
# --------------------------------------------------------------------------

def _existing_record(store):
    record = store.create(new_operation_id())
    return store.transition(
        record, RestorePhase.SOURCE_STAGED, staged_candidate_filename="candidate.sqlite"
    )


@pytest.mark.parametrize(
    "boundary",
    ["_create_owned_scratch", "_write_scratch_record", "_fsync_file", "_publish_scratch"],
)
def test_a_fault_at_any_boundary_leaves_the_complete_old_record(store, monkeypatch, boundary):
    """Old-or-new, never a partial authoritative record."""
    before = _existing_record(store)
    before_bytes = store.record_path.read_bytes()

    def explode(*_args, **_kwargs):
        raise OSError(5, "injected fault")

    monkeypatch.setattr(state_module, boundary, explode)

    with pytest.raises(RestoreStateError):
        store.transition(before, RestorePhase.CANDIDATE_VALIDATED)

    assert store.record_path.read_bytes() == before_bytes
    assert store.read().phase is RestorePhase.SOURCE_STAGED


def test_a_parent_directory_fsync_failure_does_not_lose_the_new_record(store, monkeypatch):
    """The atomic boundary already held; only its durability is best-effort.

    Refusing here would break Restore on a mount that will not fsync a directory,
    while the old-or-new guarantee the recovery matrix depends on is unaffected.
    """
    import os
    import stat

    record = _existing_record(store)
    real_fsync = state_module.os.fsync

    def refuse_directories(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError(22, "directory fsync unsupported")
        return real_fsync(fd)

    monkeypatch.setattr(state_module.os, "fsync", refuse_directories)

    published = store.transition(record, RestorePhase.CANDIDATE_VALIDATED)

    assert published.phase is RestorePhase.CANDIDATE_VALIDATED
    assert store.read().phase is RestorePhase.CANDIDATE_VALIDATED


def test_a_failed_publication_leaves_no_scratch_file_behind(store, monkeypatch):
    record = _existing_record(store)
    monkeypatch.setattr(
        state_module, "_publish_scratch", lambda *_a: (_ for _ in ()).throw(OSError("no"))
    )

    with pytest.raises(RestoreStateError):
        store.transition(record, RestorePhase.CANDIDATE_VALIDATED)

    leftovers = [
        path for path in store.workspace.restore_dir.iterdir()
        if path.name.startswith(OWNED_TEMP_PREFIX)
    ]
    assert leftovers == []


def test_publication_never_rewrites_the_record_in_place(store, monkeypatch):
    """The authoritative name is only ever reached through `os.replace`."""
    record = _existing_record(store)
    replacements: list[tuple[str, str]] = []
    real_replace = state_module.os.replace

    def record_replace(src, dst):
        replacements.append((str(src), str(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(state_module.os, "replace", record_replace)
    store.transition(record, RestorePhase.CANDIDATE_VALIDATED)

    assert len(replacements) == 1
    source, destination = replacements[0]
    assert destination == str(store.record_path)
    assert Path(source).name.startswith(OWNED_TEMP_PREFIX)


def test_the_scratch_file_is_created_in_the_publication_directory(store, monkeypatch):
    """Same directory, so the publication rename stays on one filesystem."""
    record = _existing_record(store)
    seen: list[Path] = []
    real_create = state_module._create_owned_scratch

    def watched(directory):
        seen.append(Path(directory))
        return real_create(directory)

    monkeypatch.setattr(state_module, "_create_owned_scratch", watched)
    store.transition(record, RestorePhase.CANDIDATE_VALIDATED)

    assert seen == [store.workspace.restore_dir]


def test_cleanup_only_removes_launcher_owned_temp_files(store):
    workspace = store.workspace
    workspace.ensure_restore_dir()
    foreign = workspace.restore_dir / "somebody-elses-file.txt"
    foreign.write_text("keep me", encoding="utf-8")
    owned = workspace.restore_dir / f"{OWNED_TEMP_PREFIX}abcdef.tmp"
    owned.write_text("scratch", encoding="utf-8")

    workspace.clean_owned_temp_files()

    assert foreign.exists()
    assert not owned.exists()


def test_cleanup_never_follows_a_symlink_out_of_the_boundary(store, tmp_path):
    workspace = store.workspace
    workspace.ensure_restore_dir()
    outside = tmp_path / "outside.txt"
    outside.write_text("precious", encoding="utf-8")
    link = workspace.restore_dir / f"{OWNED_TEMP_PREFIX}link.tmp"
    link.symlink_to(outside)

    workspace.clean_owned_temp_files()

    assert outside.exists()
    assert link.is_symlink()
