"""The exact twelve-phase Restore lifecycle accepted by `CR-010`.

Authoritative contract: ``docs/decisions/0016-launcher-assisted-restore.md``
§ 7.1 and § 7.2, mirrored operationally in ``docs/backup-and-restore.md`` § 7.

`phase` is the **sole authoritative lifecycle field**. Whether database
replacement happened and whether rollback completed are *derived* from it and
are never persisted as independent booleans, because two independently written
flags can disagree after a crash and the recovery decision would then have no
single source of truth.

This module owns the vocabulary and the transition graph and nothing else. It
performs no I/O, so the graph can be tested exhaustively without a filesystem.
"""

from __future__ import annotations

from enum import Enum


class RestorePhase(str, Enum):
    """Exactly twelve phases. No alias, no synonym, no additional phase."""

    PREPARED = "prepared"
    SOURCE_STAGED = "source_staged"
    CANDIDATE_VALIDATED = "candidate_validated"
    SAFETY_COPY_VERIFIED = "safety_copy_verified"
    REPLACEMENT_INTENT = "replacement_intent"
    REPLACEMENT_COMMITTED = "replacement_committed"
    VERIFICATION_IN_PROGRESS = "verification_in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"
    ROLLBACK_IN_PROGRESS = "rollback_in_progress"
    ROLLED_BACK = "rolled_back"
    RECOVERY_BLOCKED = "recovery_blocked"


# The complete authorized transition graph of ADR 0016 § 7.2, written out rather
# than derived. A derived graph would encode the reviewer's model of the rules;
# this one *is* the rules, and a diff against the ADR is a literal comparison.
ALLOWED_TRANSITIONS: dict[RestorePhase, frozenset[RestorePhase]] = {
    RestorePhase.PREPARED: frozenset({RestorePhase.SOURCE_STAGED, RestorePhase.ABORTED}),
    RestorePhase.SOURCE_STAGED: frozenset(
        {RestorePhase.CANDIDATE_VALIDATED, RestorePhase.ABORTED}
    ),
    RestorePhase.CANDIDATE_VALIDATED: frozenset(
        {RestorePhase.SAFETY_COPY_VERIFIED, RestorePhase.ABORTED}
    ),
    RestorePhase.SAFETY_COPY_VERIFIED: frozenset(
        {RestorePhase.REPLACEMENT_INTENT, RestorePhase.ABORTED}
    ),
    RestorePhase.REPLACEMENT_INTENT: frozenset(
        {RestorePhase.REPLACEMENT_COMMITTED, RestorePhase.ROLLBACK_IN_PROGRESS}
    ),
    RestorePhase.REPLACEMENT_COMMITTED: frozenset(
        {RestorePhase.VERIFICATION_IN_PROGRESS, RestorePhase.ROLLBACK_IN_PROGRESS}
    ),
    RestorePhase.VERIFICATION_IN_PROGRESS: frozenset(
        {RestorePhase.COMPLETED, RestorePhase.ROLLBACK_IN_PROGRESS}
    ),
    RestorePhase.ROLLBACK_IN_PROGRESS: frozenset(
        {RestorePhase.ROLLED_BACK, RestorePhase.RECOVERY_BLOCKED}
    ),
    RestorePhase.COMPLETED: frozenset(),
    RestorePhase.ABORTED: frozenset(),
    RestorePhase.ROLLED_BACK: frozenset(),
    RestorePhase.RECOVERY_BLOCKED: frozenset(),
}

TERMINAL_PHASES: frozenset[RestorePhase] = frozenset(
    {
        RestorePhase.COMPLETED,
        RestorePhase.ABORTED,
        RestorePhase.ROLLED_BACK,
        RestorePhase.RECOVERY_BLOCKED,
    }
)

# The phases that must not fall through to ordinary startup. Derived from the
# recovery matrix of ADR 0016 § 7.5 and used by both the engine and startup
# recovery, so the two cannot disagree about what "unsafe" means.
UNSAFE_STARTUP_PHASES: frozenset[RestorePhase] = frozenset(
    {
        RestorePhase.REPLACEMENT_INTENT,
        RestorePhase.REPLACEMENT_COMMITTED,
        RestorePhase.VERIFICATION_IN_PROGRESS,
        RestorePhase.ROLLBACK_IN_PROGRESS,
        RestorePhase.RECOVERY_BLOCKED,
    }
)

# The phases from which the accepted matrix requires rollback rather than an
# abort. Membership is the *only* replacement-happened signal in the system: a
# persisted `replacement_intent` is treated as though replacement may have
# occurred, and no filesystem appearance may override that.
ROLLBACK_REQUIRED_PHASES: frozenset[RestorePhase] = frozenset(
    {
        RestorePhase.REPLACEMENT_INTENT,
        RestorePhase.REPLACEMENT_COMMITTED,
        RestorePhase.VERIFICATION_IN_PROGRESS,
    }
)

# Failure before the replacement boundary ends the operation without touching the
# working database.
ABORTABLE_PHASES: frozenset[RestorePhase] = frozenset(
    {
        RestorePhase.PREPARED,
        RestorePhase.SOURCE_STAGED,
        RestorePhase.CANDIDATE_VALIDATED,
        RestorePhase.SAFETY_COPY_VERIFIED,
    }
)


class PhaseTransitionError(RuntimeError):
    """Raised when an unauthorized lifecycle transition is attempted.

    Deliberately loud rather than tolerant. An unauthorized transition means the
    orchestration has diverged from the accepted state machine, and continuing
    from a phase the recovery matrix does not expect is precisely the failure
    mode the machine exists to prevent.
    """


def is_terminal(phase: RestorePhase) -> bool:
    return phase in TERMINAL_PHASES


def is_allowed_transition(current: RestorePhase, target: RestorePhase) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def require_allowed_transition(current: RestorePhase, target: RestorePhase) -> None:
    """Refuse anything the accepted graph does not authorize.

    A terminal record is never reactivated: `ALLOWED_TRANSITIONS` gives every
    terminal phase an empty successor set, so this refuses without a rule of its
    own. A new attempt is a new operation with a new operation ID.
    """
    if not is_allowed_transition(current, target):
        raise PhaseTransitionError(
            f"Restore phase transition {current.value} -> {target.value} is not authorized."
        )


def requires_rollback(phase: RestorePhase) -> bool:
    """Whether the accepted recovery matrix requires rollback from this phase."""
    return phase in ROLLBACK_REQUIRED_PHASES


def permits_ordinary_startup(phase: RestorePhase) -> bool:
    """Whether ordinary backend startup may proceed with this phase persisted.

    Only meaningful for a phase that has already been resolved by startup
    recovery: an unresolved `prepared` is safe for the *database* but the
    operation still has to be moved to `aborted` first, which is recovery's job.
    """
    return phase not in UNSAFE_STARTUP_PHASES
