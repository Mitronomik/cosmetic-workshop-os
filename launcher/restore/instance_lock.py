"""One exclusive launcher instance, for the whole protected lifecycle.

`CR-010` § 2 requires the launcher to prevent a second application instance from
starting, and the same boundary has to cover ordinary startup, Restore execution
and incomplete-operation recovery. Splitting those would let a second launcher
begin recovery while the first is halfway through a replacement.

The primitive is `fcntl.flock(LOCK_EX | LOCK_NB)` on a launcher-owned lock file
under the Restore directory:

- **advisory, exclusive, per open file description.** A second process taking the
  same lock gets `BlockingIOError`/`OSError` immediately rather than waiting;
- **released by the kernel when the holder dies.** A launcher killed mid-Restore
  leaves no stale lock to clear by hand, which matters because the recovery path
  must be able to run on the next start;
- **supported on macOS and Linux**, the platforms this local-first product runs
  on. There is no Windows support here, and none is claimed.

The lock file's *contents* are not the lock and are never read as authority. The
holder's PID is written for human diagnosis only.

The backend port check is **not** the lock and does not replace it. A port is
free during exactly the window Restore needs protecting — the backend is stopped
— so inferring safety from it would be inferring safety from the absence of the
thing being coordinated. The existing port-conflict check stays where it is, with
its existing message.
"""

from __future__ import annotations

from pathlib import Path
from types import TracebackType
import fcntl
import os

from launcher.restore.workspace import RestoreWorkspace


class LauncherAlreadyRunningError(RuntimeError):
    """Raised when another launcher instance already owns the lifecycle."""


class LauncherInstanceLock:
    """An exclusive, non-blocking, self-releasing launcher-instance lock.

    Usable as a context manager. Re-entrant acquisition is refused rather than
    counted: nesting would mean two places in one process each believe they own
    the lifecycle, and only one of them can be right about when to release it.
    """

    def __init__(self, lock_path: Path) -> None:
        self.lock_path = Path(lock_path)
        self._fd: int | None = None

    @classmethod
    def for_workspace(cls, workspace: RestoreWorkspace) -> "LauncherInstanceLock":
        workspace.ensure_restore_dir()
        return cls(workspace.lock_path)

    @property
    def held(self) -> bool:
        return self._fd is not None

    def acquire(self) -> "LauncherInstanceLock":
        if self._fd is not None:
            raise LauncherAlreadyRunningError("This launcher instance already holds the lock.")
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise LauncherAlreadyRunningError(
                "Another instance of the application is already running."
            ) from exc
        try:
            # Diagnostic only. Truncating and rewriting is safe precisely because
            # nothing reads this back as authority — the flock is the lock.
            os.ftruncate(fd, 0)
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
        except OSError:
            pass
        self._fd = fd
        return self

    def release(self) -> None:
        """Release the lock, leaving the lock file in place.

        The file is not unlinked. Unlinking it would let a second launcher that
        already opened the same path hold a lock on an unlinked inode while a
        third creates a fresh one — two holders, one lifecycle.
        """
        fd, self._fd = self._fd, None
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass
        finally:
            os.close(fd)

    def __enter__(self) -> "LauncherInstanceLock":
        return self.acquire()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()
