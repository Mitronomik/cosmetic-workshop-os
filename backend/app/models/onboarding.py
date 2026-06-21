from dataclasses import dataclass


@dataclass(frozen=True)
class OnboardingState:
    has_started: bool
    is_completed: bool
    current_step: str
    completed_steps: tuple[str, ...]
    dismissed_hints: tuple[str, ...]
    created_at: str | None
    updated_at: str | None
