"""A visible-but-unconfirmed `completed` is described truthfully.

The window is narrow and specific. Replacement committed, verification passed
twice, `completed` was renamed into place — and only the flush that would make
that rename survive a host interruption could not be proved. What is true then:

```text
the restored data are in place        the replacement committed
they were verified                    two full backend cycles passed
`completed` is visible on disk        the rename landed
nothing was rolled back               there was nothing to roll back from
nothing was lost                      every artifact is preserved
startup waits                         until the confirmation succeeds
```

The finding: the message said *"Восстановление не завершилось. Возвращены
предыдущие данные мастерской."* — the rollback sentence. It claims two things
that did not happen: a rollback, and a return to the previous data. The restored
workspace is authoritative and stays authoritative; the user would have been told
their new data were gone.

So this window gets one fixed category of its own. It is **not** a phase and not
a transition: `phase` stays `completed`, the sole authoritative lifecycle field.
Only the sentence changes, and the next start retries the confirmation.
"""

import pytest

from launcher.restore import durability
from launcher.restore.contracts import (
    COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE,
    RECOVERY_BLOCKED_MESSAGE,
    RestoreFailure,
    RestoreOutcome,
    USER_SAFE_MESSAGES,
)
from launcher.restore.engine import execute_restore
from launcher.restore.phases import RestorePhase
from launcher.restore.recovery import recover_incomplete_restore
from launcher.restore.state import RestoreOperationStateStore, RestoreStateError
from launcher.restore.workspace import RestoreWorkspace

from launcher.tests.restore_fixtures import (
    make_source_backup,
    make_workspace,
    read_marker,
    request_for,
    stub_services,
)

# Wording that would be a lie in this window. Checked as substrings of the fixed
# Russian message, because the defect was a *sentence*, not a category.
ROLLBACK_WORDING = (
    "Возвращены предыдущие данные",
    "предыдущие данные мастерской",
    "не завершилось",
)


def store_for(workspace) -> RestoreOperationStateStore:
    return RestoreOperationStateStore(
        RestoreWorkspace.for_database(workspace.database_path)
    )


def refuse_confirmation(monkeypatch):
    """Make the durability re-proof fail, leaving `completed` visible."""
    monkeypatch.setattr(
        RestoreOperationStateStore,
        "confirm_record_durability",
        lambda _self: (_ for _ in ()).throw(
            RestoreStateError("durability cannot be proved", published=True)
        ),
    )


@pytest.fixture
def scenario(monkeypatch, tmp_path):
    workspace = make_workspace(monkeypatch, tmp_path, marker="workspace-A")
    source = make_source_backup(tmp_path, "workspace-B")
    context = workspace.context()
    try:
        yield workspace, source, context
    finally:
        context.release()


# --------------------------------------------------------------------------
# The message itself
# --------------------------------------------------------------------------

def test_the_message_states_only_what_is_known():
    message = USER_SAFE_MESSAGES[RestoreFailure.COMPLETION_DURABILITY_UNCONFIRMED]

    assert message == COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE
    # It says the data were restored and verified.
    assert "Данные восстановлены и проверены" in message
    # It says what actually failed, without naming a technical cause.
    assert "не удалось безопасно завершить служебную фиксацию" in message
    # It tells the user what to do, and that retrying is the whole fix.
    assert "откройте приложение" in message
    assert "Все данные сохранены" in message
    assert "поддержку" in message

    for lie in ROLLBACK_WORDING:
        assert lie not in message, f"the message must not claim {lie!r}"
    # Nor may it claim success, nor loss.
    assert "Восстановление завершено" not in message
    assert "потеря" not in message.lower()
    assert "утерян" not in message.lower()


def test_the_message_is_not_the_recovery_blocked_message():
    """Blocked is blocked; it is not the same thing as *failed*."""
    assert COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE != RECOVERY_BLOCKED_MESSAGE
    assert (
        COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE
        != USER_SAFE_MESSAGES[RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK]
    )


def test_the_message_carries_no_technical_detail():
    from launcher.tests.test_restore_privacy import assert_user_safe

    assert_user_safe(COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE)


# --------------------------------------------------------------------------
# The engine reaches it
# --------------------------------------------------------------------------

def test_an_unconfirmed_completed_uses_the_truthful_message(scenario, monkeypatch):
    workspace, source, context = scenario

    # `completed` publishes, and only the flush after the rename fails — the exact
    # window: visible on disk, durability unproved.
    real_flush = durability.flush_directory
    state = {"completed": False}

    def flush_directory(path, **kwargs):
        if state["completed"]:
            raise OSError("injected directory flush failure")
        return real_flush(path, **kwargs)

    real_transition = RestoreOperationStateStore.transition

    def transition(self, record, target, **kwargs):
        if target is RestorePhase.COMPLETED:
            state["completed"] = True
        return real_transition(self, record, target, **kwargs)

    monkeypatch.setattr(durability, "flush_directory", flush_directory)
    monkeypatch.setattr(RestoreOperationStateStore, "transition", transition)
    refuse_confirmation(monkeypatch)

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.durable_phase is RestorePhase.COMPLETED
    assert result.failure is RestoreFailure.COMPLETION_DURABILITY_UNCONFIRMED
    assert result.message == COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE
    for lie in ROLLBACK_WORDING:
        assert lie not in result.message

    # The restored workspace is authoritative and stays that way.
    assert read_marker(workspace.database_path) == "workspace-B"
    # And success is not claimed while the launcher will not act on it.
    assert result.restore_succeeded is False
    assert result.normal_startup_allowed is False


# --------------------------------------------------------------------------
# Startup recovery reaches it, and the retry resolves it
# --------------------------------------------------------------------------

def test_startup_recovery_blocks_an_unconfirmed_completed_truthfully(
    scenario, monkeypatch
):
    workspace, source, context = scenario
    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )
    assert result.outcome is RestoreOutcome.COMPLETED
    assert read_marker(workspace.database_path) == "workspace-B"

    refuse_confirmation(monkeypatch)

    recovery = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )

    assert recovery.normal_startup_allowed is False
    assert recovery.durable_phase is RestorePhase.COMPLETED
    assert recovery.message == COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE
    for lie in ROLLBACK_WORDING:
        assert lie not in recovery.message
    # Nothing was undone to say so.
    assert read_marker(workspace.database_path) == "workspace-B"
    assert store_for(workspace).read().phase is RestorePhase.COMPLETED


def test_reopening_the_application_retries_and_succeeds(scenario, monkeypatch):
    """The instruction the message gives is the one that actually works."""
    workspace, source, context = scenario
    execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    with monkeypatch.context() as unconfirmed:
        refuse_confirmation(unconfirmed)
        blocked = recover_incomplete_restore(
            context, services=stub_services(workspace.database_path)
        )
    assert blocked.normal_startup_allowed is False
    assert blocked.message == COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE

    # The next launcher start retries the confirmation, and it succeeds.
    retried = recover_incomplete_restore(
        context, services=stub_services(workspace.database_path)
    )

    assert retried.normal_startup_allowed is True
    assert retried.durable_phase is RestorePhase.COMPLETED
    assert retried.outcome is RestoreOutcome.COMPLETED
    assert retried.message is None, "an ordinary success has nothing to announce"
    assert read_marker(workspace.database_path) == "workspace-B"


def test_a_confirmed_completed_still_reports_plain_success(scenario):
    workspace, source, context = scenario

    result = execute_restore(
        request_for(source), context, services=stub_services(workspace.database_path)
    )

    assert result.failure is None
    assert result.restore_succeeded is True
    assert result.message != COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE
