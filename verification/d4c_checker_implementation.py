from pathlib import Path
p=Path('scripts/check_documentation_lifecycle.py')
t=p.read_text(encoding='utf-8')
anchor='def main() -> int:\n'
fn='''def check_d4c_implementation() -> None:
    require(D4B_SERVICE, (
        "UpdateUserStatus", "read_user_update_status",
        "classify_update_failure_for_user", "error.committed",
        "SAFE_NO_UPDATE_STATUS", "SAFE_COMPLETED_UPDATE_STATUS",
    ))
    require(D4C_SETTINGS_SCHEMA, (
        "UpdateStatusSummary", "not_required", "completed",
        "attention_required", "to_app_version", "updated_at", "next_action",
    ))
    forbid(D4C_SETTINGS_SCHEMA, (
        "operation_id", "failure_category", "schema_identity",
        "stage_identity", "backup_identity",
    ))
    require(D4C_SETTINGS_SERVICE, (
        "read_user_update_status", "Можно продолжать работу.",
        "Ничего делать не нужно.", "Закройте приложение и откройте его снова.",
    ))
    require(D4C_PACKAGE_ENTRYPOINT, (
        "_classify_update_exception", "classify_update_failure_for_user",
        "EXIT_UPDATE_STOPPED_BEFORE_COMMIT", "EXIT_UPDATE_COMPLETION_UNCERTAIN",
        "D4-C classified startup-owned update failure",
    ))
    require(D4C_USER_ALERT, (
        "UPDATE_STOPPED_BEFORE_COMMIT", "UPDATE_COMPLETION_UNCERTAIN",
        "до замены рабочей базы данных",
        "Не удалось подтвердить завершение обновления данных",
        "Не пытайтесь вручную откатывать",
    ))
    require(D4C_FRONTEND, (
        "mountSettingsUpdateStatus", "fetch('/api/settings/status')",
        "Обновление завершено", "Нужно внимание", "Что делать:",
    ))
    forbid(D4C_FRONTEND, (
        "method: 'POST'", 'method: "POST"', "method: 'PUT'",
        "method: 'PATCH'", "method: 'DELETE'", "operation_id",
        "failure_category", "schema_identity", "stage_identity", "backup_identity",
    ))
    require(D4C_BINDINGS, ("mountSettingsUpdateStatus", "data-tax-rate-section"))
    for path in (D4C_BACKEND_TEST, D4C_FRONTEND_TEST, D4C_PACKAGE_TEST):
        if not path.is_file():
            ERRORS.append(f"missing D4-C focused test: {path.relative_to(ROOT)}")
    require(D4C_BACKEND_TEST, (
        "test_no_journal_is_read_only_neutral_status",
        "test_failure_classifier_has_only_two_user_outcomes",
    ))
    require(D4C_FRONTEND_TEST, (
        "no update mutation", "caches the read for the UI session",
    ))
    require(D4C_PACKAGE_TEST, (
        "test_packaged_update_failures_use_fixed_d4c_catalog",
        "test_uncertain_message_never_suggests_manual_rollback",
    ))


'''
if t.count(anchor)!=1: raise SystemExit('checker main anchor mismatch')
t=t.replace(anchor,fn+anchor,1)
t=t.replace('    check_d4b_implementation()\n\n    if ERRORS:','    check_d4b_implementation()\n    check_d4c_implementation()\n\n    if ERRORS:',1)
t=t.replace('    print("Verified D4-C alone is authorized next; D4-D, D5 and product release readiness remain gated.")','    print("Verified D4-C is implemented but exact-head/exact-package verification and lifecycle closure remain pending.")\n    print("Verified D4-D, D5 and product release readiness remain gated.")',1)
p.write_text(t,encoding='utf-8')
