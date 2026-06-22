from fastapi import APIRouter, HTTPException, status

from app.domain.clients import ClientDraft
from app.domain.errors import DomainValidationError
from app.models.client import Client
from app.repositories.clients import ClientNotFoundError
from app.schemas.clients import ClientCreateRequest, ClientResponse, ClientsResponse, ClientUpdateRequest
from app.services.clients import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreateRequest) -> ClientResponse:
    try:
        client = ClientService().create_client(_draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    return _client_response(client)


@router.get("", response_model=ClientsResponse)
def list_clients(include_inactive: bool = False) -> ClientsResponse:
    clients = ClientService().list_clients(include_inactive=include_inactive)
    return ClientsResponse(clients=[_client_response(client) for client in clients])


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int) -> ClientResponse:
    try:
        client = ClientService().get_client(client_id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client was not found.") from exc
    return _client_response(client)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, payload: ClientUpdateRequest) -> ClientResponse:
    try:
        client = ClientService().update_client(client_id, _draft_from_payload(payload))
    except DomainValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.issue.__dict__) from exc
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client was not found.") from exc
    return _client_response(client)


@router.post("/{client_id}/deactivate", response_model=ClientResponse)
def deactivate_client(client_id: int) -> ClientResponse:
    try:
        client = ClientService().deactivate_client(client_id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client was not found.") from exc
    return _client_response(client)


def _draft_from_payload(payload: ClientCreateRequest) -> ClientDraft:
    return ClientDraft.create(
        full_name=payload.full_name, phone=payload.phone, email=payload.email,
        address=payload.address, birthday=payload.birthday, skin_notes=payload.skin_notes,
        allergy_notes=payload.allergy_notes, preference_notes=payload.preference_notes,
        contraindication_notes=payload.contraindication_notes, notes=payload.notes,
    )


def _client_response(client: Client) -> ClientResponse:
    return ClientResponse(**client.__dict__)
