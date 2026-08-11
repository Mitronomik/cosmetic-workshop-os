"""C4-II-B2 integration of the coordinator with the real C4-I intake."""

from __future__ import annotations

import hashlib
from pathlib import Path

from launcher.restore.contracts import ExpectedSourceProof, RestoreFailure
from launcher.restore.control_protocol import ControlViewState
from launcher.restore.engine import execute_restore
from launcher.restore.execution_coordinator import (
    RestoreExecutionIntent,
    execute_restore_intent,
)
from launcher.restore.state import RestoreOperationStateStore
from launcher.restore.validation_session import RestoreCandidatePreparationService
from launcher.restore.workspace import RestoreWorkspace
from launcher.tests.restore_fixtures import (
    make_source_backup,
    make_workspace,
    read_marker,
    stub_services,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_source_changed_real_c4i_refusal_restarts_without_working_db_mutation(
    monkeypatch, tmp_path
):
    """B2 restart handoff must preserve a real B1 pre-prepared refusal."""

    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    service = RestoreCandidatePreparationService(
        workspace.database_path,
        scratch_root=tmp_path / "validation-scratch",
        run_id="123e4567-e89b-42d3-a456-426614174111",
    )
    try:
        prepared = service.prepare_restore_candidate(source)
        assert prepared.accepted
        retained = service.retained_proof
        assert retained is not None
        expected = ExpectedSourceProof(
            source_identity=retained.source_identity,
            sha256=retained.sha256,
        )
    finally:
        service.close()

    # Same path, changed content after A1: B1/C4-I must refuse before `prepared`.
    payload = source.read_bytes()
    marker_offset = payload.find(b"workspace-B")
    assert marker_offset >= 0
    with source.open("r+b") as stream:
        stream.seek(marker_offset)
        stream.write(b"workspace-C")

    before_digest = _digest(workspace.database_path)
    context = workspace.context()
    starts: list[Path] = []

    def fake_start(_config, _paths, database_path: Path):
        starts.append(Path(database_path))
        return object()

    monkeypatch.setattr(context.backend, "start", fake_start)

    published: list[tuple[ControlViewState, str, str | None]] = []

    def publish(_intent, *, state, message, failure):
        published.append((state, message, failure))
        return True

    intent = RestoreExecutionIntent(
        run_id="123e4567-e89b-42d3-a456-426614174111",
        request_id="1" * 32,
        command_seq=2,
        generation=1,
        selected_source=source.resolve(),
        expected_source_proof=expected,
    )

    def real_c4i(request, passed_context):
        return execute_restore(
            request,
            passed_context,
            services=stub_services(workspace.database_path),
        )

    try:
        process = execute_restore_intent(
            intent,
            context,
            context.config,
            context.paths,
            publish,
            execute_restore_fn=real_c4i,
        )

        assert process is not None
        assert starts == [context.database_path]
        assert published[-1][0] is ControlViewState.RESTORE_FAILED
        assert published[-1][2] == RestoreFailure.SOURCE_CHANGED.value
        assert read_marker(workspace.database_path) == "workspace-A"
        assert _digest(workspace.database_path) == before_digest
        assert workspace.safety_copies() == []
        store = RestoreOperationStateStore(
            RestoreWorkspace(
                restore_dir=workspace.restore_dir,
                database_path=workspace.database_path,
            )
        )
        assert store.read() is None
    finally:
        context.release()
