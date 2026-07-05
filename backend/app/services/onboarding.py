from __future__ import annotations

from datetime import datetime, timezone
import json

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.db.transactions import transaction
import sqlite3
from app.models.onboarding import OnboardingState
from app.repositories.audit import AuditLogRepository

ONBOARDING_SETTING_KEY = "onboarding.state"
ONBOARDING_STEPS: tuple[str, ...] = (
    "welcome",
    "data_location",
    "first_ingredient",
    "first_ingredient_lot",
    "first_packaging",
    "first_recipe",
    "first_client",
    "first_client_recipe",
    "first_order",
    "production_readiness",
    "first_production",
    "alerts_and_purchases",
    "backup_and_export",
    "import_draft",
)

LEGACY_STEP_MAP: dict[str, str] = {
    "first_backup": "backup_and_export",
}


class OnboardingStepError(ValueError):
    pass


class OnboardingService:
    def __init__(self, config: DatabaseConfig | None = None) -> None:
        self.config = config or get_database_config()
        self.audit = AuditLogRepository(self.config)

    def get_state(self) -> OnboardingState:
        raw = self._read_raw_state()
        if raw is None:
            return self._default_state()
        return self._state_from_json(raw)

    def start(self) -> OnboardingState:
        state = self.get_state()
        now = _now_iso()
        created_at = state.created_at or now
        next_state = OnboardingState(
            has_started=True,
            is_completed=False,
            current_step=state.current_step if state.current_step in ONBOARDING_STEPS else ONBOARDING_STEPS[0],
            completed_steps=state.completed_steps,
            dismissed_hints=state.dismissed_hints,
            created_at=created_at,
            updated_at=now,
        )
        with transaction(self.config) as connection:
            self._save_state(next_state, connection=connection)
            self.audit.create_log(
                action="onboarding.started",
                entity_type="onboarding",
                entity_id=None,
                summary="Пользователь начал первичную настройку.",
                metadata={"current_step": next_state.current_step},
                connection=connection,
            )
        return next_state

    def complete_step(self, step: str) -> OnboardingState:
        if step not in ONBOARDING_STEPS:
            raise OnboardingStepError(f"Unknown onboarding step: {step}")
        state = self.get_state()
        now = _now_iso()
        completed = list(state.completed_steps)
        if step not in completed:
            completed.append(step)
        current_step = _next_step(tuple(completed))
        next_state = OnboardingState(
            has_started=True,
            is_completed=state.is_completed or len(completed) == len(ONBOARDING_STEPS),
            current_step=current_step,
            completed_steps=tuple(completed),
            dismissed_hints=state.dismissed_hints,
            created_at=state.created_at or now,
            updated_at=now,
        )
        with transaction(self.config) as connection:
            self._save_state(next_state, connection=connection)
            self.audit.create_log(
                action="onboarding.step_completed",
                entity_type="onboarding",
                entity_id=step,
                summary="Шаг первичной настройки отмечен выполненным.",
                metadata={"step": step, "next_step": current_step},
                connection=connection,
            )
        return next_state

    def skip(self) -> OnboardingState:
        state = self.get_state()
        now = _now_iso()
        next_state = OnboardingState(
            has_started=True,
            is_completed=True,
            current_step=state.current_step if state.current_step in ONBOARDING_STEPS else _next_step(state.completed_steps),
            completed_steps=state.completed_steps,
            dismissed_hints=state.dismissed_hints,
            created_at=state.created_at or now,
            updated_at=now,
        )
        with transaction(self.config) as connection:
            self._save_state(next_state, connection=connection)
            self.audit.create_log(
                action="onboarding.skipped",
                entity_type="onboarding",
                entity_id=None,
                summary="Пользователь закрыл чек-лист первичной настройки без отметки всех шагов.",
                metadata={"current_step": next_state.current_step, "completed_steps": list(next_state.completed_steps)},
                connection=connection,
            )
        return next_state

    def complete(self) -> OnboardingState:
        state = self.get_state()
        now = _now_iso()
        next_state = OnboardingState(
            has_started=True,
            is_completed=True,
            current_step=ONBOARDING_STEPS[-1],
            completed_steps=ONBOARDING_STEPS,
            dismissed_hints=state.dismissed_hints,
            created_at=state.created_at or now,
            updated_at=now,
        )
        with transaction(self.config) as connection:
            self._save_state(next_state, connection=connection)
            self.audit.create_log(
                action="onboarding.completed",
                entity_type="onboarding",
                entity_id=None,
                summary="Первичная настройка завершена пользователем.",
                connection=connection,
            )
        return next_state

    def reset(self) -> OnboardingState:
        state = self._default_state()
        self._save_state(state)
        return state

    def _read_raw_state(self) -> str | None:
        with session(self.config) as connection:
            row = connection.execute("SELECT value FROM app_settings WHERE key = ?", (ONBOARDING_SETTING_KEY,)).fetchone()
        return None if row is None else row["value"]

    def _save_state(self, state: OnboardingState, *, connection: sqlite3.Connection | None = None) -> None:
        payload = json.dumps(_state_to_payload(state), ensure_ascii=False)
        if connection is None:
            with session(self.config) as managed_connection:
                self._write_state_payload(payload, managed_connection)
            return
        self._write_state_payload(payload, connection)

    def _write_state_payload(self, payload: str, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
                INSERT INTO app_settings (key, value, value_type, description)
                VALUES (?, ?, 'json', 'First-run onboarding state for the local workspace.')
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    value_type = excluded.value_type,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP
                """,
            (ONBOARDING_SETTING_KEY, payload),
        )

    def _default_state(self) -> OnboardingState:
        return OnboardingState(False, False, ONBOARDING_STEPS[0], (), (), None, None)

    def _state_from_json(self, raw: str) -> OnboardingState:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return self._default_state()
        completed = _normalize_completed_steps(payload.get("completed_steps", []))
        current_step = _normalize_step(payload.get("current_step")) or _next_step(completed)
        is_completed = bool(payload.get("is_completed", False))
        return OnboardingState(
            has_started=bool(payload.get("has_started", False)),
            is_completed=is_completed,
            current_step=current_step,
            completed_steps=completed,
            dismissed_hints=tuple(str(hint) for hint in payload.get("dismissed_hints", [])),
            created_at=payload.get("created_at"),
            updated_at=payload.get("updated_at"),
        )


def _normalize_step(step: object) -> str | None:
    if not isinstance(step, str):
        return None
    mapped = LEGACY_STEP_MAP.get(step, step)
    return mapped if mapped in ONBOARDING_STEPS else None


def _normalize_completed_steps(steps: object) -> tuple[str, ...]:
    if not isinstance(steps, list):
        return ()
    normalized: list[str] = []
    for raw_step in steps:
        step = _normalize_step(raw_step)
        if step and step not in normalized:
            normalized.append(step)
    return tuple(normalized)


def _next_step(completed_steps: tuple[str, ...]) -> str:
    for step in ONBOARDING_STEPS:
        if step not in completed_steps:
            return step
    return ONBOARDING_STEPS[-1]


def _state_to_payload(state: OnboardingState) -> dict[str, object]:
    return {
        "has_started": state.has_started,
        "is_completed": state.is_completed,
        "current_step": state.current_step,
        "completed_steps": list(state.completed_steps),
        "dismissed_hints": list(state.dismissed_hints),
        "created_at": state.created_at,
        "updated_at": state.updated_at,
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
