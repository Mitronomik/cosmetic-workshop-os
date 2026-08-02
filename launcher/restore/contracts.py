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
}

SUCCESS_MESSAGE = "Восстановление завершено. Приложение работает с восстановленными данными."

ROLLED_BACK_MESSAGE = USER_SAFE_MESSAGES[RestoreFailure.VERIFICATION_FAILED_ROLLED_BACK]

# The one fixed non-technical sentence shown when nothing can be proved safe.
RECOVERY_BLOCKED_MESSAGE = USER_SAFE_MESSAGES[RestoreFailure.RECOVERY_BLOCKED]


@dataclass(frozen=True)
class RestoreRequest:
    """One Restore attempt, as a future trusted launcher caller supplies it.

    `selected_source` is the only untrusted value and is treated as immutable
    input throughout. `database_path` is **not** taken from the caller's user
    input: it is the exact path the launcher's own startup preparation resolved,
    which is what keeps Restore from ever replacing an unrelated file.
    """

    selected_source: Path
    database_path: Path
    backup_dir: Path
    restore_dir: Path
    mode: str = "user"


@dataclass(frozen=True)
class RestoreResult:
    """The internal outcome of one Restore attempt.

    Deliberately carries no absolute path. `safety_copy_filename` and
    `staged_candidate_filename` are safe relative filenames, which is everything
    a caller legitimately needs and nothing a screen could leak.
    """

    outcome: RestoreOutcome
    phase: RestorePhase
    operation_id: str
    message: str
    failure: RestoreFailure | None = None
    safety_copy_filename: str | None = None
    staged_candidate_filename: str | None = None

    @property
    def restore_succeeded(self) -> bool:
        """True only for `completed`.

        `rolled_back` means the previous workspace was recovered after a failed
        Restore, and `CR-010` § 10 forbids reporting it as success.
        """
        return self.outcome is RestoreOutcome.COMPLETED

    @property
    def working_database_replaced(self) -> bool:
        """Derived from `phase`, never persisted as an independent fact."""
        return self.phase is RestorePhase.COMPLETED


@dataclass(frozen=True)
class RecoveryResult:
    """What startup recovery concluded before ordinary startup was allowed.

    `no_operation` is the ordinary case: no Restore was ever attempted, or the
    previous one is already terminal and safe, so the launcher proceeds exactly
    as it did before `C4-I`.
    """

    normal_startup_allowed: bool
    phase: RestorePhase | None = None
    outcome: RestoreOutcome | None = None
    operation_id: str | None = None
    message: str | None = None
    no_operation: bool = False

    @property
    def blocks_browser(self) -> bool:
        return not self.normal_startup_allowed
