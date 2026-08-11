"""Focused ADR 0018 replay semantics for the B2 execute command."""

from __future__ import annotations

import pytest

from launcher.restore.control_protocol import ControlSessionError
from launcher.restore.control_session import RestoreControlSession
from launcher.restore.validation_session import RestoreCandidatePreparationService
from launcher.tests.restore_fixtures import build_workspace_database


def request_id(number: int) -> str:
    return f"{number:032x}"


def test_execute_business_refusal_consumes_sequence_and_preserves_exact_replay(tmp_path):
    database = build_workspace_database(tmp_path / "workshop.sqlite", "workspace-A")
    service = RestoreCandidatePreparationService(
        database,
        scratch_root=tmp_path / "scratch",
        run_id="123e4567-e89b-42d3-a456-426614174222",
    )
    session = RestoreControlSession(service)
    token, _state = session.bootstrap(session.bootstrap_capability)
    try:
        refused = session.execute(
            token,
            request_id=request_id(1),
            command_seq=1,
            generation=1,
        )
        assert refused.ok is False
        assert refused.code == "candidate_not_accepted"
        assert refused.command_seq == 1

        exact_retry = session.execute(
            token,
            request_id=request_id(1),
            command_seq=1,
            generation=999,
        )
        assert exact_retry == refused

        with pytest.raises(ControlSessionError) as conflict:
            session.execute(
                token,
                request_id=request_id(2),
                command_seq=1,
                generation=1,
            )
        assert conflict.value.code == "command_sequence_conflict"

        with pytest.raises(ControlSessionError) as future:
            session.execute(
                token,
                request_id=request_id(3),
                command_seq=3,
                generation=1,
            )
        assert future.value.code == "command_sequence_future"

        next_refusal = session.execute(
            token,
            request_id=request_id(4),
            command_seq=2,
            generation=1,
        )
        assert next_refusal.code == "candidate_not_accepted"
        assert next_refusal.command_seq == 2

        with pytest.raises(ControlSessionError) as stale:
            session.execute(
                token,
                request_id=request_id(1),
                command_seq=1,
                generation=1,
            )
        assert stale.value.code == "command_sequence_stale"
    finally:
        session.close()
