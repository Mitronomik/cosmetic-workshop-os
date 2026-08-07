"""Launcher-owned temporary scratch for non-destructive Restore validation.

C4-II-A1 must validate a selected backup without creating a durable Restore
operation.  The scratch therefore lives under the operating-system temporary
root, not under the durable ``<user-data>/restore`` workspace used by C4-I::

    <system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/

Only directories carrying this module's exact ownership/version marker are ever
cleaned.  Symlinks and paths outside the canonical validation root are refused.
The run/session names are launcher-generated UUID4 values and never contain user
input.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import stat
import tempfile
import uuid

from launcher.restore.workspace import RestoreWorkspace

VALIDATION_APP_DIRNAME = "cosmetic-workshop-os"
VALIDATION_DIRNAME = "restore-validation"
VALIDATION_MARKER_FILENAME = ".cwos-validation-owner"
VALIDATION_MARKER_VERSION = "cosmetic-workshop-os:restore-validation:v1"
PRIVATE_DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600


class ValidationScratchError(RuntimeError):
    """Raised when launcher ownership of validation scratch cannot be proved."""


def _new_id() -> str:
    return str(uuid.uuid4())


def _is_uuid4(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError, TypeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def _directory_is_private(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        return False
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        return False
    return stat.S_IMODE(info.st_mode) & 0o077 == 0


def _protect_private_directory(path: Path) -> Path:
    """Prove one existing directory is real/user-owned, then tighten its mode."""

    try:
        info = os.lstat(path)
    except OSError as exc:
        raise ValidationScratchError(
            f"Could not inspect validation scratch: {type(exc).__name__}"
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ValidationScratchError("Validation scratch path contains a symlink or non-directory.")
    if hasattr(os, "getuid") and info.st_uid != os.getuid():
        raise ValidationScratchError("Validation scratch directory is not owned by this user.")
    try:
        os.chmod(path, PRIVATE_DIRECTORY_MODE)
    except OSError as exc:
        raise ValidationScratchError(
            f"Could not protect validation scratch: {type(exc).__name__}"
        ) from exc
    if not _directory_is_private(path):
        raise ValidationScratchError("Validation scratch permissions are not user-only.")
    return path


def _ensure_default_private_root() -> Path:
    """Create the fixed app subtree without following a planted child symlink.

    ``tempfile.gettempdir()`` can itself have platform-level aliases (macOS often
    exposes ``/var`` via ``/private/var``), so the operating-system temp base is
    canonicalized first.  From that trusted base onward, however, each app-owned
    path component is inspected with ``lstat`` and created one level at a time.
    A pre-existing symlink at ``cosmetic-workshop-os`` or ``restore-validation``
    is therefore refused before this launcher can create/chmod anything through
    it outside the canonical temp subtree.
    """

    try:
        temp_base = Path(tempfile.gettempdir()).resolve(strict=True)
        base_info = os.lstat(temp_base)
    except OSError as exc:
        raise ValidationScratchError(
            f"Could not resolve system temporary directory: {type(exc).__name__}"
        ) from exc
    if stat.S_ISLNK(base_info.st_mode) or not stat.S_ISDIR(base_info.st_mode):
        raise ValidationScratchError("System temporary path is not a directory.")

    current = temp_base
    for component in (VALIDATION_APP_DIRNAME, VALIDATION_DIRNAME):
        candidate = current / component
        try:
            if os.path.lexists(candidate):
                info = os.lstat(candidate)
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    raise ValidationScratchError(
                        "Validation scratch path contains a symlink or non-directory."
                    )
            else:
                candidate.mkdir(
                    mode=PRIVATE_DIRECTORY_MODE,
                    parents=False,
                    exist_ok=False,
                )
        except ValidationScratchError:
            raise
        except OSError as exc:
            raise ValidationScratchError(
                f"Could not establish validation scratch: {type(exc).__name__}"
            ) from exc
        current = _protect_private_directory(candidate)

    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(temp_base)
    except (OSError, ValueError, RuntimeError) as exc:
        raise ValidationScratchError(
            "Validation scratch escaped the canonical system temporary root."
        ) from exc
    return resolved


def _ensure_private_root(path: Path) -> Path:
    """Test/integration injection seam; refuse a symlinked final root."""

    try:
        path.mkdir(parents=True, mode=PRIVATE_DIRECTORY_MODE, exist_ok=True)
    except OSError as exc:
        raise ValidationScratchError(
            f"Could not establish validation scratch: {type(exc).__name__}"
        ) from exc
    _protect_private_directory(path)
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise ValidationScratchError(
            f"Could not resolve validation scratch: {type(exc).__name__}"
        ) from exc


def _create_private_directory(path: Path) -> Path:
    try:
        path.mkdir(mode=PRIVATE_DIRECTORY_MODE, parents=False, exist_ok=False)
    except OSError as exc:
        raise ValidationScratchError(
            f"Could not create validation scratch directory: {type(exc).__name__}"
        ) from exc
    if not _directory_is_private(path):
        raise ValidationScratchError("Validation scratch directory is not user-only.")
    return path


def _marker_payload(*, kind: str, run_id: str, session_id: str | None = None) -> bytes:
    lines = [VALIDATION_MARKER_VERSION, f"kind={kind}", f"run_id={run_id}"]
    if session_id is not None:
        lines.append(f"session_id={session_id}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _write_marker(directory: Path, payload: bytes) -> None:
    marker = directory / VALIDATION_MARKER_FILENAME
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(marker, flags, PRIVATE_FILE_MODE)
    except OSError as exc:
        raise ValidationScratchError(
            f"Could not mark validation scratch ownership: {type(exc).__name__}"
        ) from exc
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)


def _marker_matches(directory: Path, payload: bytes) -> bool:
    marker = directory / VALIDATION_MARKER_FILENAME
    if marker.is_symlink() or not marker.is_file():
        return False
    try:
        info = os.lstat(marker)
        if hasattr(os, "getuid") and info.st_uid != os.getuid():
            return False
        if stat.S_IMODE(info.st_mode) & 0o077:
            return False
        return marker.read_bytes() == payload
    except OSError:
        return False


@dataclass(frozen=True)
class ValidationScratchSession:
    """One launcher-owned temporary staging session."""

    run_id: str
    session_id: str
    directory: Path
    workspace: RestoreWorkspace


class ValidationScratchManager:
    """Own the system-temp validation namespace for one launcher run."""

    def __init__(
        self,
        database_path: Path,
        *,
        root: Path | None = None,
        run_id: str | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.root = (
            _ensure_private_root(Path(root))
            if root is not None
            else _ensure_default_private_root()
        )
        self.run_id = run_id or _new_id()
        if not _is_uuid4(self.run_id):
            raise ValidationScratchError("Validation run identity is not a canonical UUID4.")

        self.run_dir = self.root / self.run_id
        if self.run_dir.exists() or self.run_dir.is_symlink():
            raise ValidationScratchError("Validation run directory already exists.")
        _create_private_directory(self.run_dir)
        try:
            _write_marker(
                self.run_dir,
                _marker_payload(kind="run", run_id=self.run_id),
            )
        except Exception:
            try:
                self.run_dir.rmdir()
            except OSError:
                pass
            raise

    def _inside_root(self, candidate: Path) -> bool:
        try:
            root = self.root.resolve()
            resolved = Path(candidate).resolve(strict=False)
        except (OSError, RuntimeError):
            return False
        return resolved == root or root in resolved.parents

    def _owned_run(self, run_dir: Path, run_id: str) -> bool:
        return (
            _is_uuid4(run_id)
            and self._inside_root(run_dir)
            and _directory_is_private(run_dir)
            and _marker_matches(
                run_dir,
                _marker_payload(kind="run", run_id=run_id),
            )
        )

    def _owned_session(self, run_dir: Path, run_id: str, session_id: str) -> bool:
        session_dir = run_dir / session_id
        return (
            self._owned_run(run_dir, run_id)
            and _is_uuid4(session_id)
            and self._inside_root(session_dir)
            and _directory_is_private(session_dir)
            and _marker_matches(
                session_dir,
                _marker_payload(kind="session", run_id=run_id, session_id=session_id),
            )
        )

    def create_session(self) -> ValidationScratchSession:
        """Create one private UUID4 session directory for real C4-I staging."""

        if not self._owned_run(self.run_dir, self.run_id):
            raise ValidationScratchError("Validation run ownership could not be proved.")
        for _attempt in range(8):
            session_id = _new_id()
            session_dir = self.run_dir / session_id
            try:
                _create_private_directory(session_dir)
            except ValidationScratchError:
                if session_dir.exists():
                    continue
                raise
            try:
                _write_marker(
                    session_dir,
                    _marker_payload(
                        kind="session", run_id=self.run_id, session_id=session_id
                    ),
                )
            except Exception:
                try:
                    session_dir.rmdir()
                except OSError:
                    pass
                raise
            workspace = RestoreWorkspace(
                restore_dir=self.run_dir,
                database_path=self.database_path,
            )
            return ValidationScratchSession(
                run_id=self.run_id,
                session_id=session_id,
                directory=session_dir,
                workspace=workspace,
            )
        raise ValidationScratchError("Could not allocate a unique validation session.")

    def cleanup_session(self, session_id: str) -> bool:
        """Delete one session only after proving its exact ownership marker."""

        if not self._owned_session(self.run_dir, self.run_id, session_id):
            return False
        workspace = RestoreWorkspace(
            restore_dir=self.run_dir,
            database_path=self.database_path,
        )
        workspace.clean_owned_staging(session_id)
        return not (self.run_dir / session_id).exists()

    def cleanup_interrupted_runs(self) -> int:
        """Remove only recognized sessions from previous launcher runs.

        The current run is deliberately excluded.  A future A2 launcher owner
        calls this only after it has single-instance authority; A1 exposes the
        bounded primitive without inventing that lifecycle wiring early.
        """

        removed_runs = 0
        try:
            entries = list(self.root.iterdir())
        except OSError:
            return 0
        for run_dir in entries:
            run_id = run_dir.name
            if run_id == self.run_id or run_dir.is_symlink():
                continue
            if not self._owned_run(run_dir, run_id):
                continue
            workspace = RestoreWorkspace(
                restore_dir=run_dir,
                database_path=self.database_path,
            )
            try:
                children = list(run_dir.iterdir())
            except OSError:
                continue
            for child in children:
                if child.name == VALIDATION_MARKER_FILENAME:
                    continue
                if child.is_symlink() or not child.is_dir():
                    continue
                session_id = child.name
                if not self._owned_session(run_dir, run_id, session_id):
                    continue
                workspace.clean_owned_staging(session_id)

            try:
                remaining = list(run_dir.iterdir())
            except OSError:
                continue
            marker = run_dir / VALIDATION_MARKER_FILENAME
            if remaining == [marker] or (
                len(remaining) == 1 and remaining[0].name == VALIDATION_MARKER_FILENAME
            ):
                try:
                    marker.unlink()
                    run_dir.rmdir()
                    removed_runs += 1
                except OSError:
                    continue
        return removed_runs

    def cleanup_current_run_if_empty(self) -> bool:
        """Remove the current run marker/root only when no session remains."""

        if not self._owned_run(self.run_dir, self.run_id):
            return False
        try:
            remaining = list(self.run_dir.iterdir())
        except OSError:
            return False
        if len(remaining) != 1 or remaining[0].name != VALIDATION_MARKER_FILENAME:
            return False
        try:
            remaining[0].unlink()
            self.run_dir.rmdir()
        except OSError:
            return False
        return True
