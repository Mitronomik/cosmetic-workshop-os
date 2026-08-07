"""A2 bootstrap/session secret-size and run-scope contract."""

from __future__ import annotations

import base64

from launcher.restore.control_session import (
    BOOTSTRAP_RANDOM_BYTES,
    SESSION_RANDOM_BYTES,
    RestoreControlSession,
)
from launcher.restore.validation_session import RestoreCandidatePreparationService
from launcher.tests.restore_fixtures import build_workspace_database


def _decode_urlsafe(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def test_bootstrap_and_session_tokens_are_at_least_256_bit_and_run_scoped(tmp_path):
    assert BOOTSTRAP_RANDOM_BYTES >= 32
    assert SESSION_RANDOM_BYTES >= 32

    first_db = build_workspace_database(tmp_path / "first.sqlite", "first")
    second_db = build_workspace_database(tmp_path / "second.sqlite", "second")
    first_service = RestoreCandidatePreparationService(
        first_db,
        scratch_root=tmp_path / "scratch-first",
    )
    second_service = RestoreCandidatePreparationService(
        second_db,
        scratch_root=tmp_path / "scratch-second",
    )
    first = RestoreControlSession(first_service)
    second = RestoreControlSession(second_service)
    try:
        first_bootstrap = first.bootstrap_capability
        second_bootstrap = second.bootstrap_capability
        assert len(_decode_urlsafe(first_bootstrap)) >= 32
        assert len(_decode_urlsafe(second_bootstrap)) >= 32
        assert first_bootstrap != second_bootstrap
        assert first.run_id != second.run_id

        first_token, _state = first.bootstrap(first_bootstrap)
        second_token, _state = second.bootstrap(second_bootstrap)
        assert len(_decode_urlsafe(first_token)) >= 32
        assert len(_decode_urlsafe(second_token)) >= 32
        assert first_token != second_token
        assert first.bootstrap_capability == ""
        assert second.bootstrap_capability == ""
    finally:
        first.close()
        second.close()
