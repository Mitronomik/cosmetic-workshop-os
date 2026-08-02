"""The accepted twelve-phase vocabulary and transition graph.

These tests are a literal comparison against ADR 0016 § 7.1 and § 7.2. They are
deliberately exhaustive rather than representative: the graph is a safety
contract, and an *extra* authorized edge is exactly as dangerous as a missing
one — `replacement_intent → completed` would let a crash-ambiguous replacement be
reported as success.
"""

import itertools

import pytest

from launcher.restore.phases import (
    ABORTABLE_PHASES,
    ALLOWED_TRANSITIONS,
    ROLLBACK_REQUIRED_PHASES,
    SAFE_TERMINAL_STARTUP_PHASES,
    TERMINAL_PHASES,
    UNSAFE_STARTUP_PHASES,
    PhaseTransitionError,
    RestorePhase,
    is_terminal,
    permits_ordinary_startup,
    require_allowed_transition,
    requires_rollback,
)

ACCEPTED_VOCABULARY = [
    "prepared",
    "source_staged",
    "candidate_validated",
    "safety_copy_verified",
    "replacement_intent",
    "replacement_committed",
    "verification_in_progress",
    "completed",
    "aborted",
    "rollback_in_progress",
    "rolled_back",
    "recovery_blocked",
]

ACCEPTED_TRANSITIONS = {
    ("prepared", "source_staged"),
    ("source_staged", "candidate_validated"),
    ("candidate_validated", "safety_copy_verified"),
    ("safety_copy_verified", "replacement_intent"),
    ("replacement_intent", "replacement_committed"),
    ("replacement_committed", "verification_in_progress"),
    ("verification_in_progress", "completed"),
    ("prepared", "aborted"),
    ("source_staged", "aborted"),
    ("candidate_validated", "aborted"),
    ("safety_copy_verified", "aborted"),
    ("replacement_intent", "rollback_in_progress"),
    ("replacement_committed", "rollback_in_progress"),
    ("verification_in_progress", "rollback_in_progress"),
    ("rollback_in_progress", "rolled_back"),
    ("rollback_in_progress", "recovery_blocked"),
}


def test_exactly_twelve_phases_with_the_accepted_lowercase_ascii_values():
    assert [phase.value for phase in RestorePhase] == ACCEPTED_VOCABULARY
    assert len(RestorePhase) == 12
    for phase in RestorePhase:
        assert phase.value.isascii() and phase.value.islower()


def test_the_vocabulary_has_no_aliases():
    """No two names may resolve to the same phase value."""
    values = [phase.value for phase in RestorePhase]
    assert len(set(values)) == len(values)
    assert len(RestorePhase.__members__) == len(values)


def test_the_terminal_phases_are_exactly_the_four_accepted_ones():
    assert {phase.value for phase in TERMINAL_PHASES} == {
        "completed",
        "aborted",
        "rolled_back",
        "recovery_blocked",
    }
    for phase in TERMINAL_PHASES:
        assert is_terminal(phase)
        assert ALLOWED_TRANSITIONS[phase] == frozenset()


def test_every_accepted_transition_is_authorized():
    for current, target in ACCEPTED_TRANSITIONS:
        require_allowed_transition(RestorePhase(current), RestorePhase(target))


def test_every_unauthorized_transition_is_rejected():
    """The complete complement of the accepted set, not a sample."""
    for current, target in itertools.product(RestorePhase, RestorePhase):
        if (current.value, target.value) in ACCEPTED_TRANSITIONS:
            continue
        with pytest.raises(PhaseTransitionError):
            require_allowed_transition(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        ("replacement_intent", "completed"),
        ("replacement_committed", "completed"),
        ("rollback_in_progress", "completed"),
        ("rolled_back", "completed"),
        ("aborted", "replacement_intent"),
        ("recovery_blocked", "completed"),
    ],
)
def test_the_explicitly_prohibited_transitions_are_rejected(current, target):
    """ADR 0016 § 7.2 names these individually; so does this test."""
    with pytest.raises(PhaseTransitionError):
        require_allowed_transition(RestorePhase(current), RestorePhase(target))


def test_a_terminal_record_is_never_reactivated():
    for terminal in TERMINAL_PHASES:
        for target in RestorePhase:
            with pytest.raises(PhaseTransitionError):
                require_allowed_transition(terminal, target)


def test_rollback_is_required_from_exactly_the_three_post_intent_phases():
    assert {phase.value for phase in ROLLBACK_REQUIRED_PHASES} == {
        "replacement_intent",
        "replacement_committed",
        "verification_in_progress",
    }
    for phase in RestorePhase:
        assert requires_rollback(phase) is (phase in ROLLBACK_REQUIRED_PHASES)


def test_abortable_phases_are_exactly_the_four_pre_replacement_phases():
    assert {phase.value for phase in ABORTABLE_PHASES} == {
        "prepared",
        "source_staged",
        "candidate_validated",
        "safety_copy_verified",
    }


def test_the_unsafe_phase_set_is_unchanged():
    assert {phase.value for phase in UNSAFE_STARTUP_PHASES} == {
        "replacement_intent",
        "replacement_committed",
        "verification_in_progress",
        "rollback_in_progress",
        "recovery_blocked",
    }


def test_only_three_terminal_phases_may_permit_ordinary_startup():
    """Stated positively, as an allow-list.

    The earlier rule was `phase not in UNSAFE_STARTUP_PHASES`, which reads as if
    it means the same thing and does not: it silently admitted the four
    *unresolved* pre-replacement phases. Those are safe for the database, because
    replacement never happened, and unsafe for startup, because the operation is
    still live and recovery has not closed it.
    """
    assert {phase.value for phase in SAFE_TERMINAL_STARTUP_PHASES} == {
        "completed",
        "aborted",
        "rolled_back",
    }


@pytest.mark.parametrize("phase", list(RestorePhase))
def test_every_phase_gets_its_exact_startup_permission(phase):
    permitted = permits_ordinary_startup(
        phase, record_exists=True, durability_confirmed=True
    )

    assert permitted is (phase in SAFE_TERMINAL_STARTUP_PHASES), phase.value


@pytest.mark.parametrize("phase", sorted(SAFE_TERMINAL_STARTUP_PHASES, key=lambda p: p.value))
def test_a_safe_terminal_phase_still_needs_confirmed_durability(phase):
    """A terminal record that could not be flushed may revert; startup waits."""
    assert (
        permits_ordinary_startup(phase, record_exists=True, durability_confirmed=False)
        is False
    )


def test_no_record_permits_ordinary_startup():
    """The ordinary case: no Restore was ever attempted here."""
    assert (
        permits_ordinary_startup(None, record_exists=False, durability_confirmed=False)
        is True
    )


def test_an_unreadable_record_never_permits_startup():
    """`None` phase with a record present means "I cannot tell what happened"."""
    assert (
        permits_ordinary_startup(None, record_exists=True, durability_confirmed=True)
        is False
    )


def test_the_graph_covers_every_phase_exactly_once():
    """No phase may be missing from the graph, and none may be invented."""
    assert set(ALLOWED_TRANSITIONS) == set(RestorePhase)
