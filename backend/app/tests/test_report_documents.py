import json
from pathlib import Path
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.services.database import initialize_database
from app.services import report_documents as report_documents_module
from app.services.report_documents import (
    ReportDocumentError,
    ReportDocumentService,
    UnsupportedReportDocumentFormatError,
    sanitize_reason,
)
from app.schemas.report_documents import ReportOverviewDocumentCreateRequest
from app.tests.test_reports import BUSINESS_TABLES, counts, seed_orders_and_production


def config(tmp_path):
    c = DatabaseConfig(path=tmp_path / "report-documents.sqlite")
    initialize_database(c)
    return c


def service(tmp_path):
    c = config(tmp_path)
    return c, ReportDocumentService(c, documents_dir=tmp_path / "exports" / "report-documents")


def test_status_and_empty_list_work_on_empty_db(tmp_path):
    _c, svc = service(tmp_path)
    status = svc.status()
    assert status.available_formats == ["markdown"]
    assert status.available_document_types == ["workshop_overview"]
    assert status.can_create is True
    assert status.documents_count == 0
    assert "вручную" in status.message
    listing = svc.list_documents()
    assert listing.items == []
    assert listing.total == 0


def test_create_overview_markdown_document_on_empty_db(tmp_path):
    c, svc = service(tmp_path)
    before = counts(c)
    response = svc.create_overview_document(ReportOverviewDocumentCreateRequest(format="markdown", reason="monthly_check"))
    metadata = response.document
    md_path = svc.documents_dir / metadata.filename
    json_path = svc.documents_dir / metadata.metadata_filename
    assert response.message == "Документ отчета создан."
    assert metadata.id.startswith("workshop-overview-")
    assert metadata.document_type == "workshop_overview"
    assert metadata.format == "markdown"
    assert metadata.source == "reports.overview"
    assert metadata.source_generated_at is not None
    assert metadata.size_bytes > 0
    assert md_path.exists()
    assert json_path.exists()
    assert counts(c) == before

    text = md_path.read_text(encoding="utf-8")
    assert "# Сводка мастерской" in text
    for section in (
        "## Когда сформировано",
        "## Краткая сводка",
        "## Склад",
        "## Заказы",
        "## Производство",
        "## Алерты и закупки",
        "## Базовые финансы",
        "## Предупреждения и неполные данные",
        "## Важные ограничения",
    ):
        assert section in text
    assert "не бухгалтерский или налоговый отчет" in text
    assert "Налог не рассчитывается" in text
    assert "Система не придумывает налоговые ставки" in text

    sidecar = json.loads(json_path.read_text(encoding="utf-8"))
    assert sidecar["id"] == metadata.id
    assert sidecar["filename"] == metadata.filename
    listing = svc.list_documents()
    assert listing.total == 1
    assert listing.items[0].id == metadata.id


def test_generated_markdown_includes_report_warnings_and_finance_limits(tmp_path):
    c, svc = service(tmp_path)
    seed_orders_and_production(c)
    response = svc.create_overview_document(ReportOverviewDocumentCreateRequest())
    text = (svc.documents_dir / response.document.filename).read_text(encoding="utf-8")
    assert "Не у всех произведённых заказов указана цена продажи." in text
    assert "Не для всех производственных партий известна себестоимость." in text
    assert "Маржа рассчитана только" in text
    assert "Известная выручка: 1200.10" in text
    assert "Известная себестоимость: 150.10" in text
    assert "Известная маржа: 1050.00" in text
    assert "Полных финансовых записей: 1" in text
    assert "Неполных записей для расчета маржи: 1" in text


@pytest.mark.parametrize("fmt", ["pdf", "docx"])
def test_unsupported_formats_are_rejected(tmp_path, fmt):
    _c, svc = service(tmp_path)
    with pytest.raises(UnsupportedReportDocumentFormatError, match="Markdown"):
        svc.create_overview_document(ReportOverviewDocumentCreateRequest(format=fmt))


def test_reason_is_sanitized_and_path_traversal_cannot_affect_output_path(tmp_path):
    assert sanitize_reason("../../secret/месяц") == "secret_месяц"
    _c, svc = service(tmp_path)
    response = svc.create_overview_document(ReportOverviewDocumentCreateRequest(reason="../../secret/месяц"))
    md_path = (svc.documents_dir / response.document.filename).resolve()
    assert md_path.parent == svc.documents_dir.resolve()
    assert ".." not in response.document.filename
    assert not (tmp_path / "secret").exists()


def test_multiple_documents_do_not_overwrite_each_other(tmp_path):
    _c, svc = service(tmp_path)
    first = svc.create_overview_document(ReportOverviewDocumentCreateRequest()).document
    second = svc.create_overview_document(ReportOverviewDocumentCreateRequest()).document
    assert first.filename != second.filename
    assert (svc.documents_dir / first.filename).exists()
    assert (svc.documents_dir / second.filename).exists()
    assert svc.list_documents().total == 2


def test_stale_metadata_sidecar_gets_suffixed_pair_without_orphan_markdown(tmp_path, monkeypatch):
    _c, svc = service(tmp_path)
    svc.documents_dir.mkdir(parents=True)
    stale_sidecar = svc.documents_dir / "workshop-overview-20260706-123456.json"
    stale_sidecar.write_text('{"stale": true}\n', encoding="utf-8")

    monkeypatch.setattr(
        report_documents_module,
        "_document_id",
        lambda created_at: "workshop-overview-20260706-123456",
    )

    response = svc.create_overview_document(ReportOverviewDocumentCreateRequest())

    assert response.document.id == "workshop-overview-20260706-123456-1"
    assert response.document.filename == "workshop-overview-20260706-123456-1.md"
    assert response.document.metadata_filename == "workshop-overview-20260706-123456-1.json"
    assert stale_sidecar.exists()
    assert not (svc.documents_dir / "workshop-overview-20260706-123456.md").exists()
    assert (svc.documents_dir / response.document.filename).exists()
    assert (svc.documents_dir / response.document.metadata_filename).exists()
    for md_path in svc.documents_dir.glob("*.md"):
        assert md_path.with_suffix(".json").exists()


def test_metadata_write_failure_removes_created_markdown(tmp_path, monkeypatch):
    _c, svc = service(tmp_path)
    original_write = report_documents_module._write_text_exclusive

    def flaky_write(path: Path, text: str) -> None:
        if path.suffix == ".json":
            raise OSError("metadata write failed")
        original_write(path, text)

    monkeypatch.setattr(report_documents_module, "_write_text_exclusive", flaky_write)

    with pytest.raises(ReportDocumentError, match="Не удалось создать документ отчета"):
        svc.create_overview_document(ReportOverviewDocumentCreateRequest())

    assert list(svc.documents_dir.glob("*.md")) == []
    assert list(svc.documents_dir.glob("*.json")) == []


def test_document_generation_only_writes_report_document_files(tmp_path):
    c, svc = service(tmp_path)
    before = counts(c)
    svc.create_overview_document(ReportOverviewDocumentCreateRequest())
    assert counts(c) == before
    assert not (tmp_path / "backups").exists()
    export_root = tmp_path / "exports"
    json_exports = [p for p in export_root.rglob("*.json") if p.parent == export_root]
    assert json_exports == []
    with sqlite3.connect(c.path) as con:
        assert con.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == before["alerts"]
        assert con.execute("SELECT COUNT(*) FROM purchase_suggestions").fetchone()[0] == before["purchase_suggestions"]


def test_document_generation_uses_reports_service_output(tmp_path, monkeypatch):
    _c, svc = service(tmp_path)
    called = False
    original = svc.reports_service.get_overview

    def wrapped():
        nonlocal called
        called = True
        return original()

    monkeypatch.setattr(svc.reports_service, "get_overview", wrapped)
    svc.create_overview_document(ReportOverviewDocumentCreateRequest())
    assert called is True
