"""C4-II-A3 native macOS picker unit contract."""

from __future__ import annotations

from pathlib import Path
import subprocess
import threading

import pytest

from launcher.restore.control_protocol import SourceSelectionState
from launcher.restore.macos_picker import (
    MacOSNativeSourceSelectionAdapter,
    NativePickerError,
    OSASCRIPT_PATH,
    PICKER_APPLESCRIPT,
    PICKER_CANCELLED_SENTINEL,
    _strip_osascript_record_terminator,
)


class CompletedProcess:
    def __init__(self, stdout: str, *, returncode: int = 0, stderr: str = "") -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def communicate(self, timeout=None):
        del timeout
        return self.stdout, self.stderr

    def poll(self):
        return self.returncode

    def terminate(self):
        raise AssertionError("completed process must not be terminated")

    def kill(self):
        raise AssertionError("completed process must not be killed")


class BlockingProcess:
    def __init__(self, *, stubborn_after_terminate: bool = False) -> None:
        self.started = threading.Event()
        self.terminated = False
        self.killed = False
        self.returncode = None
        self.stubborn_after_terminate = stubborn_after_terminate

    def communicate(self, timeout=None):
        self.started.set()
        if self.killed:
            self.returncode = -9
            return "", ""
        if self.terminated and not self.stubborn_after_terminate:
            self.returncode = -15
            return "", ""
        raise subprocess.TimeoutExpired(cmd="osascript", timeout=timeout or 0)

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


class ExitBetweenPollAndTerminateProcess:
    """Deterministically model natural child exit in the poll→terminate window."""

    def __init__(self, cancel_event: threading.Event) -> None:
        self.cancel_event = cancel_event
        self.returncode = None
        self.first_communicate = True
        self.reaped = False

    def communicate(self, timeout=None):
        if self.first_communicate:
            self.first_communicate = False
            self.cancel_event.set()
            raise subprocess.TimeoutExpired(cmd="osascript", timeout=timeout or 0)
        self.returncode = 0
        self.reaped = True
        return "", ""

    def poll(self):
        return self.returncode

    def terminate(self):
        raise ProcessLookupError("child exited naturally")

    def kill(self):
        raise AssertionError("naturally exited child must not be killed")


@pytest.fixture
def fake_osascript(tmp_path: Path) -> Path:
    path = tmp_path / "osascript"
    path.write_text("fake", encoding="utf-8")
    return path


def test_selected_path_uses_exact_owned_osascript_command(fake_osascript: Path):
    calls = []
    selected = Path("/tmp/workshop-backup.sqlite")

    def factory(argv, **kwargs):
        calls.append((argv, kwargs))
        return CompletedProcess(f"{selected}\n")

    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=factory,
        platform_name="darwin",
        osascript_path=fake_osascript,
    )
    result = adapter.select(threading.Event())

    assert OSASCRIPT_PATH == Path("/usr/bin/osascript")
    assert result.state is SourceSelectionState.SELECTED
    assert result.selected_source == selected
    assert calls[0][0] == [str(fake_osascript), "-e", PICKER_APPLESCRIPT]
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["stdin"] is subprocess.DEVNULL
    assert calls[0][1]["stdout"] is subprocess.PIPE
    assert calls[0][1]["stderr"] is subprocess.PIPE
    assert "use scripting additions" in PICKER_APPLESCRIPT
    assert "choose file" in PICKER_APPLESCRIPT
    assert "POSIX path of selectedFile" in PICKER_APPLESCRIPT
    assert "on error number -128" in PICKER_APPLESCRIPT
    assert "System Events" not in PICKER_APPLESCRIPT


def test_user_cancel_is_typed_cancelled(fake_osascript: Path):
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: CompletedProcess(
            f"{PICKER_CANCELLED_SENTINEL}\n"
        ),
        platform_name="darwin",
        osascript_path=fake_osascript,
    )

    result = adapter.select(threading.Event())

    assert result.state is SourceSelectionState.CANCELLED
    assert result.selected_source is None


def test_cancel_before_spawn_never_starts_child(fake_osascript: Path):
    calls = []
    cancel = threading.Event()
    cancel.set()
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: calls.append(True),
        platform_name="darwin",
        osascript_path=fake_osascript,
    )

    result = adapter.select(cancel)

    assert result.state is SourceSelectionState.CANCELLED
    assert calls == []


def test_cancel_terminates_and_reaps_owned_picker_process(fake_osascript: Path):
    process = BlockingProcess()
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: process,
        platform_name="darwin",
        osascript_path=fake_osascript,
        poll_seconds=0.01,
    )
    cancel = threading.Event()
    holder = []
    worker = threading.Thread(target=lambda: holder.append(adapter.select(cancel)))
    worker.start()
    assert process.started.wait(timeout=1.0)

    cancel.set()
    worker.join(timeout=2.0)

    assert not worker.is_alive()
    assert process.terminated is True
    assert process.killed is False
    assert holder[0].state is SourceSelectionState.CANCELLED


def test_terminate_timeout_kills_and_reaps_owned_picker_process(fake_osascript: Path):
    process = BlockingProcess(stubborn_after_terminate=True)
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: process,
        platform_name="darwin",
        osascript_path=fake_osascript,
        poll_seconds=0.01,
        terminate_timeout_seconds=0.01,
    )
    cancel = threading.Event()
    holder = []
    worker = threading.Thread(target=lambda: holder.append(adapter.select(cancel)))
    worker.start()
    assert process.started.wait(timeout=1.0)

    cancel.set()
    worker.join(timeout=2.0)

    assert not worker.is_alive()
    assert process.terminated is True
    assert process.killed is True
    assert holder[0].state is SourceSelectionState.CANCELLED


def test_natural_exit_between_poll_and_terminate_is_reaped_as_cancel(fake_osascript: Path):
    cancel = threading.Event()
    process = ExitBetweenPollAndTerminateProcess(cancel)
    adapter = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: process,
        platform_name="darwin",
        osascript_path=fake_osascript,
        poll_seconds=0.01,
    )

    result = adapter.select(cancel)

    assert result.state is SourceSelectionState.CANCELLED
    assert process.reaped is True


def test_non_macos_or_missing_exact_helper_is_typed_unavailable(fake_osascript: Path, tmp_path: Path):
    non_macos = MacOSNativeSourceSelectionAdapter(
        platform_name="linux",
        osascript_path=fake_osascript,
    )
    missing = MacOSNativeSourceSelectionAdapter(
        platform_name="darwin",
        osascript_path=tmp_path / "missing-osascript",
    )

    assert non_macos.select(threading.Event()).state is SourceSelectionState.UNAVAILABLE
    assert missing.select(threading.Event()).state is SourceSelectionState.UNAVAILABLE


def test_nonzero_or_non_absolute_output_is_internal_failure(fake_osascript: Path):
    failing = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: CompletedProcess("", returncode=1),
        platform_name="darwin",
        osascript_path=fake_osascript,
    )
    relative = MacOSNativeSourceSelectionAdapter(
        process_factory=lambda *_args, **_kwargs: CompletedProcess("relative.sqlite\n"),
        platform_name="darwin",
        osascript_path=fake_osascript,
    )

    with pytest.raises(NativePickerError, match="native_picker_failed"):
        failing.select(threading.Event())
    with pytest.raises(NativePickerError, match="native_picker_non_absolute_result"):
        relative.select(threading.Event())


def test_record_terminator_removal_preserves_filename_newline():
    assert _strip_osascript_record_terminator("/tmp/name\n\n") == "/tmp/name\n"
    assert _strip_osascript_record_terminator("/tmp/name\r\n") == "/tmp/name"
