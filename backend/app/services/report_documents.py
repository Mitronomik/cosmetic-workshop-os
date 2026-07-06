from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
from typing import Any

from app.db.config import DatabaseConfig, get_database_config
from app.db.paths import USER_DATA_DIR_ENV, resolve_user_data_paths
from app.schemas.report_documents import (
    ReportDocumentCreateResponse,
    ReportDocumentListResponse,
    ReportDocumentMetadata,
    ReportDocumentStatusResponse,
    ReportOverviewDocumentCreateRequest,
)
from app.schemas.reports import OverviewReportResponse, ReportWarning
from app.services.reports import ReportsService


class ReportDocumentError(RuntimeError):
    """Raised when a report document cannot be created safely."""


class UnsupportedReportDocumentFormatError(ReportDocumentError):
    """Raised when a requested document format is not supported yet."""


SUPPORTED_FORMAT = "markdown"
SUPPORTED_DOCUMENT_TYPE = "workshop_overview"
REPORT_DOCUMENT_SOURCE = "reports.overview"
REPORT_DOCUMENT_TITLE = "Сводка мастерской"
REPORT_DOCUMENTS_DIRNAME = "report-documents"


class ReportDocumentService:
    def __init__(self, config: DatabaseConfig | None = None, documents_dir: Path | None = None) -> None:
        self.config = config or get_database_config()
        self.documents_dir = documents_dir or resolve_report_documents_dir(self.config)
        self.reports_service = ReportsService(self.config)

    def status(self) -> ReportDocumentStatusResponse:
        return ReportDocumentStatusResponse(
            documents_dir=str(self.documents_dir),
            available_formats=[SUPPORTED_FORMAT],
            available_document_types=[SUPPORTED_DOCUMENT_TYPE],
            can_create=True,
            documents_count=len(_list_metadata_files(self.documents_dir)),
            message="Документы отчетов можно создавать вручную.",
        )

    def list_documents(self, limit: int = 50, offset: int = 0) -> ReportDocumentListResponse:
        normalized_limit = max(1, min(limit, 100))
        normalized_offset = max(0, offset)
        items = [_read_metadata(path) for path in _list_metadata_files(self.documents_dir)]
        items = [item for item in items if item is not None]
        items.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return ReportDocumentListResponse(
            items=items[normalized_offset : normalized_offset + normalized_limit],
            limit=normalized_limit,
            offset=normalized_offset,
            total=len(items),
        )

    def create_overview_document(self, request: ReportOverviewDocumentCreateRequest) -> ReportDocumentCreateResponse:
        if request.format != SUPPORTED_FORMAT:
            raise UnsupportedReportDocumentFormatError("Этот формат пока не поддерживается. Сейчас доступен только Markdown.")
        reason = sanitize_reason(request.reason)
        report = self.reports_service.get_overview()
        created_at = datetime.now(UTC)
        document_id = _document_id(created_at)
        markdown_filename = f"{document_id}.md"
        metadata_filename = f"{document_id}.json"
        markdown_text = _render_workshop_overview_markdown(report, created_at=created_at, reason=reason)

        self.documents_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = _unique_path(self.documents_dir / markdown_filename)
        if markdown_path.name != markdown_filename:
            document_id = markdown_path.stem
            metadata_filename = f"{document_id}.json"
        metadata_path = self.documents_dir / metadata_filename
        try:
            _write_text_exclusive(markdown_path, markdown_text)
            metadata = ReportDocumentMetadata(
                id=document_id,
                document_type=SUPPORTED_DOCUMENT_TYPE,
                format=SUPPORTED_FORMAT,
                filename=markdown_path.name,
                metadata_filename=metadata_path.name,
                created_at=created_at,
                source=REPORT_DOCUMENT_SOURCE,
                source_generated_at=_parse_datetime(report.generated_at),
                title=REPORT_DOCUMENT_TITLE,
                warnings_count=len(report.warnings),
                size_bytes=markdown_path.stat().st_size,
            )
            _write_text_exclusive(metadata_path, json.dumps(_metadata_json(metadata), ensure_ascii=False, indent=2) + "\n")
        except OSError as exc:
            raise ReportDocumentError("Не удалось создать документ отчета. Данные мастерской не изменялись.") from exc
        return ReportDocumentCreateResponse(document=metadata, message="Документ отчета создан.")


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


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    suffix = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{suffix}{path.suffix}")
        if not candidate.exists():
            return candidate
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


def _render_workshop_overview_markdown(report: OverviewReportResponse, *, created_at: datetime, reason: str | None = None) -> str:
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
        f"- Известная выручка: {_value(finance.known_revenue)}",
        f"- Известная себестоимость: {_value(finance.known_production_cost)}",
        f"- Известная маржа: {_value(finance.known_margin)}",
        f"- Маржа, %: {_value(finance.known_margin_percent)}",
        f"- Полных финансовых записей: {finance.complete_finance_record_count}",
        f"- Неполных записей для расчета маржи: {finance.incomplete_margin_count}",
        f"- Без цены продажи: {finance.missing_sale_price_count}",
        f"- Без себестоимости: {finance.missing_cost_count}",
        "- Налог не рассчитывается в этом документе и не придумывается системой.",
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
        "- PDF и DOCX пока не поддерживаются; сейчас доступен только Markdown.",
        "",
    ]
    return "\n".join(lines)
