from dataclasses import dataclass


@dataclass(frozen=True)
class Client:
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
