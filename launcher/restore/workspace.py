"""The isolated launcher-owned Restore operation directory and its ownership rules.

Every artifact `C4-I` creates lives inside one directory it made itself, under
the application user-data boundary — never inside the SQLite working database,
the repository, the application package or frontend storage.

```text
<user data base>/restore/
  launcher.lock                     exclusive launcher-instance lock
  operation.json                    the one authoritative operation record
  .operation.json.<random>.tmp      transient publication scratch (owned)
  <operation-id>/                   one isolated directory per attempt
    candidate.sqlite                the staged read-only candidate
```

Placement mirrors `app.services.backup.resolve_backup_dir` exactly rather than
inventing a second rule: in user-data mode the directory sits beside `backups/`,
and in development mode it stays next to the configured development database so
a developer run can never write into the real Documents directory.

**Ownership is provable, not assumed.** Cleanup only ever removes paths that
resolve inside a directory this module created, and only names it recognizes.
Nothing here unlinks an arbitrary path, follows a symlink out of the boundary, or
deletes a verified safety copy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import uuid

RESTORE_DIRNAME = "restore"
OPERATION_RECORD_FILENAME = "operation.json"
INSTANCE_LOCK_FILENAME = "launcher.lock"
STAGED_CANDIDATE_FILENAME = "candidate.sqlite"

# The scratch suffix used by every launcher-owned temporary file. Deliberately
# not a SQLite suffix, so an interrupted operation can never leave something that
# looks like a usable database or a listable backup.
OWNED_TEMP_SUFFIX = ".tmp"

# The prefix every launcher-owned scratch file carries. Cleanup matches on it, so
# a file this launcher did not create cannot be removed by mistake.
OWNED_TEMP_PREFIX = ".cwos-restore."


class RestoreWorkspaceError(RuntimeError):
    """Raised when the Restore workspace cannot be established or trusted."""


# The only UUID version this launcher generates. Pinned so a record carrying a
# v1 (MAC-address-and-time) or v5 (name-derived) identity is refused: those are
# derivable rather than random, and an operation ID is also a directory name.
OPERATION_ID_UUID_VERSION = 4


def new_operation_id() -> str:
    """One launcher-generated operation ID per attempt.

    A lowercase UUID4, matching the identity spelling the CR-009 ledger already
    uses. A new attempt always gets a new ID: a terminal operation record is
    never reactivated, so identity is what separates attempts.
    """
    return str(uuid.uuid4())


def is_launcher_operation_id(value: object) -> bool:
    """Whether `value` is an identity *this launcher* could have generated.

    Deliberately stricter than "a safe relative filename". An operation ID is
    joined onto the Restore directory to form a directory name, so accepting any
    safe filename would let a record name an arbitrary sibling directory as its
    own — a name that is harmless to store and not harmless to act on.

    Three conditions, and the reuse matters: the canonical-spelling check is the
    backend's own `is_canonical_operation_id`, which round-trips through
    `str(uuid.UUID(value))` so exactly one spelling per identity is admitted —
    no uppercase, no braces, no URN, no unhyphenated form. On top of that the
    version must be the one this launcher generates, and the value must still be
    a safe relative filename, because it becomes a path component.
    """
    from app.domain.artifact_audit_operations import is_canonical_operation_id

    if not is_canonical_operation_id(value):
        return False
    if not is_safe_relative_filename(value):
        return False
    try:
        return uuid.UUID(str(value)).version == OPERATION_ID_UUID_VERSION
    except (ValueError, AttributeError, TypeError):
        return False


def resolve_restore_dir(database_path: Path) -> Path:
    """The Restore directory for one database path.

    Mirrors `resolve_backup_dir`: the user-data `restore/` directory when the
    database is the resolved user database or the user-data directory was set
    explicitly, otherwise a `restore/` directory next to the configured
    development database. Computes a path and creates nothing.
    """
    # Imported here rather than at module import time: `backend/` only joins
    # `sys.path` at runtime, through `launcher.runtime.ensure_backend_import_path`.
    from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths

    resolved_database_path = Path(database_path)
    user_paths = resolve_user_data_paths()
    user_data_dir_explicit = bool(os.environ.get(USER_DATA_DIR_ENV))
    if resolved_database_path == user_paths.database_path or user_data_dir_explicit:
        return user_paths.base_dir / RESTORE_DIRNAME
    return resolved_database_path.parent / RESTORE_DIRNAME


def is_safe_relative_filename(value: object) -> bool:
    """Whether `value` is a plain relative filename safe to persist and re-resolve.

    Reuses the backend's accepted safe-filename rule rather than restating it, so
    the durable Restore record and the CR-009 ledger cannot drift apart on what
    "safe relative filename" means.
    """
    from app.domain.artifact_audit_operations import is_safe_artifact_filename

    return is_safe_artifact_filename(value)


@dataclass(frozen=True)
class RestoreWorkspace:
    """The launcher-owned Restore boundary for one database path."""

    restore_dir: Path
    database_path: Path

    @classmethod
    def for_database(cls, database_path: Path) -> "RestoreWorkspace":
        resolved = Path(database_path)
        return cls(restore_dir=resolve_restore_dir(resolved), database_path=resolved)

    # ------------------------------------------------------------------ paths

    @property
    def record_path(self) -> Path:
        return self.restore_dir / OPERATION_RECORD_FILENAME

    @property
    def lock_path(self) -> Path:
        return self.restore_dir / INSTANCE_LOCK_FILENAME

    def operation_dir(self, operation_id: str) -> Path:
        """The isolated directory for one attempt.

        The operation ID is validated as a canonical launcher-generated UUID
        before it is joined, so a record that somehow carried a traversal
        spelling — or merely an arbitrary safe filename naming some other
        directory — cannot reach outside this attempt's boundary when it is read
        back.
        """
        if not is_launcher_operation_id(operation_id):
            raise RestoreWorkspaceError(
                "Restore operation identity is not a canonical launcher-generated UUID."
            )
        return self.restore_dir / operation_id

    def staged_candidate_path(self, operation_id: str) -> Path:
        return self.operation_dir(operation_id) / STAGED_CANDIDATE_FILENAME

    # ----------------------------------------------------------------- create

    def ensure_restore_dir(self) -> Path:
        try:
            self.restore_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise RestoreWorkspaceError(
                f"Could not create the Restore directory: {type(exc).__name__}"
            ) from exc
        return self.restore_dir

    def create_operation_dir(self, operation_id: str) -> Path:
        """Create one isolated operation directory, exclusively.

        `exist_ok=False` is the ownership proof. A directory that already exists
        under a freshly generated operation ID is not this attempt's, and
        continuing into it would mean writing beside artifacts of unknown origin.
        """
        self.ensure_restore_dir()
        operation_dir = self.operation_dir(operation_id)
        try:
            operation_dir.mkdir(parents=False, exist_ok=False)
        except OSError as exc:
            raise RestoreWorkspaceError(
                f"Could not create an isolated Restore operation directory: {type(exc).__name__}"
            ) from exc
        return operation_dir

    # ------------------------------------------------------------- ownership

    def owns(self, candidate: Path) -> bool:
        """Whether `candidate` provably resolves inside this Restore directory.

        `resolve()` follows symlinks, which is the point: a symlink planted
        inside the directory that points outside it must fail this check, and a
        purely textual prefix comparison would not notice.
        """
        try:
            root = self.restore_dir.resolve()
            resolved = Path(candidate).resolve(strict=False)
        except (OSError, RuntimeError):
            return False
        return resolved == root or root in resolved.parents

    def is_owned_temp(self, candidate: Path) -> bool:
        """Whether `candidate` is a scratch file this launcher created."""
        name = Path(candidate).name
        return (
            self.owns(candidate)
            and name.startswith(OWNED_TEMP_PREFIX)
            and name.endswith(OWNED_TEMP_SUFFIX)
        )

    # --------------------------------------------------------------- cleanup

    def clean_owned_staging(self, operation_id: str) -> None:
        """Remove only this operation's own staging directory.

        Called when an operation reaches `aborted` or `completed`, never when it
        reaches `recovery_blocked` — that phase preserves every piece of
        evidence. The verified safety copy lives in `backups/`, outside this
        directory entirely, so no cleanup path can reach it.

        Every failure is swallowed on purpose: leaving a stale staged candidate
        behind is harmless, while turning a successful Restore into a reported
        failure over an `unlink` is not.
        """
        try:
            operation_dir = self.operation_dir(operation_id)
        except RestoreWorkspaceError:
            return
        if not self.owns(operation_dir) or not operation_dir.is_dir():
            return
        try:
            entries = list(operation_dir.iterdir())
        except OSError:
            return
        for entry in entries:
            # One flat directory by construction: the staged candidate and, at
            # most, scratch files this launcher created. A subdirectory is not
            # something this code produces, so it is left alone rather than
            # recursively removed.
            if not entry.is_file() or entry.is_symlink() or not self.owns(entry):
                continue
            try:
                entry.unlink()
            except OSError:
                return
        try:
            operation_dir.rmdir()
        except OSError:
            return

    def clean_owned_temp_files(self) -> None:
        """Remove leftover publication scratch files, and nothing else.

        Matched by the launcher's own prefix and suffix and confirmed to resolve
        inside the Restore directory. A file that fails either test is left where
        it is: this cleanup exists to tidy interrupted publications, not to make
        room by deleting things it cannot account for.
        """
        if not self.restore_dir.is_dir():
            return
        try:
            entries = list(self.restore_dir.iterdir())
        except OSError:
            return
        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                continue
            if not self.is_owned_temp(entry):
                continue
            try:
                entry.unlink()
            except OSError:
                continue
