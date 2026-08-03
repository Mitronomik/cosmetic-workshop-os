"""Typed internal contracts for the launcher-owned Restore engine.

`C4-I` is internal infrastructure for a future user-facing flow (`C4-II`), so
its surface is a typed Python API rather than an endpoint, a CLI or a dict of
loose keys. Two facts drive the shapes here:

1. **The caller is trusted, the result is not private.** A future launcher screen
   will render `RestoreResult.message` directly, so that string carries no path,
   no SQL, no migration ID, no stack trace and no database content. The
   `failure` category is what code branches on; the message is what a human
   reads.
2. **`phase` is the sole authoritative lifecycle field.** The result reports the
   phase it ended on and derives everything else from it. There is no
   `replacement_happened` flag to contradict it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from launcher.restore.phases import RestorePhase


class RestoreOutcome(str, Enum):
    """The four internal outcomes a Restore attempt or recovery can reach.

    They map one-to-one onto the accepted terminal phases. `ROLLED_BACK` is a
    **failed** Restore in which the previous workspace was recovered, and no
    caller may present it as success.
    """

    COMPLETED = "completed"
    ABORTED = "aborted"
    ROLLED_BACK = "rolled_back"
    RECOVERY_BLOCKED = "recovery_blocked"


TERMINAL_PHASE_OUTCOMES: dict[RestorePhase, RestoreOutcome] = {
    RestorePhase.COMPLETED: RestoreOutcome.COMPLETED,
    RestorePhase.ABORTED: RestoreOutcome.ABORTED,
    RestorePhase.ROLLED_BACK: RestoreOutcome.ROLLED_BACK,
    RestorePhase.RECOVERY_BLOCKED: RestoreOutcome.RECOVERY_BLOCKED,
}


class RestoreFailure(str, Enum):
    """Fixed internal failure categories.

    Fixed on purpose. A free-text reason would eventually carry a SQLite message
    or a path into a screen, which is exactly what `CR-010` § 12 forbids. Every
    category maps to one fixed Russian sentence below.
    """

    SOURCE_REJECTED = "source_rejected"
    CANDIDATE_INVALID = "candidate_invalid"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    INSUFFICIENT_DISK_SPACE = "insufficient_disk_space"
    SAFETY_COPY_FAILED = "safety_copy_failed"
    LAUNCHER_ALREADY_RUNNING = "launcher_already_running"
    REPLACEMENT_FAILED = "replacement_failed"
    VERIFICATION_FAILED_ROLLED_BACK = "verification_failed_rolled_back"
    RECOVERY_BLOCKED = "recovery_blocked"
    # The new attempt never got its own `prepared` record published, so the record
    # on disk still belongs to a *previous* operation. Nothing of this attempt
    # happened, and the previous operation's outcome is not this attempt's.
    PREPARATION_NOT_PUBLISHED = "preparation_not_published"
    # `completed` is visible on disk, the restored data are in place and verified,
    # and only the flush that would make that record survive a host interruption
    # could not be proved. Nothing was rolled back and nothing was lost.
    COMPLETION_DURABILITY_UNCONFIRMED = "completion_durability_unconfirmed"
    # Not a failure of the Restore at all: the configured local port is occupied
    # by an unrelated program, so the verification backend could not bind. The
    # database was not touched, the durable phase is exactly what it was, and the
    # next launch continues from there. Kept apart from every category above
    # because an environment problem that resolves itself when the user closes
    # another program must never be reported with the vocabulary of a Restore
    # that could not be recovered.
    BACKEND_PORT_UNAVAILABLE = "backend_port_unavailable"


# The complete user-safe vocabulary. Russian, concise, non-technical: these are
# the strings a future `C4-II` screen shows unchanged.
USER_SAFE_MESSAGES: dict[RestoreFailure, str] = {
    RestoreFailure.SOURCE_REJECTED: (
        "Выбранный файл не подходит для восстановления. "
        "Выберите резервную копию, созданную приложением."
    ),
    RestoreFailure.CANDIDATE_INVALID: (
        "Резервная копия повреждена или создана не этим приложением. "
        "Данные мастерской не изменились."
    ),
    RestoreFailure.UNSUPPORTED_SCHEMA: (
        "Эта резервная копия создана более новой версией приложения. "
        "Обновите приложение и попробуйте снова."
    ),
    RestoreFailure.INSUFFICIENT_DISK_SPACE: (
        "На диске недостаточно места для безопасного восстановления. "
        "Освободите место и попробуйте снова."
    ),
    RestoreFailure.SAFETY_COPY_FAILED: (
        "Не удалось создать резервную копию текущих данных, "
        "поэтому восстановление остановлено. Данные мастерской не изменились."
    ),
    RestoreFailure.LAUNCHER_ALREADY_RUNNING: (
        "Приложение уже запущено. Закройте другое окно приложения и попробуйте снова."
    ),
    RestoreFailure.REPLACEMENT_FAILED: (
        "Восстановление не завершилось. Возвращены предыдущие данные мастерской."
    ),
    RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK: (
        "Восстановление не завершилось. Возвращены предыдущие данные мастерской."
    ),
    RestoreFailure.RECOVERY_BLOCKED: (
        "Восстановление не завершилось, и приложение не может продолжить работу "
        "автоматически. Обратитесь в поддержку — все данные сохранены."
    ),
    RestoreFailure.PREPARATION_NOT_PUBLISHED: (
        "Восстановление не началось: приложению не удалось подготовить операцию. "
        "Данные мастерской не изменились. Попробуйте снова."
    ),
    # Says only what is known. The restored data are in place and verified — so
    # this may not claim a rollback, may not say the previous data were returned,
    # and may not say anything was lost. What actually failed is the technical
    # finalization of the record, and the honest instruction is to reopen the
    # application, which retries exactly that.
    RestoreFailure.COMPLETION_DURABILITY_UNCONFIRMED: (
        "Данные восстановлены и проверены, но приложению не удалось безопасно "
        "завершить служебную фиксацию. Закройте и снова откройте приложение — "
        "проверка повторится. Все данные сохранены. "
        "Если сообщение повторится, обратитесь в поддержку."
    ),
    # A retry instruction, not a support instruction. Nothing failed and nothing
    # is stuck: another program is using the port, and the work resumes by itself
    # once it is closed. Saying "обратитесь в поддержку" here would send a user to
    # support over something they can fix in ten seconds, and would imply a
    # damaged Restore that does not exist.
    RestoreFailure.BACKEND_PORT_UNAVAILABLE: (
        "Локальный порт приложения сейчас занят другой программой. "
        "Закройте её и снова откройте приложение. "
        "Данные сохранены, восстановление продолжится автоматически."
    ),
}

SUCCESS_MESSAGE = "Восстановление завершено. Приложение работает с восстановленными данными."

ROLLED_BACK_MESSAGE = USER_SAFE_MESSAGES[RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK]

# The one fixed non-technical sentence shown when nothing can be proved safe.
RECOVERY_BLOCKED_MESSAGE = USER_SAFE_MESSAGES[RestoreFailure.RECOVERY_BLOCKED]

# Startup is blocked, but *not* because anything failed or was undone. Kept
# separate from `RECOVERY_BLOCKED_MESSAGE` so a visible-but-unflushed `completed`
# is never described with the vocabulary of a Restore that did not finish.
COMPLETION_DURABILITY_UNCONFIRMED_MESSAGE = USER_SAFE_MESSAGES[
    RestoreFailure.COMPLETION_DURABILITY_UNCONFIRMED
]

# Startup is blocked for this run only, by something outside the application. The
# durable phase is untouched, every artifact is preserved, and the next launch
# resumes the same operation from the same phase.
BACKEND_PORT_UNAVAILABLE_MESSAGE = USER_SAFE_MESSAGES[
    RestoreFailure.BACKEND_PORT_UNAVAILABLE
]


@dataclass(frozen=True)
class RestoreRequest:
    """One Restore attempt, as a future trusted launcher caller supplies it.

    **The selected source is the only value a caller may supply.** Every
    destructive or application-owned path — the database, the backup directory,
    the Restore directory, the lock — is derived by
    :class:`~launcher.restore.context.LauncherLifecycleContext` from the
    launcher's own startup resolvers. A caller that could name the target could
    take the lock for one workspace and replace a database in another, and every
    individual check would still pass because each was asked about a path the
    caller chose.
    """

    selected_source: Path


@dataclass(frozen=True)
class RestoreResult:
    """The internal outcome of one Restore attempt.

    Three facts, deliberately kept separate, because a failure to persist a phase
    can make them disagree:

    `outcome`
        What the engine concluded it was doing.
    `durable_phase`
        The phase actually on disk in the authoritative record. Never inferred;
        after any publication whose durability was unproven, this is what a
        re-read returned.
    `normal_startup_allowed`
        Whether the launcher may continue into ordinary startup. Not derivable
        from `outcome` alone: a rollback that could not record its own request
        leaves an unsafe durable phase behind and must block, even though the
        outcome describes an intent to recover.

    Deliberately carries no absolute path. `safety_copy_filename` and
    `staged_candidate_filename` are safe relative filenames, which is everything
    a caller legitimately needs and nothing a screen could leak.
    """

    outcome: RestoreOutcome
    durable_phase: RestorePhase | None
    operation_id: str
    message: str
    normal_startup_allowed: bool
    failure: RestoreFailure | None = None
    safety_copy_filename: str | None = None
    staged_candidate_filename: str | None = None

    @property
    def restore_succeeded(self) -> bool:
        """True only when `completed` is durably on disk **and** startup may proceed.

        `rolled_back` means the previous workspace was recovered after a failed
        Restore, and `CR-010` § 10 forbids reporting it as success. Keyed off the
        durable phase rather than the outcome, so an outcome that was never
        persisted cannot claim success.

        `normal_startup_allowed` is part of the test for a reason that only shows
        up in one narrow window: the replacement and verification can both have
        succeeded, and `completed` can be visible on disk, while the flush that
        would make that record survive a host interruption failed. Reporting
        success there and then refusing to start the application is a mixed
        message a future `C4-II` screen cannot render honestly. Success is
        claimed only when the launcher is actually willing to proceed on it; the
        next start retries the confirmation and reports success then.
        """
        return (
            self.outcome is RestoreOutcome.COMPLETED
            and self.durable_phase is RestorePhase.COMPLETED
            and self.normal_startup_allowed
        )

    @property
    def working_database_replaced(self) -> bool:
        """Derived from the durable phase, never persisted as an independent fact."""
        return self.durable_phase is RestorePhase.COMPLETED


@dataclass(frozen=True)
class RecoveryResult:
    """What startup recovery concluded before ordinary startup was allowed.

    `no_operation` is the ordinary case: no Restore was ever attempted, or the
    previous one is already terminal and safe, so the launcher proceeds exactly
    as it did before `C4-I`.

    `durable_phase` is the phase actually on disk. When recovery could not
    publish its own transition, this reports the phase that really remains — so
    the next launcher start resumes from reality rather than from what this run
    intended.
    """

    normal_startup_allowed: bool
    durable_phase: RestorePhase | None = None
    outcome: RestoreOutcome | None = None
    operation_id: str | None = None
    message: str | None = None
    no_operation: bool = False

    @property
    def blocks_browser(self) -> bool:
        return not self.normal_startup_allowed
