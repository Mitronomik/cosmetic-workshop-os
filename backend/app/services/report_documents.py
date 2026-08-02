from collections.abc import Callable
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Literal
import struct

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths
from app.schemas.report_documents import (
    ReportDocumentCreateResponse,
    ReportDocumentListResponse,
    ReportDocumentMetadata,
    ReportDocumentStatusResponse,
    ReportOverviewDocumentCreateRequest,
)
from app.schemas.reports import FinanceReportResponse, OverviewReportResponse, ReportWarning
from app.schemas.settings import WorkshopProfile
from app.services.report_document_audit import (
    PENDING_AUDIT_MESSAGE,
    ReportDocumentArtifactUnverifiedError,
    ReportDocumentAuditService,
    ReportDocumentAuditTrackingUnavailableError,
)
from app.services.reports import ReportsService
from app.services.settings import WorkshopProfileSettingsService


class ReportDocumentError(RuntimeError):
    """Raised when a report document cannot be created safely."""


class UnsupportedReportDocumentFormatError(ReportDocumentError):
    """Raised when a requested document format is not supported yet."""


class ReportDocumentNotFoundError(ReportDocumentError):
    """Raised when requested report document metadata is unknown."""


class ReportDocumentFileMissingError(ReportDocumentError):
    """Raised when known report document file is missing from disk."""


class ReportDocumentUnsafePathError(ReportDocumentError):
    """Raised when metadata points outside the safe report documents directory."""


class UnsupportedReportDocumentDispositionError(ReportDocumentError):
    """Raised when requested file disposition is not supported."""


class ReportDocumentStatusUnavailableError(ReportDocumentError):
    """Raised when report-document status cannot be reported truthfully.

    Specifically: the pending-Journal count could not be read. Reporting the
    status without it would mean publishing `pending_audit_count: 0`, which the
    frontend treats as proof that nothing is awaiting a Journal entry and uses to
    clear a standing warning. Failing loudly is the honest option.
    """


SUPPORTED_FORMAT = "markdown"
PDF_FORMAT = "pdf"
SUPPORTED_DOCUMENT_TYPE = "workshop_overview"
REPORT_DOCUMENT_SOURCE = "reports.overview"
REPORT_DOCUMENT_TITLE = "Сводка мастерской"
REPORT_DOCUMENTS_DIRNAME = "report-documents"
CYRILLIC_FONT_SAMPLE = "Сводка мастерской Привет Яя"


class ReportDocumentService:
    def __init__(self, config: DatabaseConfig | None = None, documents_dir: Path | None = None) -> None:
        self.config = config or get_database_config()
        self.documents_dir = documents_dir or resolve_report_documents_dir(self.config)
        self.reports_service = ReportsService(self.config)
        self.workshop_profile_service = WorkshopProfileSettingsService(self.config)
        self.audit_service = ReportDocumentAuditService(self.documents_dir, self.config)

    def status(self) -> ReportDocumentStatusResponse:
        """Read-only status, including the pending-Journal count.

        Deliberately does not reconcile. Opening the workspace is a read, and a
        read must never insert an AuditLog row or move ledger state — otherwise
        simply looking at the page would change history.

        If the ledger cannot be read, this raises rather than reporting a count
        it does not actually know. The raised error carries fixed Russian text
        only: the underlying SQLite message never reaches the user.

        The caught tuple is deliberately narrow. `sqlite3.Error` and `OSError`
        are the failures the persistence boundary genuinely produces — opening
        the database goes through `ensure_database_parent`, whose `mkdir` raises
        `OSError`, and through `sqlite3.connect` plus the count query, which
        raise `sqlite3.Error`. Catching `Exception` here would additionally
        swallow `TypeError`, `AttributeError` and friends, dressing a programming
        defect up as the known "ledger temporarily unavailable" condition and
        hiding a real bug behind a reassuring Russian sentence.
        """
        try:
            pending_audit_count = self.audit_service.pending_count()
        except (sqlite3.Error, OSError) as failure:
            raise ReportDocumentStatusUnavailableError(
                "Не удалось прочитать сведения о документах отчетов. Данные мастерской не изменялись."
            ) from failure
        return ReportDocumentStatusResponse(
            documents_dir=str(self.documents_dir),
            available_formats=_available_formats(),
            available_document_types=[SUPPORTED_DOCUMENT_TYPE],
            can_create=True,
            documents_count=len(_list_metadata_files(self.documents_dir)),
            message="Документы отчетов можно создавать вручную.",
            pending_audit_count=pending_audit_count,
        )

    def list_documents(self, limit: int = 50, offset: int = 0) -> ReportDocumentListResponse:
        normalized_limit = max(1, min(limit, 100))
        normalized_offset = max(0, offset)
        items = _all_metadata(self.documents_dir)
        return ReportDocumentListResponse(
            items=items[normalized_offset : normalized_offset + normalized_limit],
            limit=normalized_limit,
            offset=normalized_offset,
            total=len(items),
        )

    def get_document_file(
        self, document_id: str, disposition: str = "attachment"
    ) -> tuple[ReportDocumentMetadata, Path, str, str]:
        normalized_disposition = disposition.strip().lower()
        if normalized_disposition not in {"attachment", "inline"}:
            raise UnsupportedReportDocumentDispositionError("Неподдерживаемый режим открытия документа.")

        metadata = next((item for item in _all_metadata(self.documents_dir) if item.id == document_id), None)
        if metadata is None:
            raise ReportDocumentNotFoundError("Документ отчета не найден.")

        document_path = _safe_document_path(self.documents_dir, metadata)
        if not document_path.exists() or not document_path.is_file():
            raise ReportDocumentFileMissingError("Файл документа отчета не найден. Данные мастерской не изменялись.")

        media_type = _media_type_for_format(metadata.format)
        effective_disposition = "inline" if normalized_disposition == "inline" and metadata.format == PDF_FORMAT else "attachment"
        return metadata, document_path, media_type, effective_disposition

    def create_overview_document(self, request: ReportOverviewDocumentCreateRequest) -> ReportDocumentCreateResponse:
        if request.format == "docx":
            raise UnsupportedReportDocumentFormatError("DOCX пока не поддерживается.")
        if request.format == PDF_FORMAT and not _is_pdf_generation_available():
            raise UnsupportedReportDocumentFormatError("PDF сейчас недоступен: не найден безопасный локальный способ сформировать PDF с русским текстом.")
        if request.format not in _available_formats():
            raise UnsupportedReportDocumentFormatError("Этот формат пока не поддерживается. Сейчас доступны: Markdown и PDF.")
        # One bounded pre-create reconciliation pass, after request validation and
        # before anything is reserved. An older unresolved operation is given its
        # chance here; it never blocks this document by itself.
        self.audit_service.reconcile()

        reason = sanitize_reason(request.reason)
        report = self.reports_service.get_overview()
        workshop_profile = self.workshop_profile_service.get_profile().profile
        created_at = datetime.now(UTC)
        base_document_id = _document_id(created_at)
        profile_rendering_mode: ProfileRenderingMode = "plain" if request.format == PDF_FORMAT else "markdown"
        content_lines = _workshop_overview_document_lines(
            report,
            created_at=created_at,
            reason=reason,
            workshop_profile=workshop_profile,
            profile_rendering_mode=profile_rendering_mode,
        )

        self.documents_dir.mkdir(parents=True, exist_ok=True)
        document_id, document_path, metadata_path = _unique_document_paths(
            self.documents_dir,
            base_document_id,
            request.format,
            is_identity_active=self._is_identity_active,
        )
        # The prepared ledger row must be committed before either file is
        # written. If it cannot be, no document is created at all — that is the
        # one case where the create is refused outright, and refusing it is
        # honest: an artifact we could not have tracked would be an artifact we
        # could never audit.
        operation_id = self.audit_service.prepare_operation(
            primary_filename=document_path.name, companion_filename=metadata_path.name
        )
        document_created = False
        metadata_created = False
        try:
            if request.format == SUPPORTED_FORMAT:
                _write_text_exclusive(document_path, _render_markdown_from_lines(content_lines))
            elif request.format == PDF_FORMAT:
                _write_pdf_exclusive(document_path, content_lines, created_at=created_at)
            document_created = True
            metadata = ReportDocumentMetadata(
                id=document_id,
                document_type=SUPPORTED_DOCUMENT_TYPE,
                format=request.format,
                filename=document_path.name,
                metadata_filename=metadata_path.name,
                created_at=created_at,
                source=REPORT_DOCUMENT_SOURCE,
                source_generated_at=_parse_datetime(report.generated_at),
                title=REPORT_DOCUMENT_TITLE,
                warnings_count=len(report.warnings),
                size_bytes=document_path.stat().st_size,
            )
            _write_text_exclusive(metadata_path, json.dumps(_metadata_json(metadata), ensure_ascii=False, indent=2) + "\n")
            metadata_created = True
        except OSError as exc:
            if metadata_created:
                try:
                    metadata_path.unlink()
                except OSError:
                    pass
            if document_created:
                try:
                    document_path.unlink()
                except OSError:
                    pass
            # The pair never completed, so this operation can be resolved now.
            # Best-effort by contract: if the transition itself fails, the
            # original creation error still reaches the user unchanged and the
            # operation is left for a later reconciliation pass to resolve.
            self.audit_service.abandon_operation(operation_id)
            message = "Не удалось создать PDF-документ отчета. Данные мастерской не изменялись." if request.format == PDF_FORMAT else "Не удалось создать документ отчета. Данные мастерской не изменялись."
            raise ReportDocumentError(message) from exc

        # Verification decides whether there is an authoritative result at all,
        # and the Journal entry is a separate, secondary question. Collapsing the
        # two is how an unverified pair would be reported as a created document
        # with a merely pending Journal entry.
        finalization = self.audit_service.finalize(operation_id, reconciled_after_failure=False)
        if not finalization.artifact_is_authoritative:
            # Both files are on disk, but this operation could not prove they are
            # the document it just wrote. They are left exactly where they are —
            # deleting a pair whose ownership is precisely what failed to verify
            # could destroy someone else's files — and the ledger row stays
            # unresolved and counted.
            raise ReportDocumentArtifactUnverifiedError(ReportDocumentArtifactUnverifiedError.message)

        # From here the pair is verified and is the authoritative result. No
        # audit outcome below deletes it or turns this into a failure.
        if not finalization.is_recorded:
            return ReportDocumentCreateResponse(
                document=metadata,
                message="Документ отчета создан.",
                audit_status="pending",
                audit_message=PENDING_AUDIT_MESSAGE,
            )
        return ReportDocumentCreateResponse(
            document=metadata, message="Документ отчета создан.", audit_status="recorded", audit_message=None
        )

    def _is_identity_active(self, primary_filename: str, companion_filename: str) -> bool:
        """Treat an active ledger identity as a filename collision.

        A `prepared` operation owns its names before its files exist, so file
        existence alone is not enough to tell whether a candidate identity is
        free. Failing to read the ledger here is a preparation failure, not a
        silent "no collision": guessing would let two operations claim one
        artifact identity.

        Only the expected persistence failures are translated. This runs before
        either file is written, so letting an unexpected defect propagate is
        safe — the create still fails with nothing on disk — and it keeps a
        `TypeError` from being reported to the user as the specific, recoverable
        "tracking unavailable" condition.
        """
        try:
            return self.audit_service.is_identity_active(primary_filename, companion_filename)
        except (sqlite3.Error, OSError) as failure:
            raise ReportDocumentAuditTrackingUnavailableError(
                "Не удалось безопасно подготовить создание документа. Документ не создан."
            ) from failure


def resolve_report_documents_dir(config: DatabaseConfig | None = None) -> Path:
    database_path = (config or get_database_config()).path
    user_paths = resolve_user_data_paths()
    if database_path == user_paths.database_path or os.environ.get(USER_DATA_DIR_ENV):
        return user_paths.exports_dir / REPORT_DOCUMENTS_DIRNAME
    return database_path.parent / "exports" / REPORT_DOCUMENTS_DIRNAME


def sanitize_reason(reason: str | None) -> str | None:
    if reason is None:
        return None
    cleaned = "".join(character if character.isalnum() or character in {"-", "_", " ", "."} else "_" for character in reason.strip())
    cleaned = re.sub(r"[.]{2,}", ".", cleaned).strip(" ._-/\\")
    return cleaned[:80] or None


def _document_id(created_at: datetime) -> str:
    return f"workshop-overview-{created_at.strftime('%Y%m%d-%H%M%S')}"


def _unique_document_paths(
    documents_dir: Path,
    document_id: str,
    format: str = SUPPORTED_FORMAT,
    *,
    is_identity_active: "Callable[[str, str], bool] | None" = None,
) -> tuple[str, Path, Path]:
    """The existing deterministic numeric-suffix identity search, plus the ledger.

    CR-009 adds one condition to the same loop rather than a new policy: an
    identity is free only when neither file exists *and* no active operation
    already owns those names. The suffix advances exactly as before, so
    generated filenames stay byte-compatible with every document created so far.
    """
    suffix = 0
    extension = ".pdf" if format == PDF_FORMAT else ".md"
    while True:
        candidate_id = document_id if suffix == 0 else f"{document_id}-{suffix}"
        document_path = documents_dir / f"{candidate_id}{extension}"
        metadata_path = documents_dir / f"{candidate_id}.json"
        free_on_disk = not document_path.exists() and not metadata_path.exists()
        if free_on_disk and not (is_identity_active and is_identity_active(document_path.name, metadata_path.name)):
            return candidate_id, document_path, metadata_path
        suffix += 1


def _write_text_exclusive(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8") as file:
        file.write(text)


def _list_metadata_files(documents_dir: Path) -> list[Path]:
    if not documents_dir.exists() or not documents_dir.is_dir():
        return []
    return sorted((p for p in documents_dir.iterdir() if p.is_file() and p.suffix.lower() == ".json"), reverse=True)


def _read_metadata(path: Path) -> ReportDocumentMetadata | None:
    try:
        return ReportDocumentMetadata.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return None


def _all_metadata(documents_dir: Path) -> list[ReportDocumentMetadata]:
    items = [_read_metadata(path) for path in _list_metadata_files(documents_dir)]
    items = [item for item in items if item is not None]
    items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
    return items


def _safe_document_path(documents_dir: Path, metadata: ReportDocumentMetadata) -> Path:
    if Path(metadata.filename).name != metadata.filename:
        raise ReportDocumentUnsafePathError("Документ отчета не может быть открыт из-за ошибки безопасности пути.")
    expected_suffix = ".pdf" if metadata.format == PDF_FORMAT else ".md" if metadata.format == SUPPORTED_FORMAT else ""
    if not expected_suffix or not metadata.filename.endswith(expected_suffix):
        raise ReportDocumentUnsafePathError("Документ отчета не может быть открыт из-за ошибки безопасности пути.")
    expected_name = f"{metadata.id}{expected_suffix}"
    if metadata.filename != expected_name:
        raise ReportDocumentUnsafePathError("Документ отчета не может быть открыт из-за ошибки безопасности пути.")
    try:
        root = documents_dir.resolve()
        candidate = (documents_dir / metadata.filename).resolve(strict=False)
        candidate.relative_to(root)
    except (OSError, ValueError):
        raise ReportDocumentUnsafePathError("Документ отчета не может быть открыт из-за ошибки безопасности пути.") from None
    return candidate


def _media_type_for_format(format: str) -> str:
    if format == PDF_FORMAT:
        return "application/pdf"
    if format == SUPPORTED_FORMAT:
        return "text/markdown; charset=utf-8"
    return "application/octet-stream"

def _metadata_json(metadata: ReportDocumentMetadata) -> dict[str, Any]:
    data = metadata.model_dump(mode="json")
    data["created_at"] = metadata.created_at.isoformat().replace("+00:00", "Z")
    if metadata.source_generated_at is not None:
        data["source_generated_at"] = metadata.source_generated_at.isoformat().replace("+00:00", "Z")
    return data


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _value(value: str | int | None) -> str:
    return "не рассчитано" if value is None else str(value)


def _warnings_lines(warnings: list[ReportWarning]) -> list[str]:
    if not warnings:
        return ["- Явных предупреждений нет."]
    return [f"- {warning.message}" + (f" (`{warning.code}`)" if warning.code else "") for warning in warnings]


ProfileRenderingMode = Literal["markdown", "plain"]


def _workshop_overview_document_lines(
    report: OverviewReportResponse,
    *,
    created_at: datetime,
    reason: str | None = None,
    workshop_profile: WorkshopProfile | None = None,
    profile_rendering_mode: ProfileRenderingMode = "markdown",
) -> list[str]:
    inventory = report.inventory_summary
    orders = report.orders_summary
    production = report.production_summary
    finance = report.finance_summary
    produced_totals = ", ".join(f"{item.quantity} {item.unit}" for item in production.produced_quantity_totals) or "нет данных"
    lines = [
        "# Сводка мастерской",
        "",
        "## Когда сформировано",
        f"- Документ создан: {created_at.isoformat().replace('+00:00', 'Z')}",
        f"- Исходный отчет сформирован backend ReportsService: {report.generated_at}",
    ]
    if reason:
        lines.append(f"- Причина создания: {reason}")
    profile_lines = _workshop_profile_lines(workshop_profile, rendering_mode=profile_rendering_mode)
    if profile_lines:
        lines += ["", "## Профиль мастерской", *profile_lines]
    lines += [
        "",
        "## Краткая сводка",
        f"- Активных компонентов: {inventory.total_active_ingredients}",
        f"- Активных заказов: {orders.active_orders}",
        f"- Производственных партий: {production.total_production_batches}",
        f"- Открытых алертов: {report.alerts_summary.open_alerts}",
        f"- Открытых закупочных предложений: {report.purchase_summary.open_purchase_suggestions}",
        "",
        "## Склад",
        f"- Активные компоненты: {inventory.total_active_ingredients}",
        f"- Активные партии компонентов: {inventory.total_active_ingredient_lots}",
        f"- Партии с положительным остатком: {inventory.ingredient_lots_with_positive_balance}",
        f"- Просроченные партии: {inventory.expired_ingredient_lots}",
        f"- Партии с близким сроком годности: {inventory.expiring_soon_ingredient_lots}",
        f"- Активная тара: {inventory.active_packaging_items}",
        f"- Позиции тары с положительным остатком: {inventory.packaging_items_with_positive_balance}",
        "",
        "## Заказы",
        f"- Всего заказов: {orders.total_orders}",
        f"- Новые: {orders.new_orders}",
        f"- Ожидают материалы: {orders.waiting_for_materials}",
        f"- Готовы к производству: {orders.ready_to_produce}",
        f"- В работе: {orders.in_progress}",
        f"- Произведены: {orders.produced}",
        f"- Доставлены: {orders.delivered}",
        f"- Отменены: {orders.cancelled}",
        f"- Архивные: {orders.archived}",
        f"- Без выбранной рецептуры: {orders.orders_missing_recipe}",
        "",
        "## Производство",
        f"- Всего партий: {production.total_production_batches}",
        f"- Заказы с производством: {production.produced_orders_count}",
        f"- Последнее производство: {_value(production.last_production_date)}",
        f"- Объемы производства: {produced_totals}",
        f"- Известная себестоимость партий: {_value(production.total_known_cost)}",
        f"- Партий без себестоимости: {production.missing_cost_count}",
        "",
        "## Алерты и закупки",
        f"- Открытые алерты: {report.alerts_summary.open_alerts}",
        f"- Критичные или блокирующие алерты: {report.alerts_summary.critical_or_blocking_alerts}",
        f"- Открытые закупочные предложения: {report.purchase_summary.open_purchase_suggestions}",
        f"- Алерты низкого остатка: {inventory.open_low_stock_alerts}",
        "",
        "## Базовые финансы",
        *_finance_lines(finance),
        "",
        "## Предупреждения и неполные данные",
        *_warnings_lines(report.warnings),
        "- Если значение показано как «не рассчитано» или «нет данных», исходные данные неполные.",
        "",
        "## Важные ограничения",
        "- Это операционная сводка мастерской, а не бухгалтерский или налоговый отчет.",
        "- Система не придумывает налоговые ставки и не пересчитывает налог в документе.",
        "- Если не хватает цены продажи или себестоимости, маржа может быть недоступна.",
        "- Документ только читает данные и не меняет склад, заказы, производство или закупки.",
        "- Markdown и PDF создаются вручную; DOCX пока не поддерживается.",
        "",
    ]
    return lines


def _finance_lines(finance: FinanceReportResponse) -> list[str]:
    """The finance section of «Сводка мастерской».

    Every number here is displayed exactly as the backend finance report DTO
    returned it. The document calculates nothing: it does not recalculate tax,
    does not derive margin, and never prints the *current* tax setting as a
    stand-in for what a historical batch actually recorded.

    Tax and margin cover only the batches that saved those values when they were
    produced, so the two coverage lines state which subset each total is about —
    they can legitimately differ from each other and from the paired-input
    counters below them.
    """
    return [
        f"- Известная выручка: {_value(finance.known_revenue)}",
        f"- Известная себестоимость: {_value(finance.known_production_cost)}",
        f"- Зафиксированный налог: {_value(finance.known_tax)}",
        f"- Зафиксированная маржа: {_value(finance.known_margin)}",
        f"- Маржа по партиям с зафиксированными финансовыми данными, %: {_value(finance.known_margin_percent)}",
        f"- Налог зафиксирован: {finance.tax_snapshot_record_count} из {finance.produced_order_count} партий",
        f"- Маржа зафиксирована: {finance.margin_snapshot_record_count} из {finance.produced_order_count} партий",
        "",
        "### Полнота исходных данных",
        f"- Партий с ценой и себестоимостью: {finance.complete_finance_record_count}",
        f"- Партий с неполной парой цены и себестоимости: {finance.incomplete_margin_count}",
        f"- Без цены продажи: {finance.missing_sale_price_count}",
        f"- Без себестоимости: {finance.missing_cost_count}",
        "",
        "### Как читать эти цифры",
        "- Документ показывает налог и маржу, сохранённые при изготовлении партий.",
        "- Налог и маржа не пересчитываются по текущей налоговой ставке.",
        "- Текущая настройка ставки не применяется к прошлым партиям задним числом.",
        "- У старых партий с неполными данными налог и маржа могут быть недоступны.",
        "- Итоги могут охватывать разные наборы партий, поэтому их количество указано отдельно.",
    ]

def _plain_document_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _markdown_safe_text(value: str) -> str:
    text = _plain_document_text(value)
    replacements = {"\\": "\\\\", "`": "\\`", "*": "\\*", "_": "\\_", "{": "\\{", "}": "\\}", "[": "\\[", "]": "\\]", "(": "\\(", ")": "\\)", "#": "\\#", "+": "\\+", "-": "\\-", ".": "\\.", "!": "\\!", "|": "\\|", ">": "\\>", "<": "&lt;"}
    return "".join(replacements.get(character, character) for character in text)


def _workshop_profile_lines(profile: WorkshopProfile | None, *, rendering_mode: ProfileRenderingMode) -> list[str]:
    if profile is None:
        return []
    formatter = _markdown_safe_text if rendering_mode == "markdown" else _plain_document_text
    fields = [
        ("Мастерская", profile.workshop_name),
        ("Мастер", profile.master_name),
        ("Контакты", profile.workshop_contact_text),
        ("Примечание", profile.workshop_note),
    ]
    lines = [f"- {label}: {formatter(value)}" for label, value in fields if value and value.strip()]
    return lines


def _available_formats() -> list[str]:
    formats = [SUPPORTED_FORMAT]
    if _is_pdf_generation_available():
        formats.append(PDF_FORMAT)
    return formats


def _is_pdf_generation_available() -> bool:
    return _find_cyrillic_font_path() is not None


def _find_cyrillic_font_path() -> Path | None:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for path in candidates:
        if _font_supports_cyrillic_for_pdf_renderer(path):
            return path
    for root in (Path("/usr/share/fonts"), Path("/System/Library/Fonts"), Path("/Library/Fonts")):
        if root.exists():
            for path in root.rglob("*.ttf"):
                if any(name in path.name.lower() for name in ("dejavusans", "notosans", "liberationsans")) and _font_supports_cyrillic_for_pdf_renderer(path):
                    return path
    return None


def _font_supports_cyrillic_for_pdf_renderer(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    if path.suffix.lower() != ".ttf":
        return False
    try:
        font_data = path.read_bytes()
    except OSError:
        return False
    cmap = _read_ttf_cmap_format4(font_data)
    if not cmap:
        return False
    for character in CYRILLIC_FONT_SAMPLE:
        if character.isspace():
            continue
        if cmap.get(ord(character), 0) == 0:
            return False
    return True


def _render_markdown_from_lines(lines: list[str]) -> str:
    return "\n".join(lines)


def _write_pdf_exclusive(path: Path, lines: list[str], *, created_at: datetime) -> None:
    font_path = _find_cyrillic_font_path()
    if font_path is None:
        raise OSError("PDF generation unavailable: no Cyrillic-capable local font found")
    pdf_bytes = _build_simple_unicode_pdf(lines, font_path=font_path, created_at=created_at)
    with path.open("xb") as file:
        file.write(pdf_bytes)


def _build_simple_unicode_pdf(lines: list[str], *, font_path: Path, created_at: datetime) -> bytes:
    page_width = 595
    page_height = 842
    margin = 48
    line_height = 15
    font_data = font_path.read_bytes()
    wrapped: list[tuple[str, int]] = []
    for raw in lines:
        level = 0
        text = raw
        if raw.startswith("# "):
            level, text = 1, raw[2:]
        elif raw.startswith("## "):
            level, text = 2, raw[3:]
        elif raw.startswith("- "):
            text = "• " + raw[2:]
        if not text:
            wrapped.append(("", 0)); continue
        width = 54 if level == 0 else 38 if level == 1 else 46
        while len(text) > width:
            cut = text.rfind(" ", 0, width) or width
            wrapped.append((text[:cut], level)); text = text[cut:].strip()
        wrapped.append((text, level))
    pages = []
    current: list[tuple[str, int]] = []
    y = page_height - margin
    for item in wrapped:
        if y < margin + line_height:
            pages.append(current); current = []; y = page_height - margin
        current.append(item); y -= line_height + (7 if item[1] == 1 else 4 if item[1] == 2 else 0)
    if current:
        pages.append(current)

    objects: list[bytes] = []
    def add(obj: bytes) -> int:
        objects.append(obj); return len(objects)
    used_codes = {ord(character) for text, _level in wrapped for character in text}
    used_codes.update(ord(character) for character in f"Сформировано: {created_at.isoformat().replace('+00:00', 'Z')}")
    cid_to_gid = _build_cid_to_gid_map(font_data, used_codes)
    font_file_obj = add(b"<< /Length %d /Length1 %d >>\nstream\n" % (len(font_data), len(font_data)) + font_data + b"\nendstream")
    cid_map_obj = add(b"<< /Length %d >>\nstream\n" % len(cid_to_gid) + cid_to_gid + b"\nendstream")
    descriptor_obj = add(f"<< /Type /FontDescriptor /FontName /DejaVuSans /Flags 4 /Ascent 928 /Descent -236 /CapHeight 700 /ItalicAngle 0 /StemV 80 /FontBBox [-1021 -463 1793 1232] /FontFile2 {font_file_obj} 0 R >>".encode())
    cidfont_obj = add(f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /DejaVuSans /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor {descriptor_obj} 0 R /CIDToGIDMap {cid_map_obj} 0 R >>".encode())
    font_obj = add(f"<< /Type /Font /Subtype /Type0 /BaseFont /DejaVuSans /Encoding /Identity-H /DescendantFonts [{cidfont_obj} 0 R] >>".encode())
    page_objs: list[int] = []
    content_objs: list[int] = []
    for page in pages:
        stream_parts = ["BT"]
        y = page_height - margin
        for text, level in page:
            size = 18 if level == 1 else 14 if level == 2 else 10
            if text:
                hex_text = text.encode("utf-16-be").hex().upper()
                stream_parts.append(f"/F1 {size} Tf 1 0 0 1 {margin} {y} Tm <{hex_text}> Tj")
            y -= line_height + (7 if level == 1 else 4 if level == 2 else 0)
        footer = f"Сформировано: {created_at.isoformat().replace('+00:00', 'Z')}"
        stream_parts.append(f"/F1 8 Tf 1 0 0 1 {margin} 24 Tm <{footer.encode('utf-16-be').hex().upper()}> Tj")
        stream_parts.append("ET")
        stream = "\n".join(stream_parts).encode("ascii")
        content_objs.append(add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"))
        page_objs.append(add(b""))
    pages_obj = len(objects) + 1
    for i, page_obj in enumerate(page_objs):
        objects[page_obj - 1] = f"<< /Type /Page /Parent {pages_obj} 0 R /MediaBox [0 0 {page_width} {page_height}] /Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_objs[i]} 0 R >>".encode()
    kids = " ".join(f"{obj} 0 R" for obj in page_objs)
    add(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_objs)} >>".encode())
    catalog_obj = add(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>".encode())
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(out)); out.extend(f"{index} 0 obj\n".encode()); out.extend(obj); out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {len(objects)+1} /Root {catalog_obj} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(out)



def _build_cid_to_gid_map(font_data: bytes, used_codes: set[int]) -> bytes:
    cmap = _read_ttf_cmap_format4(font_data)
    max_code = max(used_codes or {255})
    mapping = bytearray((max_code + 1) * 2)
    for code in used_codes:
        gid = cmap.get(code, 0)
        if code < 256 and gid == 0:
            gid = code
        struct.pack_into(">H", mapping, code * 2, gid)
    return bytes(mapping)


def _read_ttf_cmap_format4(font_data: bytes) -> dict[int, int]:
    try:
        num_tables = struct.unpack_from(">H", font_data, 4)[0]
        cmap_offset = None
        for index in range(num_tables):
            record_offset = 12 + index * 16
            tag, _checksum, offset, _length = struct.unpack_from(">4sIII", font_data, record_offset)
            if tag == b"cmap":
                cmap_offset = offset
                break
        if cmap_offset is None:
            return {}
        num_subtables = struct.unpack_from(">H", font_data, cmap_offset + 2)[0]
        subtable_offset = None
        for index in range(num_subtables):
            platform_id, encoding_id, offset = struct.unpack_from(">HHI", font_data, cmap_offset + 4 + index * 8)
            fmt = struct.unpack_from(">H", font_data, cmap_offset + offset)[0]
            if fmt == 4 and (platform_id, encoding_id) in {(3, 1), (3, 10), (0, 3), (0, 4)}:
                subtable_offset = cmap_offset + offset
                break
        if subtable_offset is None:
            return {}
        seg_count = struct.unpack_from(">H", font_data, subtable_offset + 6)[0] // 2
        end_codes_offset = subtable_offset + 14
        start_codes_offset = end_codes_offset + seg_count * 2 + 2
        deltas_offset = start_codes_offset + seg_count * 2
        range_offsets_offset = deltas_offset + seg_count * 2
        cmap: dict[int, int] = {}
        for i in range(seg_count):
            end_code = struct.unpack_from(">H", font_data, end_codes_offset + i * 2)[0]
            start_code = struct.unpack_from(">H", font_data, start_codes_offset + i * 2)[0]
            delta = struct.unpack_from(">h", font_data, deltas_offset + i * 2)[0]
            range_offset = struct.unpack_from(">H", font_data, range_offsets_offset + i * 2)[0]
            if start_code == 0xFFFF and end_code == 0xFFFF:
                continue
            for code in range(start_code, end_code + 1):
                if range_offset == 0:
                    gid = (code + delta) & 0xFFFF
                else:
                    glyph_offset = range_offsets_offset + i * 2 + range_offset + (code - start_code) * 2
                    glyph_index = struct.unpack_from(">H", font_data, glyph_offset)[0]
                    gid = 0 if glyph_index == 0 else (glyph_index + delta) & 0xFFFF
                cmap[code] = gid
        return cmap
    except (struct.error, IndexError, ValueError):
        return {}
