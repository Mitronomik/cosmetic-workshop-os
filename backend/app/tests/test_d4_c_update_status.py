import json

from app.db.paths import resolve_user_data_paths
from app.services.settings import SettingsService
from app.services.update_safety import (
    SAFE_MIGRATION_FAILURE,
    SAFE_RECONCILIATION_FAILURE,
    UpdateJournalError,
    UpdateOperationRecord,
    UpdatePostCommitError,
    UpdateSafetyError,
    _write_update_journal,
    classify_update_failure_for_user,
    read_user_update_status,
    update_journal_path,
)


def record(*, status='completed', message=None):
    return UpdateOperationRecord(
        operation_id='a' * 32, from_app_version=None, to_app_version='0.1.0',
        from_schema_identity=('0001',), to_schema_identity=('0001', '0002'),
        before_migration_backup_identity='backup.sqlite', stage_identity='.db.update-' + 'a' * 32 + '.stage',
        started_at='2026-08-13T10:00:00Z', finished_at=None if status == 'started' else '2026-08-13T10:01:00Z',
        status=status, failure_category='internal-category' if status == 'failed' else None, safe_failure_message=message,
    )


def test_no_journal_is_read_only_neutral_status(monkeypatch, tmp_path):
    monkeypatch.setenv('COSMETIC_WORKSHOP_USER_DATA_DIR', str(tmp_path / 'user-data'))
    paths = resolve_user_data_paths()
    status = read_user_update_status(paths)
    assert status.state == 'not_required'
    assert status.to_app_version is None
    assert not paths.base_dir.exists()


def test_completed_and_failed_journal_project_only_safe_status(monkeypatch, tmp_path):
    monkeypatch.setenv('COSMETIC_WORKSHOP_USER_DATA_DIR', str(tmp_path / 'user-data'))
    paths = resolve_user_data_paths()
    paths.data_dir.mkdir(parents=True)
    _write_update_journal(update_journal_path(paths), [record(status='completed')])
    completed = SettingsService().build_status().update_status
    assert completed.state == 'completed'
    assert completed.to_app_version == '0.1.0'
    assert completed.next_action == 'Можно продолжать работу.'

    _write_update_journal(update_journal_path(paths), [record(status='failed', message=SAFE_MIGRATION_FAILURE)])
    failed = SettingsService().build_status().update_status
    assert failed.state == 'attention_required'
    assert failed.message == SAFE_MIGRATION_FAILURE
    serialized = failed.model_dump_json()
    for forbidden in ('operation_id', 'failure_category', 'schema_identity', 'stage_identity', 'backup_identity', 'internal-category'):
        assert forbidden not in serialized


def test_unreadable_or_started_journal_becomes_bounded_attention(monkeypatch, tmp_path):
    monkeypatch.setenv('COSMETIC_WORKSHOP_USER_DATA_DIR', str(tmp_path / 'user-data'))
    paths = resolve_user_data_paths()
    paths.data_dir.mkdir(parents=True)
    update_journal_path(paths).write_text('{broken', encoding='utf-8')
    unreadable = SettingsService().build_status().update_status
    assert unreadable.state == 'attention_required'
    assert unreadable.message == SAFE_RECONCILIATION_FAILURE

    _write_update_journal(update_journal_path(paths), [record(status='started')])
    started = SettingsService().build_status().update_status
    assert started.state == 'attention_required'
    assert started.message == SAFE_RECONCILIATION_FAILURE


def test_failure_classifier_has_only_two_user_outcomes():
    assert classify_update_failure_for_user(UpdateSafetyError('migration', SAFE_MIGRATION_FAILURE)) == 'before_commit'
    assert classify_update_failure_for_user(UpdateSafetyError('ambiguous', SAFE_RECONCILIATION_FAILURE)) == 'completion_uncertain'
    assert classify_update_failure_for_user(UpdateJournalError()) == 'completion_uncertain'
    assert classify_update_failure_for_user(UpdatePostCommitError('post-commit')) == 'completion_uncertain'
