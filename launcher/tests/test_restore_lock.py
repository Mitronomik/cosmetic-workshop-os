"""The exclusive launcher-instance boundary.

One lock covers ordinary startup, Restore execution and incomplete-Restore
recovery, so a second launcher cannot enter the protected lifecycle while the
first is inside it. The concurrency proof uses a real second **process**: an
`fcntl.flock` is held per open file description, so two locks taken in one
process would not exercise the property that matters.
"""

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from launcher.restore.instance_lock import LauncherAlreadyRunningError, LauncherInstanceLock
from launcher.restore.workspace import INSTANCE_LOCK_FILENAME, RestoreWorkspace


@pytest.fixture
def workspace(tmp_path):
    return RestoreWorkspace(
        restore_dir=tmp_path / "restore", database_path=tmp_path / "data" / "workshop.sqlite"
    )


def try_lock_in_another_process(lock_path: Path) -> str:
    """Attempt the same lock from a separate interpreter, and report the result."""
    script = textwrap.dedent(
        """
        import fcntl, os, sys
        fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("refused")
        else:
            print("acquired")
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(lock_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return completed.stdout.strip()


def test_one_launcher_owns_the_lifecycle(workspace):
    lock = LauncherInstanceLock.for_workspace(workspace)

    with lock:
        assert lock.held
        assert workspace.lock_path.name == INSTANCE_LOCK_FILENAME
        assert workspace.lock_path.exists()
    assert not lock.held


def test_a_competing_launcher_instance_cannot_enter_the_lifecycle(workspace):
    with LauncherInstanceLock.for_workspace(workspace):
        assert try_lock_in_another_process(workspace.lock_path) == "refused"


def test_the_lock_is_released_after_safe_completion(workspace):
    with LauncherInstanceLock.for_workspace(workspace):
        pass

    assert try_lock_in_another_process(workspace.lock_path) == "acquired"


def test_the_lock_is_retained_for_the_whole_protected_section(workspace):
    """Recovery work happens inside the same boundary as startup."""
    lock = LauncherInstanceLock.for_workspace(workspace).acquire()
    try:
        assert try_lock_in_another_process(workspace.lock_path) == "refused"
        # A simulated recovery step in the middle changes nothing.
        workspace.clean_owned_temp_files()
        assert try_lock_in_another_process(workspace.lock_path) == "refused"
    finally:
        lock.release()


def test_re_entrant_acquisition_is_refused(workspace):
    lock = LauncherInstanceLock.for_workspace(workspace).acquire()
    try:
        with pytest.raises(LauncherAlreadyRunningError):
            lock.acquire()
    finally:
        lock.release()


def test_releasing_twice_is_harmless(workspace):
    lock = LauncherInstanceLock.for_workspace(workspace).acquire()
    lock.release()
    lock.release()

    assert not lock.held


def test_the_lock_file_is_not_unlinked_on_release(workspace):
    """Unlinking would let two holders coexist on different inodes."""
    with LauncherInstanceLock.for_workspace(workspace):
        pass

    assert workspace.lock_path.exists()


def test_the_lock_file_contents_are_never_read_as_authority(workspace):
    """The flock is the lock; the PID inside is diagnostic only."""
    workspace.ensure_restore_dir()
    workspace.lock_path.write_text("999999\n", encoding="utf-8")

    with LauncherInstanceLock.for_workspace(workspace) as lock:
        assert lock.held


def test_a_second_launcher_is_refused_by_run_local_runtime(monkeypatch, tmp_path):
    """The launcher surfaces the boundary with a human-readable Russian message."""
    import socket

    from launcher import runtime
    from launcher.config import build_runtime_config, resolve_runtime_paths

    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv("COSMETIC_WORKSHOP_USER_DATA_DIR", str(user_data_dir))
    monkeypatch.delenv("COSMETIC_WORKSHOP_DB_PATH", raising=False)

    database_path = user_data_dir / "data" / "cosmetic_workshop.sqlite"
    holder = LauncherInstanceLock.for_workspace(
        RestoreWorkspace.for_database(database_path)
    ).acquire()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            free_port = probe.getsockname()[1]
        config = build_runtime_config(backend_port=free_port, open_browser=False)

        with pytest.raises(runtime.RuntimeLaunchError, match="уже запущено"):
            runtime.run_local_runtime(config, resolve_runtime_paths())
    finally:
        holder.release()


def test_the_port_check_still_runs_and_keeps_its_own_message(monkeypatch, tmp_path):
    """The port conflict behaviour is unchanged, and is not the Restore lock."""
    import socket

    from launcher import runtime
    from launcher.config import build_runtime_config, resolve_runtime_paths

    user_data_dir = tmp_path / "user-data"
    monkeypatch.setenv("COSMETIC_WORKSHOP_USER_DATA_DIR", str(user_data_dir))
    monkeypatch.delenv("COSMETIC_WORKSHOP_DB_PATH", raising=False)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        config = build_runtime_config(
            backend_port=occupied.getsockname()[1], open_browser=False
        )

        with pytest.raises(runtime.RuntimeLaunchError, match="Порт .* уже занят"):
            runtime.run_local_runtime(config, resolve_runtime_paths())

    # The port check comes first, so nothing under the user-data boundary was
    # created — including the Restore directory.
    assert not user_data_dir.exists()
