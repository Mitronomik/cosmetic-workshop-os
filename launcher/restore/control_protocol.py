"""Typed launcher-internal contracts for the C4-II-A Restore control flow.

The browser never owns a filesystem path. A source-selection adapter returns a
path only inside the launcher process. The closed A2 unavailable adapter remains
the default for direct/test construction; A3 production runtime injects the
launcher-owned native macOS adapter explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import Event
from typing import Protocol


class SourceSelectionState(str, Enum):
    SELECTED = "selected"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class SourceSelectionResult:
    """Launcher-private picker result.

    ``selected_source`` is intentionally absent unless the launcher-owned adapter
    returned ``SELECTED``. This type is never serialized to HTTP.
    """

    state: SourceSelectionState
    selected_source: Path | None = None

    @classmethod
    def selected(cls, path: Path) -> "SourceSelectionResult":
        return cls(SourceSelectionState.SELECTED, Path(path))

    @classmethod
    def cancelled(cls) -> "SourceSelectionResult":
        return cls(SourceSelectionState.CANCELLED)

    @classmethod
    def unavailable(cls) -> "SourceSelectionResult":
        return cls(SourceSelectionState.UNAVAILABLE)


class SourceSelectionAdapter(Protocol):
    """Launcher-owned source-selection seam used by A2/A3.

    Production A3 injects the native adapter at launcher runtime. Tests may inject
    fakes directly; HTTP requests never carry a source path.
    """

    def select(self, cancel_event: Event) -> SourceSelectionResult:
        ...


class UnavailableSourceSelectionAdapter:
    """Closed A2 fail-closed/default adapter retained for direct construction."""

    def select(self, cancel_event: Event) -> SourceSelectionResult:
        del cancel_event
        return SourceSelectionResult.unavailable()


class ControlViewState(str, Enum):
    IDLE = "idle"
    SELECTING = "selecting"
    VALIDATING = "validating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    TECHNICAL_FAILURE = "technical_failure"


@dataclass(frozen=True)
class ControlStateSnapshot:
    """Presentation-safe state returned by the launcher control plane."""

    run_id: str
    state: ControlViewState
    generation: int
    filename: str = ""
    message: str = ""
    compatibility: str | None = None
    failure: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "state": self.state.value,
            "generation": self.generation,
            "filename": self.filename,
            "message": self.message,
            "compatibility": self.compatibility,
            "failure": self.failure,
        }


@dataclass(frozen=True)
class CommandReply:
    """Safe idempotent result retained for the highest consumed command."""

    ok: bool
    code: str
    command_seq: int
    state: ControlStateSnapshot

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "code": self.code,
            "command_seq": self.command_seq,
            "state": self.state.to_dict(),
        }


class ControlSessionError(RuntimeError):
    """Safe protocol/session refusal with an HTTP status and stable code."""

    def __init__(self, status: int, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
