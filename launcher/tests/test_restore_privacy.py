"""The privacy and error boundary of the Restore engine.

`CR-010` § 12: user-visible errors are fixed, human-readable and non-technical,
and technical detail belongs only in local logs. These tests hold that line at
the two places it can be crossed — the durable operation record and the
`RestoreResult` a future `C4-II` screen renders.
"""

import re
import sqlite3

import pytest

from launcher.restore.contracts import (
    RECOVERY_BLOCKED_MESSAGE,
    SUCCESS_MESSAGE,
    USER_SAFE_MESSAGES,
    RestoreFailure,
    RestoreResult,
)
from launcher.restore.engine import execute_restore
from launcher.restore.phases import RestorePhase

from launcher.tests.restore_fixtures import (
    failing_verifier,
    make_source_backup,
    make_workspace,
    request_for,
    stub_services,
)

# Anything that looks like a filesystem path, a SQL fragment or a traceback.
TECHNICAL_PATTERNS = [
    re.compile(r"/"),
    re.compile(r"\\"),
    re.compile(r"\bSELECT\b", re.IGNORECASE),
    re.compile(r"\bPRAGMA\b", re.IGNORECASE),
    re.compile(r"\bsqlite3?\b", re.IGNORECASE),
    re.compile(r"Traceback"),
    re.compile(r"\b\d{4}_[a-z_]+\b"),  # a migration ID
]


def assert_user_safe(message: str) -> None:
    assert message and message.strip() == message
    for pattern in TECHNICAL_PATTERNS:
        assert not pattern.search(message), f"{pattern.pattern!r} leaked into: {message}"


# --------------------------------------------------------------------------
# The fixed message vocabulary
# --------------------------------------------------------------------------

def test_every_failure_category_has_a_fixed_non_technical_russian_message():
    assert set(USER_SAFE_MESSAGES) == set(RestoreFailure)
    for failure, message in USER_SAFE_MESSAGES.items():
        assert_user_safe(message)
        assert re.search(r"[А-Яа-яЁё]", message), f"{failure.value} is not Russian"


def test_the_success_and_blocked_messages_are_fixed_and_non_technical():
    assert_user_safe(SUCCESS_MESSAGE)
    assert_user_safe(RECOVERY_BLOCKED_MESSAGE)
    assert RECOVERY_BLOCKED_MESSAGE == USER_SAFE_MESSAGES[RestoreFailure.RECOVERY_BLOCKED]


def test_the_recovery_blocked_message_points_at_support_without_technical_detail():
    assert "поддержк" in RECOVERY_BLOCKED_MESSAGE
    assert_user_safe(RECOVERY_BLOCKED_MESSAGE)


def test_the_error_categories_cover_the_accepted_boundary_set():
    """The complete closed vocabulary. Categories, never free text.

    Two of these describe conditions that are not failures of the *Restore*, and
    they exist precisely so those conditions stop borrowing another category's
    sentence: `preparation_not_published` is an attempt that never started over a
    record belonging to a previous operation, and
    `completion_durability_unconfirmed` is a `completed` whose flush could not be
    proved — restored, verified, in place, and not rolled back.

    Neither adds a lifecycle phase. `phase` remains the sole authoritative field;
    a category only decides which fixed sentence is rendered.
    """
    assert {failure.value for failure in RestoreFailure} == {
        "source_rejected",
        "candidate_invalid",
        "unsupported_schema",
        "insufficient_disk_space",
        "safety_copy_failed",
        "launcher_already_running",
        "replacement_failed",
        "verification_failed_rolled_back",
        "recovery_blocked",
        "preparation_not_published",
        "completion_durability_unconfirmed",
    }


# --------------------------------------------------------------------------
# Results carry no technical detail
# --------------------------------------------------------------------------

@pytest.fixture
def scenario(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        yield workspace, source, context
    finally:
        context.release()


def run(workspace, source, context, **overrides):
    return execute_restore(
        request_for(source),
        context,
        services=stub_services(workspace.database_path, **overrides),
    )


def test_a_successful_result_exposes_no_path(scenario, tmp_path):
    workspace, source, context = scenario

    result = run(workspace, source, context)

    assert_user_safe(result.message)
    assert str(tmp_path) not in repr(result)
    assert "/" not in (result.safety_copy_filename or "")
    assert "/" not in (result.staged_candidate_filename or "")


def test_a_rejected_source_result_never_names_the_selected_path(scenario, tmp_path):
    workspace, _source, context = scenario
    secret = tmp_path / "Клиенты" / "личное.sqlite"

    result = execute_restore(
        request_for(secret),
        context,
        services=stub_services(workspace.database_path),
    )

    assert_user_safe(result.message)
    assert "личное" not in repr(result)
    assert str(tmp_path) not in repr(result)


def test_a_rolled_back_result_carries_no_technical_reason(scenario):
    workspace, source, context = scenario

    result = run(workspace, source, context, verify=failing_verifier("uvicorn refused: sqlite3 locked"))

    assert_user_safe(result.message)
    assert "uvicorn" not in result.message
    assert "sqlite3" not in result.message


def test_the_result_type_has_no_field_a_stack_trace_could_ride_in_on():
    assert set(RestoreResult.__dataclass_fields__) == {
        "outcome",
        "durable_phase",
        "operation_id",
        "message",
        "normal_startup_allowed",
        "failure",
        "safety_copy_filename",
        "staged_candidate_filename",
    }


def test_rolled_back_is_never_reported_as_a_successful_restore(scenario):
    workspace, source, context = scenario

    result = run(workspace, source, context, verify=failing_verifier())

    assert result.restore_succeeded is False
    assert result.working_database_replaced is False
    assert result.durable_phase is RestorePhase.ROLLED_BACK
    assert result.message != SUCCESS_MESSAGE


# --------------------------------------------------------------------------
# The durable record carries no business data
# --------------------------------------------------------------------------

def test_no_client_recipe_or_order_data_reaches_the_operation_record(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    # Recognizable fake business data in both databases.
    for database in (workspace.database_path, source):
        connection = sqlite3.connect(database)
        try:
            connection.execute(
                "INSERT INTO clients (full_name, notes) VALUES ('Демо Клиент', 'Демо заметка')"
            )
            connection.commit()
        finally:
            connection.close()

    context = workspace.context()
    try:
        run(workspace, source, context)
    finally:
        context.release()

    serialized = (workspace.restore_dir / "operation.json").read_text(encoding="utf-8")
    assert "Демо Клиент" not in serialized
    assert "clients" not in serialized
    assert str(tmp_path) not in serialized
