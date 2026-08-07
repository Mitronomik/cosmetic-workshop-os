"""C4-II-A1 non-destructive Restore candidate-preparation contract."""

from pathlib import Path
import hashlib
import os
import sqlite3
import stat

import pytest

from app.db.migrations import MIGRATION_TABLE, expected_migration_ids
from launcher.restore.validation_session import (
    MAX_DISPLAY_FILENAME_CHARS,
    CandidateCompatibility,
    CandidatePreparationFailure,
    CandidatePreparationState,
    RestoreCandidatePreparationService,
)
from launcher.restore.validation_scratch import (
    ValidationScratchError,
    ValidationScratchManager,
)
from launcher.restore.workspace import resolve_restore_dir
from launcher.tests.restore_fixtures import (
    build_workspace_database,
    make_source_backup,
    make_workspace,
)


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit_count(path: Path) -> int:
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])


def rewrite_history(path: Path, migration_ids: list[str]) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(f"DELETE FROM {MIGRATION_TABLE}")
        connection.executemany(
            f"INSERT INTO {MIGRATION_TABLE} (migration_id) VALUES (?)",
            [(migration_id,) for migration_id in migration_ids],
        )


@pytest.fixture
def working_database(tmp_path):
    return build_workspace_database(tmp_path / "data" / "workshop.sqlite", "working")


@pytest.fixture
def current_source(tmp_path):
    return build_workspace_database(tmp_path / "chosen" / "backup.sqlite", "source")


@pytest.fixture
def scratch_root(tmp_path):
    return tmp_path / "system-temp" / "cosmetic-workshop-os" / "restore-validation"


def test_current_schema_is_accepted_and_retains_only_launcher_private_proof(
    working_database, current_source, scratch_root
):
    source_before = digest(current_source)
    working_before = digest(working_database)

    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(current_source)
        proof = service.retained_proof

        assert result.state is CandidatePreparationState.ACCEPTED
        assert result.compatibility is CandidateCompatibility.CURRENT_SCHEMA
        assert result.failure is None
        assert result.filename == current_source.name
        assert result.accepted is True
        assert proof is not None
        assert proof.generation == result.generation
        assert proof.compatibility is CandidateCompatibility.CURRENT_SCHEMA
        assert proof.source_path == current_source.resolve()
        assert proof.sha256 == source_before
        assert proof.source_identity.st_size == current_source.stat().st_size

        # Presentation-safe result: only the basename and opaque IDs leave the
        # service.  Absolute source/staged paths are not DTO fields.
        assert str(current_source) not in repr(result)
        assert str(current_source.parent) not in result.message
        assert not (service._scratch.run_dir / result.session_id / "candidate.sqlite").exists()

    assert digest(current_source) == source_before
    assert digest(working_database) == working_before


def test_display_filename_is_bounded_and_removes_control_formatting(
    tmp_path, working_database, scratch_root
):
    unsafe_name = "backup\n\t\u202e" + ("x" * 200) + ".sqlite"
    source = build_workspace_database(tmp_path / "chosen" / unsafe_name, "unsafe-label")

    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(source)

        assert result.accepted is True
        assert "\n" not in result.filename
        assert "\t" not in result.filename
        assert "\u202e" not in result.filename
        assert len(result.filename) <= MAX_DISPLAY_FILENAME_CHARS
        assert str(source.parent) not in result.filename


def test_known_older_schema_is_accepted_without_migrating_source_or_working_database(
    tmp_path, working_database, scratch_root
):
    older = build_workspace_database(
        tmp_path / "chosen" / "older.sqlite",
        "older",
        up_to="0018_demo_data_tracking",
    )
    source_before = digest(older)
    working_before = digest(working_database)

    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(older)
        proof = service.retained_proof

        assert result.state is CandidatePreparationState.ACCEPTED
        assert result.compatibility is CandidateCompatibility.OLDER_SUPPORTED_SCHEMA
        assert proof is not None
        assert proof.compatibility is CandidateCompatibility.OLDER_SUPPORTED_SCHEMA

    assert digest(older) == source_before
    assert digest(working_database) == working_before
    with sqlite3.connect(f"file:{older}?mode=ro", uri=True) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    assert "artifact_audit_operations" not in tables


def test_newer_schema_is_typed_unsupported_and_retains_no_proof(
    working_database, current_source, scratch_root
):
    rewrite_history(current_source, expected_migration_ids() + ["0021_from_the_future"])
    before = digest(current_source)

    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(current_source)

        assert result.state is CandidatePreparationState.REJECTED
        assert result.failure is CandidatePreparationFailure.UNSUPPORTED_SCHEMA
        assert result.compatibility is None
        assert service.retained_proof is None
        assert "0021_from_the_future" not in result.message

    assert digest(current_source) == before


@pytest.mark.parametrize(
    "kind, expected",
    [
        ("empty", CandidatePreparationFailure.SOURCE_REJECTED),
        ("directory", CandidatePreparationFailure.SOURCE_REJECTED),
        ("foreign", CandidatePreparationFailure.CANDIDATE_INVALID),
        ("corrupt", CandidatePreparationFailure.CANDIDATE_INVALID),
    ],
)
def test_invalid_source_classes_are_typed_without_leaking_technical_details(
    tmp_path, working_database, scratch_root, kind, expected
):
    source = tmp_path / "chosen" / f"{kind}.sqlite"
    source.parent.mkdir(parents=True, exist_ok=True)
    if kind == "empty":
        source.write_bytes(b"")
    elif kind == "directory":
        source.mkdir()
    elif kind == "foreign":
        with sqlite3.connect(source) as connection:
            connection.execute("CREATE TABLE notes (body TEXT)")
            connection.execute("INSERT INTO notes VALUES ('healthy but foreign')")
    elif kind == "corrupt":
        source.write_bytes(b"SQLite format 3\x00" + b"not-a-real-database" * 200)

    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(source)

        assert result.state is CandidatePreparationState.REJECTED
        assert result.failure is expected
        assert service.retained_proof is None
        assert str(source) not in result.message
        assert "sqlite" not in result.message.lower()


def test_symlink_working_database_and_source_sidecar_are_rejected_by_c4_i_rules(
    tmp_path, working_database, current_source, scratch_root
):
    symlink = tmp_path / "chosen" / "linked.sqlite"
    symlink.symlink_to(current_source)

    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        linked = service.prepare_restore_candidate(symlink)
        working = service.prepare_restore_candidate(working_database)

        current_source.with_name(current_source.name + "-wal").write_bytes(b"sidecar")
        sidecar = service.prepare_restore_candidate(current_source)

        assert linked.failure is CandidatePreparationFailure.SOURCE_REJECTED
        assert working.failure is CandidatePreparationFailure.SOURCE_REJECTED
        # C4-I deliberately presents a sidecar-dependent source as an invalid
        # candidate rather than as a generic path-selection mistake.
        assert sidecar.failure is CandidatePreparationFailure.CANDIDATE_INVALID
        assert service.retained_proof is None


def test_candidate_preparation_creates_no_restore_operation_safety_copy_audit_or_db_change(
    monkeypatch, tmp_path, scratch_root
):
    workspace = make_workspace(monkeypatch, tmp_path)
    source = make_source_backup(tmp_path, "restore-source")
    working_before = digest(workspace.database_path)
    source_before = digest(source)
    audit_before = audit_count(workspace.database_path)
    durable_restore_dir = resolve_restore_dir(workspace.database_path)
    safety_before = workspace.safety_copies()

    with RestoreCandidatePreparationService(
        workspace.database_path, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(source)
        assert result.accepted is True

    assert digest(workspace.database_path) == working_before
    assert digest(source) == source_before
    assert audit_count(workspace.database_path) == audit_before
    assert workspace.safety_copies() == safety_before
    assert not durable_restore_dir.exists(), "A1 created durable C4-I Restore state"


def test_cancel_during_validation_blocks_late_proof_publication(
    monkeypatch, working_database, current_source, scratch_root
):
    from launcher.restore import validation_session as module

    real_validate = module.validate_staged_candidate
    service = RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    )

    def cancel_then_validate(path):
        service.cancel()
        return real_validate(path)

    monkeypatch.setattr(module, "validate_staged_candidate", cancel_then_validate)
    try:
        result = service.prepare_restore_candidate(current_source)

        assert result.state is CandidatePreparationState.CANCELLED
        assert result.failure is CandidatePreparationFailure.CANCELLED
        assert service.retained_proof is None
        assert not (service._scratch.run_dir / result.session_id).exists()
    finally:
        service.close()


def test_new_selection_clears_previous_proof_before_new_staging(
    monkeypatch, tmp_path, working_database, scratch_root
):
    from launcher.restore import validation_session as module

    first = build_workspace_database(tmp_path / "chosen" / "first.sqlite", "first")
    second = build_workspace_database(tmp_path / "chosen" / "second.sqlite", "second")
    service = RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    )
    try:
        first_result = service.prepare_restore_candidate(first)
        assert first_result.accepted is True
        assert service.retained_proof is not None
        first_generation = first_result.generation

        observed = []
        real_stage = module.stage_source

        def observe_then_stage(workspace, operation_id, held):
            observed.append(service.retained_proof)
            return real_stage(workspace, operation_id, held)

        monkeypatch.setattr(module, "stage_source", observe_then_stage)
        second_result = service.prepare_restore_candidate(second)

        assert observed == [None]
        assert second_result.accepted is True
        assert second_result.generation > first_generation
        assert service.retained_proof is not None
        assert service.retained_proof.source_path == second.resolve()
    finally:
        service.close()


def test_source_change_during_candidate_validation_is_refused_and_not_retained(
    monkeypatch, working_database, current_source, scratch_root
):
    from launcher.restore import validation_session as module

    real_validate = module.validate_staged_candidate
    before = digest(current_source)

    def mutate_source_after_staging(path):
        validated = real_validate(path)
        with current_source.open("ab") as stream:
            stream.write(b"changed-after-staging")
        return validated

    monkeypatch.setattr(module, "validate_staged_candidate", mutate_source_after_staging)
    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(current_source)

        assert result.state is CandidatePreparationState.REJECTED
        assert result.failure is CandidatePreparationFailure.SOURCE_REJECTED
        assert service.retained_proof is None

    assert digest(current_source) != before, "fixture did not actually mutate the source"


def test_internal_failure_returns_fixed_safe_message_and_no_proof(
    monkeypatch, working_database, current_source, scratch_root
):
    from launcher.restore import validation_session as module
    from launcher.restore.staging import StagingError

    def fail_stage(_workspace, _operation_id, _held):
        raise StagingError("SECRET /tmp/private/source.sqlite raw sqlite detail")

    monkeypatch.setattr(module, "stage_source", fail_stage)
    with RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    ) as service:
        result = service.prepare_restore_candidate(current_source)

        assert result.state is CandidatePreparationState.TECHNICAL_FAILURE
        assert result.failure is CandidatePreparationFailure.TECHNICAL_FAILURE
        assert "SECRET" not in result.message
        assert "/tmp/private" not in result.message
        assert service.retained_proof is None


def test_validation_scratch_is_private_and_interrupted_cleanup_is_owned_only(
    tmp_path, working_database, scratch_root
):
    stale = ValidationScratchManager(working_database, root=scratch_root)
    stale_session = stale.create_session()
    (stale_session.directory / "candidate.sqlite").write_bytes(b"owned scratch")

    assert stat.S_IMODE(stale.root.stat().st_mode) & 0o077 == 0
    assert stat.S_IMODE(stale.run_dir.stat().st_mode) & 0o077 == 0
    assert stat.S_IMODE(stale_session.directory.stat().st_mode) & 0o077 == 0

    outside = tmp_path / "outside"
    outside.mkdir()
    foreign = scratch_root / "foreign-run"
    foreign.mkdir()
    foreign_file = foreign / "keep.txt"
    foreign_file.write_text("not launcher owned", encoding="utf-8")
    escape = scratch_root / "escape-link"
    escape.symlink_to(outside, target_is_directory=True)

    current = ValidationScratchManager(working_database, root=scratch_root)
    try:
        removed = current.cleanup_interrupted_runs()

        assert removed == 1
        assert not stale.run_dir.exists()
        assert foreign_file.read_text(encoding="utf-8") == "not launcher owned"
        assert escape.is_symlink()
        assert outside.exists()
    finally:
        assert current.cleanup_current_run_if_empty() is True


def test_default_scratch_refuses_symlinked_app_ancestry(
    monkeypatch, tmp_path, working_database
):
    from launcher.restore import validation_scratch as module

    fake_temp = tmp_path / "system-temp"
    fake_temp.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (fake_temp / module.VALIDATION_APP_DIRNAME).symlink_to(
        outside, target_is_directory=True
    )
    monkeypatch.setattr(module.tempfile, "gettempdir", lambda: str(fake_temp))

    with pytest.raises(ValidationScratchError):
        ValidationScratchManager(working_database)

    assert not (outside / module.VALIDATION_DIRNAME).exists()


def test_close_clears_retained_proof_and_removes_empty_run_root(
    working_database, current_source, scratch_root
):
    service = RestoreCandidatePreparationService(
        working_database, scratch_root=scratch_root
    )
    run_dir = service._scratch.run_dir

    result = service.prepare_restore_candidate(current_source)
    assert result.accepted is True
    assert service.retained_proof is not None
    assert run_dir.exists()

    service.close()

    assert service.retained_proof is None
    assert not run_dir.exists()
