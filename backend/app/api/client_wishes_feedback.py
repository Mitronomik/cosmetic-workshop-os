from fastapi import APIRouter, HTTPException, status

from app.domain.client_wishes_feedback import ClientFeedbackDraft, ClientWishDraft, ClientWishStatusUpdate
from app.domain.errors import DomainValidationError
from app.models.client_wishes_feedback import ClientFeedback, ClientWish
from app.repositories.client_recipes import ClientRecipeNotFoundError
from app.repositories.client_wishes_feedback import ClientFeedbackNotFoundError, ClientWishNotFoundError
from app.repositories.clients import ClientNotFoundError
from app.schemas.client_wishes_feedback import ClientFeedbackCreateRequest, ClientFeedbackListResponse, ClientFeedbackResponse, ClientWishCreateRequest, ClientWishesResponse, ClientWishResponse, ClientWishStatusUpdateRequest
from app.services.client_wishes_feedback import ClientFeedbackService, ClientRecipeClientMismatchError, ClientWishFeedbackClientInactiveError, ClientWishService

router = APIRouter(tags=["client-wishes-feedback"])


@router.get("/clients/{client_id}/wishes", response_model=ClientWishesResponse)
def list_client_wishes(client_id: int, include_inactive: bool = False):
    try:
        return ClientWishesResponse(wishes=[_wish(w) for w in ClientWishService().list_for_client(client_id, include_inactive=include_inactive)])
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client was not found.") from exc


@router.post("/clients/{client_id}/wishes", response_model=ClientWishResponse, status_code=status.HTTP_201_CREATED)
def create_client_wish(client_id: int, payload: ClientWishCreateRequest):
    try:
        draft = ClientWishDraft.create(client_id=client_id, **payload.model_dump())
        return _wish(ClientWishService().create(draft))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except (ClientNotFoundError, ClientRecipeNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client or linked client recipe was not found.") from exc
    except (ClientWishFeedbackClientInactiveError, ClientRecipeClientMismatchError) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/client-wishes/{wish_id}", response_model=ClientWishResponse)
def get_client_wish(wish_id: int):
    try:
        return _wish(ClientWishService().get(wish_id))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientWishNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client wish was not found.") from exc


@router.put("/client-wishes/{wish_id}/status", response_model=ClientWishResponse)
def update_client_wish_status(wish_id: int, payload: ClientWishStatusUpdateRequest):
    try:
        return _wish(ClientWishService().update_status(wish_id, ClientWishStatusUpdate.create(**payload.model_dump())))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientWishNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client wish was not found.") from exc


@router.post("/client-wishes/{wish_id}/archive", response_model=ClientWishResponse)
def archive_client_wish(wish_id: int):
    try:
        return _wish(ClientWishService().archive(wish_id))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientWishNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client wish was not found.") from exc


@router.get("/clients/{client_id}/feedback", response_model=ClientFeedbackListResponse)
def list_client_feedback(client_id: int):
    try:
        return ClientFeedbackListResponse(feedback=[_feedback(f) for f in ClientFeedbackService().list_for_client(client_id)])
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client was not found.") from exc


@router.post("/clients/{client_id}/feedback", response_model=ClientFeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_client_feedback(client_id: int, payload: ClientFeedbackCreateRequest):
    try:
        draft = ClientFeedbackDraft.create(client_id=client_id, **payload.model_dump())
        return _feedback(ClientFeedbackService().create(draft))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except (ClientNotFoundError, ClientRecipeNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client or linked client recipe was not found.") from exc
    except (ClientWishFeedbackClientInactiveError, ClientRecipeClientMismatchError) as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/client-feedback/{feedback_id}", response_model=ClientFeedbackResponse)
def get_client_feedback(feedback_id: int):
    try:
        return _feedback(ClientFeedbackService().get(feedback_id))
    except DomainValidationError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientFeedbackNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Client feedback was not found.") from exc


def _wish(wish: ClientWish) -> ClientWishResponse:
    return ClientWishResponse(**wish.__dict__)


def _feedback(feedback: ClientFeedback) -> ClientFeedbackResponse:
    return ClientFeedbackResponse(**feedback.__dict__)
