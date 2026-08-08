"""Launcher-owned native macOS source picker for C4-II-A3.

The browser never receives or supplies a filesystem path. Production uses the
exact macOS-provided ``/usr/bin/osascript`` executable with one fixed AppleScript
program. The only value returned to the launcher is the selected absolute POSIX
path; C4-I/A1 remains the acceptance and validation authority.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from threading import Event
from typing import Callable

from launcher.restore.control_protocol import SourceSelectionResult

OSASCRIPT_PATH = Path("/usr/bin/osascript")
PICKER_CANCELLED_SENTINEL = "__CWOS_RESTORE_PICKER_CANCELLED__"
PICKER_POLL_SECONDS = 0.05
PICKER_TERMINATE_TIMEOUT_SECONDS = 1.0

PICKER_APPLESCRIPT = f'''use scripting additions
try
    set selectedFile to choose file with prompt "Выберите резервную копию мастерской"
    return POSIX path of selectedFile
on error number -128
    return "{PICKER_CANCELLED_SENTINEL}"
end try
'''


class NativePickerError(RuntimeError):
    """Launcher-internal native picker failure; details never cross the control API."""


class MacOSNativeSourceSelectionAdapter:
    """Run one owned native macOS picker and cooperate with A2 cancellation."""

    def __init__(
        self,
        *,
        process_factory: Callable[..., subprocess.Popen[str]] | None = None,
        platform_name: str | None = None,
        osascript_path: Path | None = None,
        poll_seconds: float = PICKER_POLL_SECONDS,
        terminate_timeout_seconds: float = PICKER_TERMINATE_TIMEOUT_SECONDS,
    ) -> None:
        self._process_factory = process_factory or subprocess.Popen
        self._platform_name = sys.platform if platform_name is None else platform_name
        self._osascript_path = OSASCRIPT_PATH if osascript_path is None else Path(osascript_path)
        self._poll_seconds = poll_seconds
        self._terminate_timeout_seconds = terminate_timeout_seconds

    def select(self, cancel_event: Event) -> SourceSelectionResult:
        if cancel_event.is_set():
            return SourceSelectionResult.cancelled()
        if self._platform_name != "darwin" or not self._osascript_path.is_file():
            return SourceSelectionResult.unavailable()

        try:
            process = self._process_factory(
                [str(self._osascript_path), "-e", PICKER_APPLESCRIPT],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
        except OSError as exc:
            raise NativePickerError("native_picker_spawn_failed") from exc

        try:
            completed = self._communicate_until_complete(process, cancel_event)
        except BaseException:
            self._terminate_owned_process(process)
            raise

        if completed is None:
            return SourceSelectionResult.cancelled()

        stdout, _stderr = completed
        if cancel_event.is_set():
            return SourceSelectionResult.cancelled()
        if process.returncode != 0:
            raise NativePickerError("native_picker_failed")

        output = _strip_osascript_record_terminator(stdout)
        if output == PICKER_CANCELLED_SENTINEL:
            return SourceSelectionResult.cancelled()
        if not output:
            raise NativePickerError("native_picker_empty_result")

        selected_path = Path(output)
        if not selected_path.is_absolute():
            raise NativePickerError("native_picker_non_absolute_result")
        return SourceSelectionResult.selected(selected_path)

    def _communicate_until_complete(
        self,
        process: subprocess.Popen[str],
        cancel_event: Event,
    ) -> tuple[str, str] | None:
        while True:
            if cancel_event.is_set():
                self._terminate_owned_process(process)
                return None
            try:
                return process.communicate(timeout=self._poll_seconds)
            except subprocess.TimeoutExpired:
                continue

    def _terminate_owned_process(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            process.communicate()
            return
        try:
            process.terminate()
        except ProcessLookupError:
            # The child can exit naturally between poll() and terminate(). It is
            # still our child, so drain/reap it and preserve typed cancellation.
            process.communicate()
            return
        try:
            process.communicate(timeout=self._terminate_timeout_seconds)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            # SIGKILL is the final ownership boundary: wait until the exact child
            # is reaped rather than returning an unaccounted picker process.
            process.communicate()


def _strip_osascript_record_terminator(output: str) -> str:
    """Remove only osascript's one record terminator, preserving filename newlines."""

    if output.endswith("\r\n"):
        return output[:-2]
    if output.endswith("\n"):
        return output[:-1]
    return output
