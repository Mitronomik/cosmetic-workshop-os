"""The complete startup recovery matrix, resolved before ordinary startup.

`CR-010` § 7.5. Every one of the twelve phases has exactly one required
behaviour, and this module implements that table — not an equivalent of its own
choosing. An interrupted Restore may never be ignored, and no unsafe phase may
fall through to ordinary startup, startup migrations or the browser.

The four groups:

| Phases | Behaviour |
|---|---|
| `prepared`, `source_staged`, `candidate_validated`, `safety_copy_verified` | Never replaced anything. Transition to `aborted`, clean only owned staging and the one owned replacement artifact, allow normal startup. A verified safety copy is retained. |
| `replacement_intent`, `replacement_committed`, `verification_in_progress` | Block startup. Durably enter `rollback_in_progress`, restore and verify the safety copy, end at `rolled_back` or `recovery_blocked`. |
| `rollback_in_progress` | Block startup. Continue or safely repeat the rollback. |
| `completed`, `aborted`, `rolled_back` | Terminal and safe. Confirm the record is readable, retain the safety copy, clean only owned staging, allow normal startup. |
| `recovery_blocked` | Nothing starts. All evidence preserved. One fixed non-technical result. |

Two things are never done here. A record that exists but cannot be read is **not**
treated as "no operation" — that is the one case where the launcher knows
something happened and cannot tell what, and the accepted answer is
`recovery_blocked`, not an optimistic start. And no transition outside the
accepted graph is ever attempted: when a required transition cannot be published,
the **actual** durable phase is reported and ordinary startup is blocked, so the
next launcher start resumes from reality.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

from launcher.restore.context import LauncherLifecycleContext, RestoreLifecycleError
from launcher.restore.contracts import (
    BACKEND_PORT_UNAVAILABLE_MESSAGE,
    COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE,
    RECOVERY_BLOCKED_MESSAGE,
    ROLLED_BACK_MESSAGE,
    RecoveryResult,
    RestoreOutcome,
)
from launcher.restore.engine import RestoreServices, perform_rollback
from launcher.restore.phases import (
    ABORTABLE_PHASES,
    ROLLBACK_REQUIRED_PHASES,
    SAFE_TERMINAL_STARTUP_PHASES,
    RestorePhase,
    permits_ordinary_startup,
)
from launcher.restore.replacement import discard_owned_replacement_artifact
from launcher.restore.state import (
    RestoreOperationRecord,
    RestoreOperationStateStore,
    RestoreStateError,
)
from launcher.restore.verification import RetryableBackendStartError
from launcher.restore.workspace import RestoreWorkspaceError

logger = logging.getLogger(__name__)


def _confirm_record_durability(store: RestoreOperationStateStore) -> bool:
    """Re-prove the existing record's durability, changing nothing.

    Called before ordinary startup is allowed from any terminal phase. It is the
    same retry the engine performs after a post-rename flush failure, and the
    reason both do it is the same: a phase that is visible but unflushed can
    disappear across a host interruption, and startup must not depend on a value
    that might not be there afterwards.
    """
    try:
        store.confirm_record_durability()
    except RestoreStateError as exc:
        logger.error("Operation record durability could not be confirmed: %s", exc)
        return False
    return True


def _allowed(
    phase: RestorePhase, operation_id: str | None, outcome: RestoreOutcome
) -> RecoveryResult:
    """Permit ordinary startup, through the one shared positive rule.

    The `assert` is a guard against this function being called from a branch that
    has not established both conditions. Startup permission is decided in exactly
    one place, and reaching here with anything else is a programming error rather
    than a state to report.
    """
    assert permits_ordinary_startup(
        phase, record_exists=True, durability_confirmed=True
    ), f"ordinary startup is not permitted from {phase.value}"
    return RecoveryResult(
        normal_startup_allowed=True,
        durable_phase=phase,
        outcome=outcome,
        operation_id=operation_id,
    )


def _blocked_result(
    phase: RestorePhase | None, operation_id: str | None, message: str
) -> RecoveryResult:
    """Block ordinary startup, reporting the phase that is actually on disk.

    `phase` is never the phase this run *wanted* to reach. When a transition
    could not be published it is the pre-transition phase that really remains, so
    the next launcher start resolves the same real state through the same matrix.
    """
    return RecoveryResult(
        normal_startup_allowed=False,
        durable_phase=phase,
        outcome=RestoreOutcome.RECOVERY_BLOCKED,
        operation_id=operation_id,
        message=message,
    )


def _blocked_by_backend_liveness(store: RestoreOperationStateStore) -> RecoveryResult:
    """Block startup because another backend owns this workspace.

    Reads the record purely to *report* the phase that is really there — it is
    never transitioned, rewritten or cleaned, and a record that will not parse
    simply reports no phase. Works identically whether an interrupted Restore
    exists or not: with no record, the orphan alone is reason enough to refuse,
    because ordinary startup would put a second writer on one SQLite database.
    """
    phase = None
    operation_id = None
    try:
        record = store.read()
    except RestoreStateError:
        record = None
    if record is not None:
        phase = record.phase
        operation_id = record.operation_id
    return _blocked_result(phase, operation_id, RECOVERY_BLOCKED_MESSAGE)


def _deferred_by_port(
    store: RestoreOperationStateStore, record: RestoreOperationRecord
) -> RecoveryResult:
    """Refuse this run only, reporting the phase that really — and still — remains.

    Startup is blocked, so the browser stays closed and no backend starts. What
    makes this different from every other blocked result is that **nothing was
    written to reach it**: no transition, no cleanup, no replacement. The record
    on disk is byte-identical to what the interrupted operation left, and the
    phase reported here is that phase.

    The record is re-read rather than trusted, for the same reason every other
    reporting path re-reads: what is on disk is the only authority, and if it has
    somehow become unreadable that is a genuinely blocked recovery rather than a
    busy port.
    """
    try:
        actual = store.read()
    except RestoreStateError:
        logger.error("The operation record became unreadable while recovery was deferred.")
        return _blocked_result(None, None, RECOVERY_BLOCKED_MESSAGE)
    live = actual if actual is not None else record
    return RecoveryResult(
        normal_startup_allowed=False,
        durable_phase=live.phase,
        # No `outcome`: the operation did not reach one. It is exactly where it
        # was, waiting for the next launch.
        operation_id=live.operation_id,
        message=BACKEND_PORT_UNAVAILABLE_MESSAGE,
    )


def _clean_non_destructive_artifacts(workspace, context, operation_id: str) -> None:
    """Remove only what this operation provably owns.

    The staged candidate lives in this operation's own directory; the replacement
    artifact has one deterministic name derived from the operation ID. Neither
    lookup lists a directory looking for things to delete, which is what keeps
    cleanup from ever reaching a file beside the user's database that the
    launcher did not create.
    """
    try:
        workspace.clean_owned_staging(operation_id)
        workspace.clean_owned_temp_files()
    except RestoreWorkspaceError:
        return
    discard_owned_replacement_artifact(context.database_path, operation_id)


@dataclass(frozen=True)
class RestoreStartupPreflight:
    """Everything startup recovery can establish **without changing anything**.

    The fifth-audit finding this exists for: the launcher had to resolve Restore
    before the port check, because a real orphan holds the canonical lock *and*
    the configured port. But full recovery *mutates* — it aborts pre-replacement
    operations, enters `rollback_in_progress`, replaces the working database from
    the safety copy and runs migrations. Doing all of that and only then
    discovering that an unrelated program owns the port meant a temporary
    environment problem could end a recoverable operation at terminal
    `recovery_blocked`.

    So the two halves are separated. This half establishes **exclusion and facts**:

    ```text
    the launcher's authority is held
    any launcher-owned child is stopped
    the retained maintenance lease is taken   ← exclusion, from here on
    a foreign/orphan backend is detected
    the authoritative record is read          ← read only
    ```

    and nothing else. No phase is transitioned, no operation is created, no
    rollback is entered, no database is replaced, no staging is cleaned, no
    migration runs and no verification backend starts. The launcher can therefore
    check the port between this and full recovery, and refuse an ordinary
    collision with the Restore history byte-identical.

    `blocked_result` is non-`None` when startup is already refused on grounds the
    port cannot change: an orphan holding the canonical lock, an unreadable
    authoritative record, or a durable `recovery_blocked`. Those are answered
    before the port is ever consulted, so a same-port orphan still gets the typed
    blocked result rather than a port-collision message.
    """

    blocked_result: RecoveryResult | None
    record: RestoreOperationRecord | None
    has_record: bool

    @property
    def startup_already_refused(self) -> bool:
        return self.blocked_result is not None

    @property
    def durable_phase(self) -> RestorePhase | None:
        return self.record.phase if self.record is not None else None


def prepare_restore_startup_recovery(
    context: LauncherLifecycleContext,
) -> RestoreStartupPreflight:
    """Establish backend exclusion and read the record. Change nothing.

    Safe to call twice: `stop_backend()` re-proves an already-proved stop and the
    maintenance lease is idempotent to acquire, so `recover_incomplete_restore`
    calls this itself when it is not handed a result. That is what keeps one
    implementation of the recovery matrix rather than two that could disagree.
    """
    context.require_authority()
    store = RestoreOperationStateStore(context.workspace)

    # Recovery runs *before* ordinary startup, so the launcher has not started a
    # backend yet — but that has to be established, not assumed. With no owned
    # handle this records the "never started" proof; if a previous run in this
    # process did start one, it is stopped here, before any rollback replacement.
    # It also takes the retained maintenance lease, which is what keeps a backend
    # from appearing during a rollback replacement further down.
    try:
        context.stop_backend()
    except RestoreLifecycleError as exc:
        # An orphaned backend from a hard launcher crash still holds the liveness
        # lock, so the lease cannot be taken. That is an **expected** condition of
        # this gate, not a fault in it: the accepted answer is a blocked startup,
        # and the caller is `run_local_runtime`, which branches on a
        # `RecoveryResult`. Letting the lifecycle error escape instead would turn
        # a designed refusal into an unhandled exception and a stack trace on a
        # user's screen. Nothing is started, nothing is transitioned, the working
        # database is untouched, and the technical detail stays in the local log.
        #
        # This is decided here, before any port check, so a real orphan — which
        # holds the port as well as the lock — is reported as blocked recovery and
        # never as an ordinary port collision.
        logger.error("Startup recovery is blocked: %s", exc)
        return RestoreStartupPreflight(
            blocked_result=_blocked_by_backend_liveness(store),
            record=None,
            has_record=store.has_record(),
        )

    if not store.has_record():
        return RestoreStartupPreflight(blocked_result=None, record=None, has_record=False)

    try:
        record = store.read()
    except RestoreStateError as exc:
        # Present but unreadable. Nothing may be inferred from a record that
        # cannot be parsed, and "there is no operation" is not what this is. No
        # port is free enough to make this startable, so it is answered here.
        logger.error("Restore operation record is unreadable: %s", type(exc).__name__)
        return RestoreStartupPreflight(
            blocked_result=_blocked_result(None, None, RECOVERY_BLOCKED_MESSAGE),
            record=None,
            has_record=True,
        )
    if record is None:
        return RestoreStartupPreflight(blocked_result=None, record=None, has_record=False)

    if record.phase is RestorePhase.RECOVERY_BLOCKED:
        # Terminal and already blocked. Answered before the port for the same
        # reason: freeing the port would not make this startable, and the fixed
        # support sentence is the accepted result.
        logger.error("Startup blocked: a previous Restore ended in recovery_blocked.")
        return RestoreStartupPreflight(
            blocked_result=_blocked_result(
                record.phase, record.operation_id, RECOVERY_BLOCKED_MESSAGE
            ),
            record=record,
            has_record=True,
        )

    return RestoreStartupPreflight(blocked_result=None, record=record, has_record=True)


def recover_incomplete_restore(
    context: LauncherLifecycleContext,
    *,
    services: RestoreServices | None = None,
    preflight: RestoreStartupPreflight | None = None,
) -> RecoveryResult:
    """Resolve any persisted Restore operation before the backend may start.

    `context` carries the held launcher lock and the canonically derived paths,
    so recovery guards exactly the workspace ordinary startup is about to use.
    Returns a :class:`RecoveryResult` whose `normal_startup_allowed` is the only
    thing the launcher needs to branch on; `no_operation` is the ordinary case.

    **This is the state-mutating half.** `preflight` is the non-mutating half,
    already run by the launcher so the configured port could be checked in
    between; when it is not supplied this runs it, so a direct caller still gets
    the complete gate and there is only ever one recovery matrix.
    """
    active_services = services or RestoreServices()
    ready = preflight if preflight is not None else prepare_restore_startup_recovery(context)
    if ready.blocked_result is not None:
        return ready.blocked_result

    workspace = context.workspace
    store = RestoreOperationStateStore(workspace)

    # The lease is held from the preflight onwards, so the record read there is
    # still the record on disk: no backend could have started against this
    # workspace in between, and this launcher holds the instance lock.
    record = ready.record
    if record is None:
        return RecoveryResult(normal_startup_allowed=True, no_operation=True)

    phase = record.phase

    # ------------------------------------------------- terminal safe states
    if phase in SAFE_TERMINAL_STARTUP_PHASES:
        # Terminal: **no transition of any kind**, not even a self-transition.
        # Readability alone is not enough to start on, though. A terminal record
        # whose publication could not be flushed may revert across a host
        # interruption, so its durability is re-proved here — the same retry the
        # engine performs — and startup waits until that succeeds.
        if not _confirm_record_durability(store):
            logger.error(
                "The terminal Restore record could not be proved durable; "
                "startup is blocked and the next start retries."
            )
            # Startup is blocked either way, but what the user is told is not the
            # same. A `completed` record that is visible and unflushed means the
            # restored data are in place and verified and only the technical
            # finalization is unproved — nothing failed, nothing was undone and
            # nothing was lost, so it does not get the "Restore did not finish"
            # sentence. The next start retries the confirmation and, when it
            # succeeds, ordinary startup proceeds as an ordinary success.
            message = (
                COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE
                if phase is RestorePhase.COMPLETED
                else RECOVERY_BLOCKED_MESSAGE
            )
            return _blocked_result(phase, record.operation_id, message)

        # Only launcher-owned artifacts are cleaned; the safety copy is retained.
        _clean_non_destructive_artifacts(workspace, context, record.operation_id)
        if phase is RestorePhase.ROLLED_BACK:
            # Restore remains failed. Startup continues against the recovered
            # previous workspace, and the message says so rather than implying a
            # successful Restore.
            return RecoveryResult(
                normal_startup_allowed=True,
                durable_phase=phase,
                outcome=RestoreOutcome.ROLLED_BACK,
                operation_id=record.operation_id,
                message=ROLLED_BACK_MESSAGE,
            )
        outcome = (
            RestoreOutcome.COMPLETED
            if phase is RestorePhase.COMPLETED
            else RestoreOutcome.ABORTED
        )
        return _allowed(phase, record.operation_id, outcome)

    # ------------------------------------------------- pre-replacement states
    if phase in ABORTABLE_PHASES:
        # Nothing was replaced, so nothing is rolled back and the replacement is
        # never executed automatically. The operation is closed out and ordinary
        # startup continues against the existing working database.
        try:
            aborted = store.transition(record, RestorePhase.ABORTED)
        except RestoreStateError as exc:
            actual = store.read_durable_record(record)
            if actual.phase is not RestorePhase.ABORTED:
                # The abort did not stick. Nothing destructive happened, but the
                # operation is still live, so startup is blocked rather than
                # continuing past an unresolved record — and the next start sees
                # the same real phase and tries again.
                logger.error(
                    "An interrupted Restore could not be closed out; durable phase remains %s.",
                    actual.phase.value,
                )
                return _blocked_result(
                    actual.phase, actual.operation_id, RECOVERY_BLOCKED_MESSAGE
                )
            logger.warning(
                "Abort publication reported %s but the record is durable.", type(exc).__name__
            )
            aborted = actual
            # The rename landed but its flush did not. Re-prove it before letting
            # ordinary startup depend on the `aborted` value being there.
            if not _confirm_record_durability(store):
                return _blocked_result(
                    RestorePhase.ABORTED, aborted.operation_id, RECOVERY_BLOCKED_MESSAGE
                )
        _clean_non_destructive_artifacts(workspace, context, aborted.operation_id)
        return _allowed(RestorePhase.ABORTED, aborted.operation_id, RestoreOutcome.ABORTED)

    # ------------------------------------------------ rollback-required states
    if phase in ROLLBACK_REQUIRED_PHASES:
        try:
            record = store.transition(record, RestorePhase.ROLLBACK_IN_PROGRESS)
        except RestoreStateError:
            actual = store.read_durable_record(record)
            if actual.phase is not RestorePhase.ROLLBACK_IN_PROGRESS:
                # No unauthorized transition is attempted from here. The durable
                # phase stays what it is, startup is blocked, and the next
                # launcher start retries recovery from that same real phase.
                logger.error(
                    "Rollback could not be durably requested; durable phase remains %s.",
                    actual.phase.value,
                )
                return _blocked_result(
                    actual.phase, actual.operation_id, RECOVERY_BLOCKED_MESSAGE
                )
            record = actual

    # `rollback_in_progress` arrives here either from the transition above or
    # from a crash during a previous rollback. Both continue the same way, which
    # is what makes rollback safely repeatable.
    try:
        result = perform_rollback(store, record, workspace, context, active_services)
    except RetryableBackendStartError:
        # The port was free at the preflight and was taken before the verification
        # child could bind it. No momentary probe can close that race, so it is
        # *classified* instead: the durable phase stays exactly where it is,
        # nothing is published, the safety copy and staging are retained, and the
        # user is told to close the other program and reopen. `rollback_in_progress`
        # is safely repeatable, so the next launch finishes what this one could not
        # start — which is the whole difference between a busy port and a
        # workspace nothing can prove safe.
        logger.warning(
            "Startup recovery deferred: the configured port is occupied; "
            "the durable phase is unchanged and the next start resumes it."
        )
        return _deferred_by_port(store, record)

    if result.outcome is RestoreOutcome.ROLLED_BACK and result.normal_startup_allowed:
        # `perform_rollback` already applied the shared startup rule, including
        # the durability confirmation for the terminal `rolled_back` record. It is
        # carried through rather than re-derived, so there is one decision and not
        # two that could disagree.
        return RecoveryResult(
            normal_startup_allowed=True,
            durable_phase=RestorePhase.ROLLED_BACK,
            outcome=RestoreOutcome.ROLLED_BACK,
            operation_id=result.operation_id,
            message=ROLLED_BACK_MESSAGE,
        )
    return _blocked_result(
        result.durable_phase, result.operation_id, RECOVERY_BLOCKED_MESSAGE
    )
