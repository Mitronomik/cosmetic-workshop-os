from dataclasses import dataclass
import hashlib
import re

from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
from app.models.catalog import CatalogScope

_SLUG_RE = re.compile(r"^[a-z0-9_-]+$")
_LATIN_RE = re.compile(r"[^a-z0-9_-]+")
_WS_RE = re.compile(r"\s+")


def parse_scope(value: str) -> CatalogScope:
    try:
        return CatalogScope(value)
    except ValueError as exc:
        raise DomainValidationError(
            DomainIssue(
                DomainIssueCode.INVALID_CATEGORY,
                "Неизвестная область каталога.",
                "scope",
                value,
                "Выберите ingredient, packaging или recipe.",
            )
        ) from exc


def normalize_name(name: str, field: str = "name") -> str:
    normalized = _WS_RE.sub(" ", (name or "").strip())
    if not normalized:
        raise DomainValidationError(
            DomainIssue(
                DomainIssueCode.REQUIRED_FIELD,
                "Название не может быть пустым.",
                field,
                name,
                "Укажите понятное название.",
            )
        )
    return normalized


def normalize_slug(slug: str | None, name: str, prefix: str) -> str:
    if slug is not None and slug.strip():
        value = slug.strip().lower()
        if not _SLUG_RE.match(value):
            raise DomainValidationError(
                DomainIssue(
                    DomainIssueCode.INVALID_CATEGORY,
                    "Слаг может содержать только латинские строчные буквы, цифры, _ и -.",
                    "slug",
                    slug,
                    "Исправьте слаг, например active-oils.",
                )
            )
        return value
    base = name.strip().lower()
    base = _LATIN_RE.sub("-", base).strip("-")
    if base and _SLUG_RE.match(base):
        return base
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


@dataclass(frozen=True)
class CatalogCategoryDraft:
    scope: CatalogScope
    name: str
    slug: str
    parent_id: int | None = None
    sort_order: int = 0

    @classmethod
    def create(
        cls,
        *,
        scope: str,
        name: str,
        slug: str | None = None,
        parent_id: int | None = None,
        sort_order: int = 0,
    ):
        clean_name = normalize_name(name)
        return cls(
            parse_scope(scope),
            clean_name,
            normalize_slug(slug, clean_name, "category"),
            parent_id,
            int(sort_order),
        )


@dataclass(frozen=True)
class CatalogTagDraft:
    scope: CatalogScope
    name: str
    slug: str
    color: str = ""

    @classmethod
    def create(cls, *, scope: str, name: str, slug: str | None = None, color: str = ""):
        clean_name = normalize_name(name)
        return cls(
            parse_scope(scope),
            clean_name,
            normalize_slug(slug, clean_name, "tag"),
            (color or "").strip(),
        )
