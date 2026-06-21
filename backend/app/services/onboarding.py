from __future__ import annotations

from datetime import datetime, timezone
import json

from app.db.config import DatabaseConfig, get_database_config
from app.db.connection import session
from app.models.onboarding import OnboardingState
from app.repositories.audit import AuditLogRepository

ONBOARDING_SETTING_KEY = "onboarding.state"
ONBOARDING_STEPS: tuple[str, ...] = (
    "welcome",
    "data_location",
    "first_ingredient",
    "first_recipe",
    "first_client",
    "first_order",
    "first_backup",
)


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
        self._save_state(next_state)
        self.audit.create_log(
            action="onboarding.started",
            entity_type="onboarding",
            entity_id=None,
            summary="Пользователь начал первичную настройку.",
            metadata={"current_step": next_state.current_step},
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
            is_completed=state.is_completed,
            current_step=current_step,
            completed_steps=tuple(completed),
            dismissed_hints=state.dismissed_hints,
            created_at=state.created_at or now,
            updated_at=now,
        )
        self._save_state(next_state)
        self.audit.create_log(
            action="onboarding.step_completed",
            entity_type="onboarding",
            entity_id=step,
            summary="Шаг первичной настройки отмечен выполненным.",
            metadata={"step": step, "next_step": current_step},
        )
        return next_state

    def complete(self) -> OnboardingState:
        state = self.get_state()
        now = _now_iso()
        next_state = OnboardingState(
            has_started=True,
            is_completed=True,
            current_step="first_backup",
            completed_steps=ONBOARDING_STEPS,
            dismissed_hints=state.dismissed_hints,
            created_at=state.created_at or now,
            updated_at=now,
        )
        self._save_state(next_state)
        self.audit.create_log(
            action="onboarding.completed",
            entity_type="onboarding",
            entity_id=None,
            summary="Первичная настройка завершена или пропущена пользователем.",
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

    def _save_state(self, state: OnboardingState) -> None:
        payload = json.dumps(_state_to_payload(state), ensure_ascii=False)
        with session(self.config) as connection:
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
        completed = tuple(step for step in payload.get("completed_steps", []) if step in ONBOARDING_STEPS)
        current_step = payload.get("current_step") if payload.get("current_step") in ONBOARDING_STEPS else _next_step(completed)
        return OnboardingState(
            has_started=bool(payload.get("has_started", False)),
            is_completed=bool(payload.get("is_completed", False)),
            current_step=current_step,
            completed_steps=completed,
            dismissed_hints=tuple(str(hint) for hint in payload.get("dismissed_hints", [])),
            created_at=payload.get("created_at"),
            updated_at=payload.get("updated_at"),
        )


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
