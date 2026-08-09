"""C4-II-B1 retained A1 source-proof binding at the C4-I intake boundary.

All data live in isolated temporary workspaces. A proof mismatch must be refused
before `prepared`, before a safety copy and before working-database mutation.
Legacy C4-I calls without a proof remain behaviorally unchanged.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import os

import pytest

from launcher.restore import engine as engine_module
from launcher.restore import source_proof as proof_module
from launcher.restore import staging as staging_module
from launcher.restore.contracts import (
    ExpectedSourceProof,
    ProofBoundRestoreRequest,
    RestoreFailure,
    RestoreOutcome,
    USER_SAFE_MESSAGES,
)
from launcher.restore.engine import execute_restore
from launcher.restore.state import RestoreOperationStateStore
from launcher.restore.validation_session import RestoreCandidatePreparationService
from launcher.restore.workspace import (
    BACKEND_LIVENESS_LOCK_FILENAME,
    INSTANCE_LOCK_FILENAME,
    RestoreWorkspace,
)
from launcher.tests.restore_fixtures import (
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)


A1_TEST_RUN_ID = "123e4567-e89b-42d3-a456-426614174000"


def digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def store_for(workspace_fixture) -> RestoreOperationStateStore:
    return RestoreOperationStateStore(
        RestoreWorkspace(
            restore_dir=workspace_fixture.restore_dir,
            database_path=workspace_fixture.database_path,
        )
    )


def expected_from_a1(workspace, source: Path, tmp_path: Path) -> ExpectedSourceProof:
    service = RestoreCandidatePreparationService(
        workspace.database_path,
        scratch_root=tmp_path / "validation-scratch",
        run_id=A1_TEST_RUN_ID,
    )
    try:
        result = service.prepare_restore_candidate(source)
        assert result.accepted
        retained = service.retained_proof
        assert retained is not None
        assert retained.source_path == source.resolve(strict=True)
        return ExpectedSourceProof(
            source_identity=retained.source_identity,
            sha256=retained.sha256,
        )
    finally:
        service.close()


def run_bound(workspace, source: Path, expected: ExpectedSourceProof, context):
    return execute_restore(
        ProofBoundRestoreRequest(
            selected_source=source,
            expected_source_proof=expected,
        ),
        context,
        services=stub_services(workspace.database_path),
    )


def assert_refused_before_prepared(workspace, result, *, database_digest: str) -> None:
    assert result.outcome is RestoreOutcome.ABORTED
    assert result.durable_phase is None
    assert result.failure is RestoreFailure.SOURCE_CHANGED
    assert result.message == USER_SAFE_MESSAGES[RestoreFailure.SOURCE_CHANGED]
    assert result.normal_startup_allowed is True
    assert store_for(workspace).read() is None
    assert workspace.safety_copies() == []
    assert digest(workspace.database_path) == database_digest
    if workspace.restore_dir.exists():
        entries = list(workspace.restore_dir.iterdir())
        assert {entry.name for entry in entries} <= {
            INSTANCE_LOCK_FILENAME,
            BACKEND_LIVENESS_LOCK_FILENAME,
        }
        assert all(entry.is_file() and not entry.is_symlink() for entry in entries)


@pytest.fixture
def scenario(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    expected = expected_from_a1(workspace, source, tmp_path)
    context = workspace.context()
    try:
        yield workspace, source, expected, context
    finally:
        context.release()


def test_exact_a1_identity_and_digest_allow_existing_c4_i_flow(scenario):
    workspace, source, expected, context = scenario
    source_before = digest(source)

    result = run_bound(workspace, source, expected, context)

    assert result.outcome is RestoreOutcome.COMPLETED
    assert result.restore_succeeded is True
    assert read_marker(workspace.database_path) == "workspace-B"
    assert digest(source) == source_before


def test_proof_gate_and_stage_use_the_same_held_source_descriptor(monkeypatch, scenario):
    workspace, source, expected, context = scenario
    seen: dict[str, int] = {}
    real_bind = proof_module.bind_expected_source_proof
    real_stage = engine_module.stage_source

    def tracked_bind(held, proof):
        seen["proof_object"] = id(held)
        seen["proof_fd"] = held.fd
        return real_bind(held, proof)

    def tracked_stage(workspace_arg, operation_id, held):
        seen["stage_object"] = id(held)
        seen["stage_fd"] = held.fd
        return real_stage(workspace_arg, operation_id, held)

    monkeypatch.setattr(engine_module, "bind_expected_source_proof", tracked_bind)
    monkeypatch.setattr(engine_module, "stage_source", tracked_stage)

    result = run_bound(workspace, source, expected, context)

    assert result.restore_succeeded is True
    assert seen["proof_object"] == seen["stage_object"]
    assert seen["proof_fd"] == seen["stage_fd"]


def test_same_path_replaced_with_different_inode_is_refused_before_prepared(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    expected = expected_from_a1(workspace, source, tmp_path)
    replacement = tmp_path / "replacement" / source.name
    replacement.parent.mkdir(parents=True, exist_ok=True)
    make_source_backup(tmp_path / "replacement-fixture", "workspace-C").replace(replacement)
    os.replace(replacement, source)
    database_before = digest(workspace.database_path)
    context = workspace.context()
    try:
        result = run_bound(workspace, source, expected, context)
    finally:
        context.release()

    assert_refused_before_prepared(workspace, result, database_digest=database_before)


def test_same_inode_and_size_changed_bytes_are_refused_by_digest_proof(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    expected = expected_from_a1(workspace, source, tmp_path)

    payload = source.read_bytes()
    marker_offset = payload.find(b"workspace-B")
    assert marker_offset >= 0
    before_stat = source.stat()
    with source.open("r+b") as stream:
        stream.seek(marker_offset)
        stream.write(b"workspace-C")
    after_stat = source.stat()
    assert after_stat.st_ino == before_stat.st_ino
    assert after_stat.st_size == before_stat.st_size

    # Freeze identity reconstruction so only the full held-descriptor digest can
    # detect the same-inode, same-size byte change.
    monkeypatch.setattr(
        staging_module.SourceIdentity,
        "from_stat",
        classmethod(lambda _cls, _info: expected.source_identity),
    )

    database_before = digest(workspace.database_path)
    context = workspace.context()
    try:
        result = run_bound(workspace, source, expected, context)
    finally:
        context.release()

    assert_refused_before_prepared(workspace, result, database_digest=database_before)


def test_sidecar_appearing_after_a1_validation_is_refused_before_prepared(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    expected = expected_from_a1(workspace, source, tmp_path)
    source_before = digest(source)
    Path(str(source) + "-wal").write_bytes(b"late-sidecar")
    database_before = digest(workspace.database_path)
    context = workspace.context()
    try:
        result = run_bound(workspace, source, expected, context)
    finally:
        context.release()

    assert_refused_before_prepared(workspace, result, database_digest=database_before)
    assert digest(source) == source_before


def test_symlink_substitution_after_a1_validation_is_refused_before_prepared(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    expected = expected_from_a1(workspace, source, tmp_path)
    original = source.with_name("accepted-original.sqlite")
    source.replace(original)
    source.symlink_to(original)
    original_before = digest(original)
    database_before = digest(workspace.database_path)
    context = workspace.context()
    try:
        result = run_bound(workspace, source, expected, context)
    finally:
        context.release()

    assert_refused_before_prepared(workspace, result, database_digest=database_before)
    assert digest(original) == original_before


def test_expected_digest_byte_count_mismatch_is_refused_before_prepared(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    expected = expected_from_a1(workspace, source, tmp_path)
    source_before = digest(source)
    real_digest = staging_module.HeldSource.digest

    def short_digest(self):
        actual, count = real_digest(self)
        return actual, count - 1

    monkeypatch.setattr(staging_module.HeldSource, "digest", short_digest)
    database_before = digest(workspace.database_path)
    context = workspace.context()
    try:
        result = run_bound(workspace, source, expected, context)
    finally:
        context.release()

    assert_refused_before_prepared(workspace, result, database_digest=database_before)
    assert digest(source) == source_before


def test_wrong_expected_sha_is_refused_without_source_or_database_mutation(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    accepted = expected_from_a1(workspace, source, tmp_path)
    expected = ExpectedSourceProof(
        source_identity=accepted.source_identity,
        sha256="0" * 64,
    )
    source_before = digest(source)
    database_before = digest(workspace.database_path)
    context = workspace.context()
    try:
        result = run_bound(workspace, source, expected, context)
    finally:
        context.release()

    assert_refused_before_prepared(workspace, result, database_digest=database_before)
    assert digest(source) == source_before


def test_source_changed_result_exposes_no_absolute_path(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    accepted = expected_from_a1(workspace, source, tmp_path)
    expected = ExpectedSourceProof(
        source_identity=accepted.source_identity,
        sha256="f" * 64,
    )
    context = workspace.context()
    try:
        result = run_bound(workspace, source, expected, context)
    finally:
        context.release()

    assert result.failure is RestoreFailure.SOURCE_CHANGED
    assert str(source) not in result.message
    assert source.name not in result.message
    assert "SQLite" not in result.message
    assert "SQL" not in result.message


def test_legacy_c4_i_request_without_expected_proof_is_behaviorally_unchanged(
    monkeypatch, tmp_path
):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        result = execute_restore(
            request_for(source),
            context,
            services=stub_services(workspace.database_path),
        )
    finally:
        context.release()

    assert result.restore_succeeded is True
    assert read_marker(workspace.database_path) == "workspace-B"
