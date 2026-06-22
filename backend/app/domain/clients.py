from dataclasses import dataclass
from datetime import date
import re

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_optional_string(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_full_name(full_name: str) -> str:
    normalized = normalize_optional_string(full_name)
    if not normalized:
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.REQUIRED_FIELD,
                message="Имя клиента обязательно.",
                field="full_name",
                value=str(full_name),
                next_action="Введите имя клиента, например “Анна Иванова”.",
            )
        )
    return normalized


def normalize_phone(phone: str | None) -> str:
    return normalize_optional_string(phone)


def normalize_email(email: str | None) -> str:
    normalized = normalize_optional_string(email).lower()
    if normalized and not _EMAIL_RE.match(normalized):
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_EMAIL,
                message="Email клиента должен быть похож на адрес электронной почты.",
                field="email",
                value=normalized,
                next_action="Исправьте email, например anna@example.com, или оставьте поле пустым.",
            )
        )
    return normalized


def parse_birthday(value: date | str | None) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        birthday = value
    else:
        try:
            birthday = date.fromisoformat(str(value))
        except ValueError as exc:
            raise DomainValidationError(
                DomainIssue(
                    code=DomainIssueCode.INVALID_DATE,
                    message="Дата рождения должна быть настоящей датой в формате ГГГГ-ММ-ДД.",
                    field="birthday",
                    value=str(value),
                    next_action="Укажите дату вроде 1990-05-20 или оставьте поле пустым.",
                )
            ) from exc
    if birthday > date.today():
        raise DomainValidationError(
            DomainIssue(
                code=DomainIssueCode.INVALID_DATE,
                message="Дата рождения клиента не может быть в будущем.",
                field="birthday",
                value=birthday.isoformat(),
                next_action="Проверьте дату рождения или оставьте поле пустым.",
            )
        )
    return birthday


@dataclass(frozen=True)
class ClientDraft:
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

    @classmethod
    def create(cls, *, full_name: str, phone: str | None = "", email: str | None = "", address: str | None = "", birthday: date | str | None = None, skin_notes: str | None = "", allergy_notes: str | None = "", preference_notes: str | None = "", contraindication_notes: str | None = "", notes: str | None = "") -> "ClientDraft":
        return cls(
            full_name=normalize_full_name(full_name),
            phone=normalize_phone(phone),
            email=normalize_email(email),
            address=normalize_optional_string(address),
            birthday=parse_birthday(birthday),
            skin_notes=normalize_optional_string(skin_notes),
            allergy_notes=normalize_optional_string(allergy_notes),
            preference_notes=normalize_optional_string(preference_notes),
            contraindication_notes=normalize_optional_string(contraindication_notes),
            notes=normalize_optional_string(notes),
        )
