"""Exact-run Restore control-session coordination for C4-II-A2.

This module owns authentication lifetime, command ordering and worker publication.
It deliberately owns no HTTP parsing and no filesystem picker implementation.
Long selection/validation work runs on one launcher-owned worker so heartbeat,
state and cancel requests remain serviceable by the concurrent HTTP boundary.
"""

from __future__ import annotations

import hmac
import secrets
import threading
import time
from typing import Callable

from launcher.restore.control_protocol import (
    CommandReply,
    ControlSessionError,
    ControlStateSnapshot,
    ControlViewState,
    SourceSelectionAdapter,
    SourceSelectionState,
    UnavailableSourceSelectionAdapter,
)
from launcher.restore.validation_session import (
    CandidatePreparationState,
    RestoreCandidatePreparationService,
)

BOOTSTRAP_RANDOM_BYTES = 32
SESSION_RANDOM_BYTES = 32
HEARTBEAT_INTERVAL_SECONDS = 15
SESSION_EXPIRY_SECONDS = 60
EXPIRY_POLL_SECONDS = 0.5

PICKER_UNAVAILABLE_MESSAGE = (
    "Выбор резервной копии пока недоступен. Перезапустите приложение после обновления."
)
SELECTION_CANCELLED_MESSAGE = "Выбор резервной копии отменён. Данные мастерской не изменились."
SESSION_EXPIRED_MESSAGE = "Сессия восстановления завершена. Данные мастерской не изменились."
ACTION_IN_PROGRESS_MESSAGE = "Предыдущая операция выбора или проверки ещё выполняется."
NOTHING_TO_CANCEL_MESSAGE = "Активной проверки резервной копии нет."


class RestoreControlSession:
    """Own one launcher's bootstrap, browser session and selection generation."""

    def __init__(
        self,
        candidate_service: RestoreCandidatePreparationService,
        *,
        picker_adapter: SourceSelectionAdapter | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._candidate_service = candidate_service
        self._picker = picker_adapter or UnavailableSourceSelectionAdapter()
        self._clock = clock
        self._lock = threading.RLock()
        self._bootstrap_capability = secrets.token_urlsafe(BOOTSTRAP_RANDOM_BYTES)
        self._bootstrap_consumed = False
        self._session_token: str | None = None
        self._last_authenticated_at: float | None = None
        self._selection_generation = 0
        self._state = ControlStateSnapshot(
            run_id=candidate_service.run_id,
            state=ControlViewState.IDLE,
            generation=0,
        )
        self._highest_command_seq = 0
        self._last_command_request_id: str | None = None
        self._last_command_name: str | None = None
        self._last_command_reply: CommandReply | None = None
        self._worker: threading.Thread | None = None
        self._worker_cancel: threading.Event | None = None
        self._closed = False
        self._expiry_stop = threading.Event()
        self._expiry_thread: threading.Thread | None = None

    @property
    def run_id(self) -> str:
        return self._candidate_service.run_id

    @property
    def bootstrap_capability(self) -> str:
        """Launcher-private one-use capability; A2 never puts it in product navigation."""

        return self._bootstrap_capability

    @property
    def heartbeat_interval_seconds(self) -> int:
        return HEARTBEAT_INTERVAL_SECONDS

    @property
    def session_expiry_seconds(self) -> int:
        return SESSION_EXPIRY_SECONDS

    @property
    def current_state(self) -> ControlStateSnapshot:
        with self._lock:
            return self._state

    @property
    def session_active(self) -> bool:
        with self._lock:
            self._expire_locked(self._clock())
            return self._session_token is not None and not self._closed

    def start_expiry_monitor(self) -> None:
        with self._lock:
            if self._closed:
                raise ControlSessionError(503, "control_plane_closed")
            if self._expiry_thread is not None and self._expiry_thread.is_alive():
                return
            self._expiry_stop.clear()
            thread = threading.Thread(
                target=self._expiry_loop,
                name="restore-control-expiry",
                daemon=True,
            )
            self._expiry_thread = thread
            thread.start()

    def _expiry_loop(self) -> None:
        while not self._expiry_stop.wait(EXPIRY_POLL_SECONDS):
            self.expire_if_needed()

    def expire_if_needed(self) -> bool:
        with self._lock:
            return self._expire_locked(self._clock())

    def _expire_locked(self, now: float) -> bool:
        if self._closed or self._session_token is None or self._last_authenticated_at is None:
            return False
        if now - self._last_authenticated_at < SESSION_EXPIRY_SECONDS:
            return False
        self._session_token = None
        self._last_authenticated_at = None
        self._selection_generation += 1
        self._candidate_service.cancel()
        if self._worker_cancel is not None:
            self._worker_cancel.set()
        self._state = ControlStateSnapshot(
            run_id=self.run_id,
            state=ControlViewState.CANCELLED,
            generation=self._selection_generation,
            message=SESSION_EXPIRED_MESSAGE,
            failure="session_expired",
        )
        return True

    def bootstrap(self, presented_capability: str) -> tuple[str, ControlStateSnapshot]:
        """Atomically compare-and-consume the one-use bootstrap capability."""

        if not isinstance(presented_capability, str):
            raise ControlSessionError(400, "invalid_bootstrap_request")
        with self._lock:
            if self._closed:
                raise ControlSessionError(503, "control_plane_closed")
            if self._bootstrap_consumed:
                raise ControlSessionError(401, "bootstrap_invalid")
            if not hmac.compare_digest(presented_capability, self._bootstrap_capability):
                raise ControlSessionError(401, "bootstrap_invalid")

            # Consumption happens before the new token becomes observable, so two
            # concurrent exchanges can never both pass the capability check. The
            # consumed secret is also cleared from coordinator memory immediately.
            self._bootstrap_consumed = True
            self._bootstrap_capability = ""
            session_token = secrets.token_urlsafe(SESSION_RANDOM_BYTES)
            self._session_token = session_token
            self._last_authenticated_at = self._clock()
            return session_token, self._state

    def _authenticate_locked(self, presented_token: str, *, touch: bool = True) -> None:
        self._expire_locked(self._clock())
        if self._closed or self._session_token is None:
            raise ControlSessionError(401, "invalid_session")
        if not isinstance(presented_token, str) or not hmac.compare_digest(
            presented_token, self._session_token
        ):
            raise ControlSessionError(401, "invalid_session")
        if touch:
            self._last_authenticated_at = self._clock()

    def get_state(self, presented_token: str) -> ControlStateSnapshot:
        with self._lock:
            self._authenticate_locked(presented_token)
            return self._state

    def heartbeat(self, presented_token: str) -> ControlStateSnapshot:
        with self._lock:
            self._authenticate_locked(presented_token)
            return self._state

    def _consume_command_locked(
        self,
        *,
        name: str,
        request_id: str,
        command_seq: int,
    ) -> CommandReply | None:
        """Consume exactly-next sequence before any business precondition check."""

        if command_seq < self._highest_command_seq:
            raise ControlSessionError(409, "command_sequence_stale")
        if command_seq > self._highest_command_seq + 1:
            raise ControlSessionError(409, "command_sequence_future")
        if command_seq == self._highest_command_seq:
            if (
                request_id != self._last_command_request_id
                or name != self._last_command_name
                or self._last_command_reply is None
            ):
                raise ControlSessionError(409, "command_sequence_conflict")
            return self._last_command_reply

        self._highest_command_seq = command_seq
        self._last_command_request_id = request_id
        self._last_command_name = name
        self._last_command_reply = CommandReply(
            ok=True,
            code="command_consumed",
            command_seq=command_seq,
            state=self._state,
        )
        return None

    def _record_reply_locked(self, reply: CommandReply) -> CommandReply:
        self._last_command_reply = reply
        return reply

    def select(
        self,
        presented_token: str,
        *,
        request_id: str,
        command_seq: int,
    ) -> CommandReply:
        with self._lock:
            self._authenticate_locked(presented_token)
            retry = self._consume_command_locked(
                name="restore.select",
                request_id=request_id,
                command_seq=command_seq,
            )
            if retry is not None:
                return retry

            if self._worker is not None and self._worker.is_alive():
                return self._record_reply_locked(
                    CommandReply(
                        ok=False,
                        code="action_in_progress",
                        command_seq=command_seq,
                        state=ControlStateSnapshot(
                            run_id=self.run_id,
                            state=self._state.state,
                            generation=self._state.generation,
                            filename=self._state.filename,
                            message=ACTION_IN_PROGRESS_MESSAGE,
                            compatibility=self._state.compatibility,
                            failure="action_in_progress",
                        ),
                    )
                )

            self._selection_generation += 1
            generation = self._selection_generation
            self._candidate_service.cancel()
            cancel_event = threading.Event()
            self._worker_cancel = cancel_event
            self._state = ControlStateSnapshot(
                run_id=self.run_id,
                state=ControlViewState.SELECTING,
                generation=generation,
            )
            reply = self._record_reply_locked(
                CommandReply(
                    ok=True,
                    code="select_started",
                    command_seq=command_seq,
                    state=self._state,
                )
            )
            worker = threading.Thread(
                target=self._run_selection_worker,
                args=(generation, command_seq, request_id, cancel_event),
                name="restore-control-selection",
                daemon=True,
            )
            self._worker = worker
            worker.start()
            return reply

    def cancel(
        self,
        presented_token: str,
        *,
        request_id: str,
        command_seq: int,
    ) -> CommandReply:
        with self._lock:
            self._authenticate_locked(presented_token)
            retry = self._consume_command_locked(
                name="restore.cancel",
                request_id=request_id,
                command_seq=command_seq,
            )
            if retry is not None:
                return retry

            was_actionable = (
                (self._worker is not None and self._worker.is_alive())
                or self._state.state is ControlViewState.ACCEPTED
            )
            self._selection_generation += 1
            self._candidate_service.cancel()
            if self._worker_cancel is not None:
                self._worker_cancel.set()

            if was_actionable:
                self._state = ControlStateSnapshot(
                    run_id=self.run_id,
                    state=ControlViewState.CANCELLED,
                    generation=self._selection_generation,
                    message=SELECTION_CANCELLED_MESSAGE,
                    failure="cancelled",
                )
                code = "cancelled"
                ok = True
            else:
                self._state = ControlStateSnapshot(
                    run_id=self.run_id,
                    state=self._state.state,
                    generation=self._selection_generation,
                    filename=self._state.filename,
                    message=NOTHING_TO_CANCEL_MESSAGE,
                    compatibility=self._state.compatibility,
                    failure="nothing_to_cancel",
                )
                code = "nothing_to_cancel"
                ok = False

            return self._record_reply_locked(
                CommandReply(
                    ok=ok,
                    code=code,
                    command_seq=command_seq,
                    state=self._state,
                )
            )

    def _worker_generation_current_locked(self, generation: int) -> bool:
        return (
            not self._closed
            and self._session_token is not None
            and generation == self._selection_generation
        )

    def _update_worker_reply_locked(
        self,
        *,
        command_seq: int,
        request_id: str,
        ok: bool,
        code: str,
    ) -> None:
        if (
            self._highest_command_seq == command_seq
            and self._last_command_request_id == request_id
            and self._last_command_name == "restore.select"
        ):
            self._last_command_reply = CommandReply(
                ok=ok,
                code=code,
                command_seq=command_seq,
                state=self._state,
            )

    def _publish_simple_worker_result(
        self,
        *,
        generation: int,
        command_seq: int,
        request_id: str,
        state: ControlViewState,
        ok: bool,
        code: str,
        message: str,
        failure: str | None,
    ) -> None:
        with self._lock:
            if not self._worker_generation_current_locked(generation):
                return
            self._state = ControlStateSnapshot(
                run_id=self.run_id,
                state=state,
                generation=generation,
                message=message,
                failure=failure,
            )
            self._update_worker_reply_locked(
                command_seq=command_seq,
                request_id=request_id,
                ok=ok,
                code=code,
            )

    def _run_selection_worker(
        self,
        generation: int,
        command_seq: int,
        request_id: str,
        cancel_event: threading.Event,
    ) -> None:
        try:
            try:
                selected = self._picker.select(cancel_event)
            except Exception:  # noqa: BLE001 - never surface adapter details to HTTP
                self._publish_simple_worker_result(
                    generation=generation,
                    command_seq=command_seq,
                    request_id=request_id,
                    state=ControlViewState.TECHNICAL_FAILURE,
                    ok=False,
                    code="selection_failed",
                    message="Не удалось открыть выбор резервной копии. Данные мастерской не изменились.",
                    failure="technical_failure",
                )
                return

            if selected.state is SourceSelectionState.UNAVAILABLE:
                self._publish_simple_worker_result(
                    generation=generation,
                    command_seq=command_seq,
                    request_id=request_id,
                    state=ControlViewState.IDLE,
                    ok=False,
                    code="picker_unavailable",
                    message=PICKER_UNAVAILABLE_MESSAGE,
                    failure="picker_unavailable",
                )
                return
            if selected.state is SourceSelectionState.CANCELLED or cancel_event.is_set():
                self._publish_simple_worker_result(
                    generation=generation,
                    command_seq=command_seq,
                    request_id=request_id,
                    state=ControlViewState.CANCELLED,
                    ok=True,
                    code="selection_cancelled",
                    message=SELECTION_CANCELLED_MESSAGE,
                    failure="cancelled",
                )
                return
            if selected.selected_source is None:
                self._publish_simple_worker_result(
                    generation=generation,
                    command_seq=command_seq,
                    request_id=request_id,
                    state=ControlViewState.TECHNICAL_FAILURE,
                    ok=False,
                    code="selection_failed",
                    message="Не удалось открыть выбор резервной копии. Данные мастерской не изменились.",
                    failure="technical_failure",
                )
                return

            with self._lock:
                if not self._worker_generation_current_locked(generation):
                    return
                self._state = ControlStateSnapshot(
                    run_id=self.run_id,
                    state=ControlViewState.VALIDATING,
                    generation=generation,
                )
                self._update_worker_reply_locked(
                    command_seq=command_seq,
                    request_id=request_id,
                    ok=True,
                    code="validation_started",
                )

            candidate = self._candidate_service.prepare_restore_candidate(
                selected.selected_source
            )

            with self._lock:
                if not self._worker_generation_current_locked(generation):
                    return
                if candidate.state is CandidatePreparationState.ACCEPTED:
                    view_state = ControlViewState.ACCEPTED
                    code = "candidate_accepted"
                    ok = True
                elif candidate.state is CandidatePreparationState.REJECTED:
                    view_state = ControlViewState.REJECTED
                    code = "candidate_rejected"
                    ok = False
                elif candidate.state is CandidatePreparationState.CANCELLED:
                    view_state = ControlViewState.CANCELLED
                    code = "validation_cancelled"
                    ok = True
                else:
                    view_state = ControlViewState.TECHNICAL_FAILURE
                    code = "validation_failed"
                    ok = False

                self._state = ControlStateSnapshot(
                    run_id=self.run_id,
                    state=view_state,
                    generation=generation,
                    filename=candidate.filename,
                    message=candidate.message,
                    compatibility=(
                        candidate.compatibility.value if candidate.compatibility else None
                    ),
                    failure=candidate.failure.value if candidate.failure else None,
                )
                self._update_worker_reply_locked(
                    command_seq=command_seq,
                    request_id=request_id,
                    ok=ok,
                    code=code,
                )
        finally:
            with self._lock:
                if self._worker is threading.current_thread():
                    self._worker = None
                    self._worker_cancel = None

    def close(self) -> None:
        """Invalidate authority immediately, then quiesce worker before A1 cleanup."""

        self._expiry_stop.set()
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._bootstrap_capability = ""
            self._session_token = None
            self._last_authenticated_at = None
            self._selection_generation += 1
            self._candidate_service.cancel()
            if self._worker_cancel is not None:
                self._worker_cancel.set()
            worker = self._worker
            expiry_thread = self._expiry_thread

        if worker is not None and worker is not threading.current_thread():
            worker.join()
        if expiry_thread is not None and expiry_thread is not threading.current_thread():
            expiry_thread.join(timeout=2.0)
        self._candidate_service.close()
