"""Make a packaged startup refusal visible to a user who has no terminal.

An application opened from Finder has no console anybody reads. Without this,
every fatal packaged startup failure — a missing resource, an occupied port, a
backend that refused to start — is a Dock icon that appears and disappears, and
the user's only information is that "nothing happened".

The mechanism is deliberately the smallest thing that works: one `display alert`
through `/usr/bin/osascript`, which every supported macOS already has. It adds
no dependency, and it is **not** a second product UI — it has no state, no
navigation, no product data, and it only ever runs on a path that ends in the
application exiting.

Two rules make it safe to keep:

```text
1. the dialog text is chosen from a fixed catalogue, never composed
2. nothing user-, path- or exception-derived is ever passed to AppleScript
```

The catalogue is why. `osascript -e` compiles its argument as source, so any
interpolated string is executable text; a filesystem path or an exception
message reaching that argument is a script-injection sink. Here the AppleScript
source is three constant lines, the two strings it displays arrive as `argv`
values rather than as source, and every one of them comes from
:data:`STARTUP_FAILURE_MESSAGES`. Technical detail — paths, tracebacks, port
numbers — stays on stderr, where developers and the local log can have it.
"""

from __future__ import annotations

from enum import Enum
import os
import subprocess
import sys

OSASCRIPT = "/usr/bin/osascript"

# The human-facing product name, as decided for the bundle's display name.
ALERT_TITLE = "Мастерская косметолога"

# Set by automated smoke runners and tests. A modal dialog in an unattended run
# would block until it timed out and would make a clean failure look like a hang.
DISABLE_ALERTS_ENV = "COSMETIC_WORKSHOP_PACKAGE_DISABLE_ALERTS"

# The dialog is a last word before exiting, not a prompt. It closes itself so an
# unattended machine cannot be left with a modal window open forever.
ALERT_GIVE_UP_SECONDS = 120


class StartupFailure(Enum):
    """The packaged startup refusals a user can actually be told apart."""

    MISSING_RESOURCES = "missing_resources"
    RUNTIME_MISSING = "runtime_missing"
    FRONTEND_PORT_BUSY = "frontend_port_busy"
    BACKEND_PORT_BUSY = "backend_port_busy"
    LAUNCHER_REFUSED = "launcher_refused"
    UNEXPECTED = "unexpected"


# Fixed, non-technical, and each one ends with something the user can do. No
# entry contains a path, a port number, an exception message or a stack trace.
STARTUP_FAILURE_MESSAGES: dict[StartupFailure, str] = {
    StartupFailure.MISSING_RESOURCES: (
        "Приложение повреждено или распаковано не полностью. "
        "Удалите эту копию, распакуйте архив заново и откройте приложение ещё раз. "
        "Ваши данные не изменились."
    ),
    StartupFailure.RUNTIME_MISSING: (
        "Приложение повреждено: внутри него не найдена рабочая среда. "
        "Удалите эту копию, распакуйте архив заново и откройте приложение ещё раз. "
        "Ваши данные не изменились."
    ),
    StartupFailure.FRONTEND_PORT_BUSY: (
        "Не удалось открыть локальное окно программы: нужный порт занят другой программой. "
        "Закройте другое окно приложения или другую программу и откройте приложение снова. "
        "Ваши данные не изменились."
    ),
    StartupFailure.BACKEND_PORT_BUSY: (
        "Не удалось запустить рабочую часть программы: нужный порт занят другой программой. "
        "Закройте другое окно приложения или другую программу и откройте приложение снова. "
        "Ваши данные не изменились."
    ),
    StartupFailure.LAUNCHER_REFUSED: (
        "Приложение не смогло запуститься и остановилось, ничего не изменив. "
        "Закройте другие окна приложения и попробуйте снова. "
        "Ваши данные не изменились."
    ),
    StartupFailure.UNEXPECTED: (
        "Приложение не смогло запуститься из-за непредвиденной ошибки и остановилось. "
        "Попробуйте открыть приложение ещё раз. "
        "Ваши данные не изменились."
    ),
}


def alerts_enabled() -> bool:
    """Alerts are for a real macOS desktop session, and only when not suppressed."""
    if os.environ.get(DISABLE_ALERTS_ENV):
        return False
    return sys.platform == "darwin" and os.path.exists(OSASCRIPT)


def report_startup_failure(
    failure: StartupFailure, *, packaged: bool, detail: str | None = None
) -> None:
    """Tell the user, and separately tell the log.

    `detail` is the technical half — a resource name, an exception summary. It
    is written to stderr and **never** reaches the dialog or AppleScript. A
    source-tree run gets only the stderr half, which is the developer-visible
    diagnostic the launcher already relies on.
    """
    message = STARTUP_FAILURE_MESSAGES[failure]
    print(f"{ALERT_TITLE}: {message}", file=sys.stderr)
    if detail:
        print(f"[{failure.value}] {detail}", file=sys.stderr)
    if packaged:
        show_alert(message)


def show_alert(message: str) -> bool:
    """Display one fixed catalogue message, or do nothing at all.

    Returns whether a dialog was actually shown, which is what the tests assert
    on. A message outside the catalogue is refused rather than displayed: that
    is the invariant keeping composed or user-derived text away from AppleScript,
    and it is checked here rather than trusted at every call site.
    """
    if message not in STARTUP_FAILURE_MESSAGES.values():
        print(
            "Отказ: попытка показать сообщение вне фиксированного набора.",
            file=sys.stderr,
        )
        return False
    if not alerts_enabled():
        return False
    try:
        subprocess.run(
            [
                OSASCRIPT,
                "-e",
                "on run argv",
                # Both strings are read from `argv` at runtime. Neither is part
                # of the compiled script text, so neither can be interpreted as
                # AppleScript no matter what it contains.
                "-e",
                "display alert (item 1 of argv) message (item 2 of argv) "
                f"as critical giving up after {ALERT_GIVE_UP_SECONDS}",
                "-e",
                "end run",
                "--",
                ALERT_TITLE,
                message,
            ],
            check=False,
            capture_output=True,
            timeout=ALERT_GIVE_UP_SECONDS + 30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        # A failed dialog must never replace the failure it was describing.
        print(f"Не удалось показать сообщение об ошибке: {exc!r}", file=sys.stderr)
        return False
    return True
