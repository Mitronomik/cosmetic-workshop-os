from datetime import date

from pydantic import BaseModel


class ClientCreateRequest(BaseModel):
    full_name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    birthday: date | None = None
    skin_notes: str = ""
    allergy_notes: str = ""
    preference_notes: str = ""
    contraindication_notes: str = ""
    notes: str = ""


class ClientUpdateRequest(ClientCreateRequest):
    pass


class ClientResponse(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str
    address: str
    birthday: str | None
    skin_notes: str
    allergy_notes: str
    preference_notes: str
    contraindication_notes: str
    notes: str
    is_active: bool
    created_at: str
    updated_at: str


class ClientsResponse(BaseModel):
    clients: list[ClientResponse]
