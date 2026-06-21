from pydantic import BaseModel


class OnboardingStateResponse(BaseModel):
    has_started: bool
    is_completed: bool
    current_step: str
    completed_steps: list[str]
    dismissed_hints: list[str]
    available_steps: list[str]
    created_at: str | None
    updated_at: str | None


class CompleteOnboardingStepRequest(BaseModel):
    step: str
