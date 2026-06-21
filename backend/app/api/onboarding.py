from fastapi import APIRouter, HTTPException, status

from app.models.onboarding import OnboardingState
from app.schemas.onboarding import CompleteOnboardingStepRequest, OnboardingStateResponse
from app.services.onboarding import ONBOARDING_STEPS, OnboardingService, OnboardingStepError

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("", response_model=OnboardingStateResponse)
def get_onboarding_state() -> OnboardingStateResponse:
    return _response(OnboardingService().get_state())


@router.post("/start", response_model=OnboardingStateResponse)
def start_onboarding() -> OnboardingStateResponse:
    return _response(OnboardingService().start())


@router.post("/complete-step", response_model=OnboardingStateResponse)
def complete_onboarding_step(payload: CompleteOnboardingStepRequest) -> OnboardingStateResponse:
    try:
        state = OnboardingService().complete_step(payload.step)
    except OnboardingStepError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неизвестный шаг первичной настройки.",
        ) from exc
    return _response(state)


@router.post("/complete", response_model=OnboardingStateResponse)
def complete_onboarding() -> OnboardingStateResponse:
    return _response(OnboardingService().complete())


@router.post("/skip", response_model=OnboardingStateResponse)
def skip_onboarding() -> OnboardingStateResponse:
    return _response(OnboardingService().skip())


@router.post("/reset", response_model=OnboardingStateResponse)
def reset_onboarding() -> OnboardingStateResponse:
    return _response(OnboardingService().reset())


def _response(state: OnboardingState) -> OnboardingStateResponse:
    return OnboardingStateResponse(
        has_started=state.has_started,
        is_completed=state.is_completed,
        current_step=state.current_step,
        completed_steps=list(state.completed_steps),
        dismissed_hints=list(state.dismissed_hints),
        available_steps=list(ONBOARDING_STEPS),
        created_at=state.created_at,
        updated_at=state.updated_at,
    )
