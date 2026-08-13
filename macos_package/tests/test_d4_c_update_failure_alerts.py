from types import SimpleNamespace

import pytest

from app.services.update_safety import (
    SAFE_MIGRATION_FAILURE,
    SAFE_RECONCILIATION_FAILURE,
    UpdatePostCommitError,
    UpdateSafetyError,
)
from launcher import runtime
from macos_package import entrypoint
from macos_package.user_alert import DATA_UNCHANGED_SENTENCE, PRE_MUTATION_FAILURES, STARTUP_FAILURE_MESSAGES, StartupFailure


@pytest.mark.parametrize(
    ('error', 'failure', 'exit_code'),
    [
        (UpdateSafetyError('secret-precommit-category', SAFE_MIGRATION_FAILURE), StartupFailure.UPDATE_STOPPED_BEFORE_COMMIT, entrypoint.EXIT_UPDATE_STOPPED_BEFORE_COMMIT),
        (UpdateSafetyError('secret-ambiguous-category', SAFE_RECONCILIATION_FAILURE), StartupFailure.UPDATE_COMPLETION_UNCERTAIN, entrypoint.EXIT_UPDATE_COMPLETION_UNCERTAIN),
        (UpdatePostCommitError('secret-postcommit-category'), StartupFailure.UPDATE_COMPLETION_UNCERTAIN, entrypoint.EXIT_UPDATE_COMPLETION_UNCERTAIN),
        (UpdateSafetyError('future-committed-category', SAFE_MIGRATION_FAILURE, committed=True), StartupFailure.UPDATE_COMPLETION_UNCERTAIN, entrypoint.EXIT_UPDATE_COMPLETION_UNCERTAIN),
    ],
)
def test_packaged_update_failures_use_fixed_d4c_catalog(monkeypatch, error, failure, exit_code):
    captured = []
    monkeypatch.setattr(runtime, 'run_local_runtime', lambda _config: (_ for _ in ()).throw(error))
    monkeypatch.setattr(entrypoint, 'report_startup_failure', lambda kind, *, packaged, detail=None: captured.append((kind, packaged, detail)))
    layout = SimpleNamespace(is_packaged=True)
    server = SimpleNamespace(origin='http://127.0.0.1:5173')
    arguments = SimpleNamespace(backend_port=8000, no_browser=True)

    assert entrypoint._run_launcher(layout, server, arguments) == exit_code
    assert captured == [(failure, True, 'D4-C classified startup-owned update failure')]
    message = STARTUP_FAILURE_MESSAGES[failure]
    for forbidden in ('secret-', '/Users/', 'traceback', 'schema_identity', 'operation_id'):
        assert forbidden not in message
    assert DATA_UNCHANGED_SENTENCE not in message
    assert failure not in PRE_MUTATION_FAILURES


def test_precommit_message_claim_is_bounded_to_database_commit_point():
    message = STARTUP_FAILURE_MESSAGES[StartupFailure.UPDATE_STOPPED_BEFORE_COMMIT]
    assert 'до замены рабочей базы данных' in message
    assert DATA_UNCHANGED_SENTENCE not in message


def test_uncertain_message_never_suggests_manual_rollback():
    message = STARTUP_FAILURE_MESSAGES[StartupFailure.UPDATE_COMPLETION_UNCERTAIN]
    assert 'Не удалось подтвердить завершение обновления данных' in message
    assert 'Не пытайтесь вручную откатывать' in message
