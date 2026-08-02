"""The CR-009 B1 ledger, verifier and exactly-once finalizer.

The load-bearing claim of this slice is that a completed document and its
AuditLog event are *not* one transaction, and that the application stays honest
about that anyway: the document survives every audit failure, the missing event
is never forgotten, and it is never written twice. These tests exercise each of
those separately, including the two concurrent-writer cases that a single-run
happy path would hide.
"""

import json
from pathlib import Path
import sqlite3
import threading
import uuid

import pytest

from app.db.config import DatabaseConfig
from app.domain.artifact_audit_operations import (
    ARTIFACT_KIND_REPORT_DOCUMENT,
    AUDIT_ACTION_REPORT_DOCUMENT_CREATED,
    ArtifactAuditOperationError,
    is_canonical_operation_id,
    is_safe_artifact_filename,
    new_operation_id,
    validate_artifact_filename,
    validate_operation_id,
)
from app.repositories.artifact_audit_operations import ArtifactAuditOperationRepository
from app.repositories.audit import AuditLogRepository
from app.services.database import initialize_database
from app.services import report_document_audit as audit_module
from app.services.report_document_audit import (
    PENDING_AUDIT_MESSAGE,
    ReportDocumentAuditService,
    ReportDocumentAuditTrackingUnavailableError,
    SUPPORTED_DOCUMENT_TYPE,
    SUPPORTED_FORMAT_EXTENSIONS,
)
from app.services.report_documents import PDF_FORMAT, ReportDocumentService, SUPPORTED_FORMAT
from app.schemas.report_documents import ReportOverviewDocumentCreateRequest


def setup(tmp_path):
    config = DatabaseConfig(path=tmp_path / "audit.sqlite")
    initialize_database(config)
    documents_dir = tmp_path / "exports" / "report-documents"
    documents_dir.mkdir(parents=True)
    return config, documents_dir, ReportDocumentAuditService(documents_dir, config)


def write_pair(documents_dir: Path, document_id="workshop-overview-20260731-101112", fmt="markdown", **overrides):
    """Write a genuine document/sidecar pair the verifier should accept."""
    extension = SUPPORTED_FORMAT_EXTENSIONS[fmt]
    document_path = documents_dir / f"{document_id}{extension}"
    sidecar_path = documents_dir / f"{document_id}.json"
    body = "# Сводка мастерской\n" if fmt == "markdown" else "%PDF-1.4\n%%EOF\n"
    document_path.write_text(body, encoding="utf-8")
    metadata = {
        "id": document_id,
        "document_type": SUPPORTED_DOCUMENT_TYPE,
        "format": fmt,
        "filename": document_path.name,
        "metadata_filename": sidecar_path.name,
        "created_at": "2026-07-31T10:11:12Z",
        "source": "reports.overview",
        "source_generated_at": "2026-07-31T10:11:00Z",
        "title": "Сводка мастерской",
        "warnings_count": 0,
        "size_bytes": document_path.stat().st_size,
    }
    metadata.update(overrides)
    sidecar_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    return document_path, sidecar_path


def prepare(service, document_path: Path, sidecar_path: Path) -> str:
    return service.prepare_operation(primary_filename=document_path.name, companion_filename=sidecar_path.name)


def audit_rows(config):
    with sqlite3.connect(config.path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT id, action, entity_type, entity_id, summary, actor_type, metadata_json FROM audit_logs ORDER BY id"
        ).fetchall()


# --------------------------------------------------------------------------
# Operation and filename identity
# --------------------------------------------------------------------------

def test_generated_operation_ids_are_canonical_lowercase_uuids():
    ids = {new_operation_id() for _ in range(50)}

    assert len(ids) == 50
    for value in ids:
        assert is_canonical_operation_id(value)
        assert value == value.lower()
        assert str(uuid.UUID(value)) == value
        assert validate_operation_id(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "not-a-uuid",
        "11111111-1111-4111-8111-11111111111",
        "11111111111141118111111111111111",
        "{11111111-1111-4111-8111-111111111111}",
        "urn:uuid:11111111-1111-4111-8111-111111111111",
        "11111111-1111-4111-8111-111111111111 ",
        None,
        12345,
    ],
)
def test_non_canonical_operation_ids_are_rejected(value):
    assert is_canonical_operation_id(value) is False
    with pytest.raises(ArtifactAuditOperationError):
        validate_operation_id(value)


def test_an_uppercase_uuid_spelling_is_rejected():
    """One identity must have exactly one spelling.

    `uuid.UUID` would happily parse the uppercase form, and accepting it would
    let the same operation exist under two primary keys — which is precisely the
    idempotency the whole exactly-once argument rests on.
    """
    canonical = new_operation_id()

    assert is_canonical_operation_id(canonical.upper()) is False
    with pytest.raises(ArtifactAuditOperationError):
        validate_operation_id(canonical.upper())


@pytest.mark.parametrize(
    "value",
    ["workshop-overview-20260731-101112.md", "workshop-overview-20260731-101112-1.json", "a.pdf"],
)
def test_safe_relative_filenames_are_accepted(value):
    assert is_safe_artifact_filename(value) is True
    assert validate_artifact_filename(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "/etc/passwd",
        "/tmp/absolute.md",
        "../escape.md",
        "../../escape.md",
        "nested/name.md",
        "nested\\name.md",
        "with\x00nul.md",
        "with\nnewline.md",
        "with\tcontrol.md",
        "with\x7fdelete.md",
        ".",
        "..",
        " leading.md",
        "trailing.md ",
        None,
        42,
    ],
)
def test_unsafe_filenames_are_rejected(value):
    assert is_safe_artifact_filename(value) is False
    with pytest.raises(ArtifactAuditOperationError):
        validate_artifact_filename(value)


# --------------------------------------------------------------------------
# Ledger repository
# --------------------------------------------------------------------------

def test_prepare_read_count_and_transition_an_operation(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    repository = ArtifactAuditOperationRepository(config)
    document_path, sidecar_path = write_pair(documents_dir)

    operation_id = prepare(service, document_path, sidecar_path)
    operation = repository.get_operation(operation_id)

    assert operation is not None
    assert operation.artifact_kind == ARTIFACT_KIND_REPORT_DOCUMENT
    assert operation.audit_action == AUDIT_ACTION_REPORT_DOCUMENT_CREATED
    assert operation.status == "prepared"
    assert operation.audit_log_id is None
    assert operation.primary_filename == document_path.name
    assert operation.companion_filename == sidecar_path.name
    assert operation.is_unresolved is True
    assert repository.count_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT) == 1
    assert [item.operation_id for item in repository.list_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT)] == [operation_id]

    assert repository.mark_pending_audit(operation_id) is True
    assert repository.get_operation(operation_id).status == "pending_audit"
    assert repository.count_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT) == 1

    assert repository.mark_abandoned(operation_id) is True
    assert repository.get_operation(operation_id).status == "abandoned"
    assert repository.count_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT) == 0
    assert repository.list_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT) == []


def test_a_resolved_operation_is_never_reopened(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    repository = ArtifactAuditOperationRepository(config)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    repository.mark_abandoned(operation_id)

    assert repository.mark_pending_audit(operation_id) is False
    assert repository.mark_audited(operation_id, 1) is False
    assert repository.get_operation(operation_id).status == "abandoned"


def test_a_second_active_operation_cannot_own_the_same_identity(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    prepare(service, document_path, sidecar_path)

    assert service.is_identity_active(document_path.name, sidecar_path.name) is True
    with pytest.raises(ReportDocumentAuditTrackingUnavailableError):
        prepare(service, document_path, sidecar_path)


def test_a_shared_sidecar_name_counts_as_an_active_collision(tmp_path):
    """Two formats of one document ID share one `.json` name.

    A `prepared` Markdown operation owns its sidecar before the file exists, so
    a PDF request for the same ID must see the collision through the ledger —
    the filesystem cannot show it yet.
    """
    _config, documents_dir, service = setup(tmp_path)
    service.prepare_operation(
        primary_filename="workshop-overview-20260731-101112.md",
        companion_filename="workshop-overview-20260731-101112.json",
    )

    assert service.is_identity_active(
        "workshop-overview-20260731-101112.pdf", "workshop-overview-20260731-101112.json"
    ) is True
    assert service.is_identity_active(
        "workshop-overview-20260731-999999.pdf", "workshop-overview-20260731-999999.json"
    ) is False


def test_unsafe_identities_never_reach_the_ledger(tmp_path):
    _config, _documents_dir, service = setup(tmp_path)

    with pytest.raises(ReportDocumentAuditTrackingUnavailableError):
        service.prepare_operation(primary_filename="../escape.md", companion_filename="ok.json")
    with pytest.raises(ReportDocumentAuditTrackingUnavailableError):
        service.prepare_operation(primary_filename="ok.md", companion_filename="/tmp/escape.json")
    assert service.pending_count() == 0


def test_the_ledger_has_no_user_facing_route():
    """The ledger is internal: no API route may read or write it."""
    from app.main import create_app

    paths = {route.path for route in create_app().routes}

    assert not any("artifact-audit" in path or "audit-operations" in path or "ledger" in path for path in paths)


# --------------------------------------------------------------------------
# Verifier
# --------------------------------------------------------------------------

@pytest.mark.parametrize("fmt", ["markdown", "pdf"])
def test_a_valid_pair_verifies_and_is_left_byte_identical(tmp_path, fmt):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir, fmt=fmt)
    before = (document_path.read_bytes(), sidecar_path.read_bytes())
    operation_id = prepare(service, document_path, sidecar_path)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    verification = service.verify(operation)

    assert verification.outcome == "valid"
    assert verification.is_valid is True
    assert verification.metadata is not None
    assert verification.metadata.format == fmt
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before


def test_an_absent_pair_is_definitely_absent(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    document_path.unlink()
    sidecar_path.unlink()
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    assert service.verify(operation).outcome == "definitely_absent"


def mutate_and_verify(tmp_path, mutate, **write_kwargs):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir, **write_kwargs)
    operation_id = prepare(service, document_path, sidecar_path)
    mutate(document_path, sidecar_path)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    return service.verify(operation)


def test_a_missing_primary_file_alone_is_ambiguous(tmp_path):
    result = mutate_and_verify(tmp_path, lambda document, _sidecar: document.unlink())
    assert result.outcome == "ambiguous"
    assert result.reason == "primary-missing"


def test_a_missing_sidecar_alone_is_ambiguous(tmp_path):
    result = mutate_and_verify(tmp_path, lambda _document, sidecar: sidecar.unlink())
    assert result.outcome == "ambiguous"
    assert result.reason == "companion-missing"


def test_a_directory_in_place_of_the_primary_file_is_ambiguous(tmp_path):
    def replace(document: Path, _sidecar: Path):
        document.unlink()
        document.mkdir()

    result = mutate_and_verify(tmp_path, replace)
    assert result.outcome == "ambiguous"
    assert result.reason == "primary-not-regular-file"


def test_a_directory_in_place_of_the_sidecar_is_ambiguous(tmp_path):
    def replace(_document: Path, sidecar: Path):
        sidecar.unlink()
        sidecar.mkdir()

    result = mutate_and_verify(tmp_path, replace)
    assert result.outcome == "ambiguous"
    assert result.reason == "companion-not-regular-file"


def test_malformed_sidecar_json_is_ambiguous(tmp_path):
    result = mutate_and_verify(tmp_path, lambda _d, sidecar: sidecar.write_text("{not json", encoding="utf-8"))
    assert result.outcome == "ambiguous"
    assert result.reason == "metadata-unreadable"


def test_sidecar_json_that_is_not_the_metadata_model_is_ambiguous(tmp_path):
    result = mutate_and_verify(tmp_path, lambda _d, sidecar: sidecar.write_text('{"id": "x"}', encoding="utf-8"))
    assert result.outcome == "ambiguous"
    assert result.reason == "metadata-invalid"


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"filename": "other-document.md"}, "metadata-filename-mismatch"),
        ({"metadata_filename": "other-document.json"}, "metadata-companion-mismatch"),
        ({"document_type": "invoice"}, "unexpected-document-type"),
        ({"format": "docx"}, "unsupported-format"),
        ({"size_bytes": 999999}, "size-mismatch"),
    ],
)
def test_a_mismatched_sidecar_is_ambiguous_and_never_rewritten(tmp_path, overrides, expected_reason):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
    metadata.update(overrides)
    sidecar_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    before = (document_path.read_bytes(), sidecar_path.read_bytes())
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == expected_reason
    # Never audited, never deleted, never repaired.
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before
    assert document_path.exists() and sidecar_path.exists()


def test_an_extension_that_disagrees_with_the_metadata_format_is_ambiguous(tmp_path):
    """A `.md` file whose sidecar claims PDF is not a document we may audit."""
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
    metadata["format"] = "pdf"
    sidecar_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    operation_id = prepare(service, document_path, sidecar_path)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "primary-name-contract-mismatch"


def test_a_metadata_id_that_disagrees_with_the_filename_contract_is_ambiguous(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
    metadata["id"] = "workshop-overview-19990101-000000"
    sidecar_path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
    operation_id = prepare(service, document_path, sidecar_path)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "primary-name-contract-mismatch"


@pytest.mark.parametrize("unsafe", ["../escape.md", "nested/name.md", "", "with\x00nul.md"])
def test_an_unsafe_stored_filename_is_ambiguous_on_read(tmp_path, unsafe):
    """Validation is repeated on read, not trusted from write time.

    The row is inserted here through raw SQL precisely because the repository
    would refuse it — the point is that a ledger row that somehow *does* hold an
    unsafe name is still refused when reconciliation reads it back.
    """
    config, documents_dir, service = setup(tmp_path)
    with sqlite3.connect(config.path) as connection:
        connection.execute(
            "INSERT INTO artifact_audit_operations"
            " (operation_id, artifact_kind, primary_filename, companion_filename, status, audit_action)"
            " VALUES (?, 'report_document', ?, 'ok.json', 'prepared', 'report_document.created')",
            (new_operation_id(), unsafe or "x"),
        )
    operation = ArtifactAuditOperationRepository(config).list_unresolved(ARTIFACT_KIND_REPORT_DOCUMENT)[0]
    object.__setattr__(operation, "primary_filename", unsafe)

    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "unsafe-primary-filename"


def test_a_symlink_leaving_the_documents_directory_is_refused(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    real_document, real_sidecar = write_pair(outside)
    link_document = documents_dir / real_document.name
    link_sidecar = documents_dir / real_sidecar.name
    try:
        link_document.symlink_to(real_document)
        link_sidecar.symlink_to(real_sidecar)
    except (OSError, NotImplementedError):
        pytest.skip("This filesystem does not support symlinks.")
    operation_id = prepare(service, link_document, link_sidecar)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    verification = service.verify(operation)

    assert verification.outcome == "ambiguous"
    assert verification.reason == "path-outside-documents-directory"


def test_verification_never_rerenders_or_consults_current_report_data(tmp_path, monkeypatch):
    """The verifier reads files; it does not regenerate or compare content."""
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)

    from app.services import reports as reports_module

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Verification must not consult ReportsService.")

    monkeypatch.setattr(reports_module.ReportsService, "get_overview", forbidden)

    assert service.verify(operation).outcome == "valid"


def test_the_verifier_format_table_agrees_with_the_renderer():
    """The verifier keeps its own copy of the format vocabulary to avoid an
    import cycle; this is what stops the two copies from drifting apart."""
    from app.services import report_documents as renderer

    assert SUPPORTED_DOCUMENT_TYPE == renderer.SUPPORTED_DOCUMENT_TYPE
    assert set(SUPPORTED_FORMAT_EXTENSIONS) == {renderer.SUPPORTED_FORMAT, renderer.PDF_FORMAT}
    assert SUPPORTED_FORMAT_EXTENSIONS[renderer.SUPPORTED_FORMAT] == ".md"
    assert SUPPORTED_FORMAT_EXTENSIONS[renderer.PDF_FORMAT] == ".pdf"


# --------------------------------------------------------------------------
# Exactly-once finalization
# --------------------------------------------------------------------------

def test_finalization_creates_exactly_one_event_with_the_accepted_contract(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "recorded"
    assert finalization.is_recorded is True
    assert finalization.artifact_is_authoritative is True
    assert finalization.verification.is_valid is True
    audit_log_id = finalization.audit_log_id

    rows = audit_rows(config)
    assert len(rows) == 1
    row = rows[0]
    assert audit_log_id == row["id"]
    assert row["action"] == "report_document.created"
    assert row["entity_type"] == "report_document"
    assert row["entity_id"] == operation_id
    assert row["actor_type"] == "user"
    assert row["summary"] == "Report document created"
    assert json.loads(row["metadata_json"]) == {
        "operation_id": operation_id,
        "document_type": "workshop_overview",
        "format": "markdown",
        "reconciled_after_failure": False,
    }
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    assert operation.status == "audited"
    assert operation.audit_log_id == audit_log_id
    assert service.pending_count() == 0


def test_repeated_sequential_finalization_creates_exactly_one_event(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)

    first = service.finalize(operation_id, reconciled_after_failure=False)
    second = service.finalize(operation_id, reconciled_after_failure=True)
    third = service.finalize(operation_id, reconciled_after_failure=True)

    assert [f.outcome for f in (first, second, third)] == ["recorded"] * 3
    # The repeat calls reuse the already committed event rather than inserting.
    assert first.audit_log_id == second.audit_log_id == third.audit_log_id
    assert len(audit_rows(config)) == 1


def test_startup_then_pre_create_reconciliation_creates_exactly_one_event(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)

    first = service.reconcile()
    second = service.reconcile()

    assert first.audited == 1
    assert second.examined == 0
    assert len(audit_rows(config)) == 1
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == "audited"


def test_two_concurrent_finalizers_create_exactly_one_event(tmp_path):
    """Concurrency is the case a sequential test cannot reach.

    `BEGIN IMMEDIATE` orders the two writers; the loser re-reads inside its own
    transaction, sees `audited`, and resolves the existing ID instead of
    inserting a second event.
    """
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)

    barrier = threading.Barrier(2)
    results: list[int | None] = []
    lock = threading.Lock()

    def run():
        worker = ReportDocumentAuditService(documents_dir, config)
        barrier.wait()
        outcome = worker.finalize(operation_id, reconciled_after_failure=False)
        with lock:
            results.append(outcome.audit_log_id if outcome.is_recorded else None)

    threads = [threading.Thread(target=run) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    rows = audit_rows(config)
    assert len(rows) == 1
    assert len(results) == 2
    # Both callers resolve the same committed event; neither invents a second.
    assert set(results) == {rows[0]["id"]}


def test_an_audit_insert_failure_leaves_the_operation_unresolved_and_the_files_intact(tmp_path, monkeypatch):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    before = (document_path.read_bytes(), sidecar_path.read_bytes())
    operation_id = prepare(service, document_path, sidecar_path)

    def failing_create_log(*_args, **_kwargs):
        raise sqlite3.OperationalError("audit log insert failed")

    monkeypatch.setattr(AuditLogRepository, "create_log", failing_create_log)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    # The pair is verified, so this is a pending Journal entry and never an
    # invalid artifact: the document itself is still authoritative.
    assert finalization.outcome == "audit_pending"
    assert finalization.artifact_is_authoritative is True
    assert finalization.is_recorded is False
    assert finalization.audit_log_id is None

    assert audit_rows(config) == []
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    assert operation.status == "pending_audit"
    assert operation.audit_log_id is None
    assert service.pending_count() == 1
    # The artifact is untouched: nothing was deleted as compensation.
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before


def test_a_ledger_update_failure_rolls_back_the_audit_insert(tmp_path, monkeypatch):
    """Both writes commit together or neither does.

    Simulated at the point where the AuditLog row has already been inserted
    inside the transaction — the only way to prove the insert is genuinely rolled
    back rather than merely never attempted.
    """
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    before = (document_path.read_bytes(), sidecar_path.read_bytes())
    operation_id = prepare(service, document_path, sidecar_path)

    monkeypatch.setattr(ArtifactAuditOperationRepository, "mark_audited", lambda *_a, **_k: False)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    # The pair is verified, so this is a pending Journal entry and never an
    # invalid artifact: the document itself is still authoritative.
    assert finalization.outcome == "audit_pending"
    assert finalization.artifact_is_authoritative is True
    assert finalization.is_recorded is False
    assert finalization.audit_log_id is None

    assert audit_rows(config) == []
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    assert operation.status == "pending_audit"
    assert operation.audit_log_id is None
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before


def test_no_second_sqlite_connection_participates_in_the_finalizer(tmp_path, monkeypatch):
    """One caller-owned connection holds the write transaction.

    A second connection opened while the first holds `BEGIN IMMEDIATE` would
    either deadlock against it or commit outside it; both break the "commit
    together or not at all" guarantee.
    """
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)

    opened: list[int] = []
    real_connect = sqlite3.connect
    inside = {"active": False}

    def counting_connect(*args, **kwargs):
        if inside["active"]:
            opened.append(1)
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", counting_connect)

    real_commit = audit_module.ReportDocumentAuditService._commit_finalization

    def traced(self, *args, **kwargs):
        inside["active"] = True
        try:
            return real_commit(self, *args, **kwargs)
        finally:
            inside["active"] = False

    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "_commit_finalization", traced)

    assert service.finalize(operation_id, reconciled_after_failure=False).is_recorded
    # Exactly the one connection the transaction itself opened.
    assert sum(opened) == 1


def test_reconciliation_marks_immediate_and_recovered_events_apart(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    immediate_document, immediate_sidecar = write_pair(documents_dir, document_id="workshop-overview-20260731-101112")
    recovered_document, recovered_sidecar = write_pair(documents_dir, document_id="workshop-overview-20260731-202122")
    immediate_id = prepare(service, immediate_document, immediate_sidecar)
    recovered_id = prepare(service, recovered_document, recovered_sidecar)

    service.finalize(immediate_id, reconciled_after_failure=False)
    service.reconcile()

    metadata = {row["entity_id"]: json.loads(row["metadata_json"]) for row in audit_rows(config)}
    assert metadata[immediate_id]["reconciled_after_failure"] is False
    assert metadata[recovered_id]["reconciled_after_failure"] is True


def test_no_filename_path_reason_profile_or_report_content_reaches_the_audit_log(tmp_path):
    """The event says what happened, not what the document contains."""
    config, documents_dir, _service = setup(tmp_path)
    service = ReportDocumentService(config, documents_dir=documents_dir)
    from app.schemas.settings import WorkshopProfileUpdateRequest
    from app.services.settings import WorkshopProfileSettingsService

    WorkshopProfileSettingsService(config).update_profile(
        WorkshopProfileUpdateRequest(workshop_name="Мастерская Марии", workshop_contact_text="+7 900 000-00-00")
    )
    response = service.create_overview_document(
        ReportOverviewDocumentCreateRequest(format=SUPPORTED_FORMAT, reason="секретная причина")
    )

    row = next(row for row in audit_rows(config) if row["action"] == "report_document.created")
    serialized = f"{row['summary']}|{row['metadata_json']}|{row['entity_id']}|{row['entity_type']}"
    for forbidden in (
        response.document.filename,
        response.document.metadata_filename,
        response.document.id,
        str(documents_dir),
        "секретная",
        "причина",
        "Мастерская Марии",
        "+7 900",
        ".md",
        "/",
    ):
        assert forbidden not in serialized, forbidden
    assert set(json.loads(row["metadata_json"])) == {
        "operation_id",
        "document_type",
        "format",
        "reconciled_after_failure",
    }


# --------------------------------------------------------------------------
# Reconciliation classification
# --------------------------------------------------------------------------

def test_reconciliation_abandons_a_definitely_absent_pair(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    document_path.unlink()
    sidecar_path.unlink()

    result = service.reconcile()

    assert result.abandoned == 1
    assert result.audited == 0
    assert audit_rows(config) == []
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == "abandoned"
    assert service.pending_count() == 0


def test_reconciliation_leaves_an_ambiguous_pair_unresolved_and_counted(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    sidecar_path.unlink()
    document_bytes = document_path.read_bytes()

    result = service.reconcile()

    assert result.unresolved == 1
    assert result.audited == 0
    assert result.abandoned == 0
    assert audit_rows(config) == []
    assert ArtifactAuditOperationRepository(config).get_operation(operation_id).status == "pending_audit"
    assert service.pending_count() == 1
    # Not deleted and not repaired, only left alone.
    assert document_path.read_bytes() == document_bytes


def test_reconciliation_is_idempotent_and_never_raises(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    valid_document, valid_sidecar = write_pair(documents_dir, document_id="workshop-overview-20260731-101112")
    ambiguous_document, ambiguous_sidecar = write_pair(documents_dir, document_id="workshop-overview-20260731-202122")
    absent_document, absent_sidecar = write_pair(documents_dir, document_id="workshop-overview-20260731-303132")
    prepare(service, valid_document, valid_sidecar)
    prepare(service, ambiguous_document, ambiguous_sidecar)
    prepare(service, absent_document, absent_sidecar)
    ambiguous_sidecar.unlink()
    absent_document.unlink()
    absent_sidecar.unlink()

    first = service.reconcile()
    for _ in range(3):
        service.reconcile()

    assert first.examined == 3
    assert (first.audited, first.abandoned, first.unresolved) == (1, 1, 1)
    assert len(audit_rows(config)) == 1
    assert service.pending_count() == 1


def test_reconciliation_ignores_files_that_no_operation_recorded(tmp_path):
    """No directory scan: an untracked file is invisible to reconciliation."""
    config, documents_dir, service = setup(tmp_path)
    write_pair(documents_dir, document_id="workshop-overview-20250101-000000")

    result = service.reconcile()

    assert result.examined == 0
    assert audit_rows(config) == []
    assert service.pending_count() == 0


def test_reconciliation_survives_a_ledger_read_failure(tmp_path, monkeypatch):
    _config, documents_dir, service = setup(tmp_path)

    def failing(*_args, **_kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "list_unresolved", failing)

    result = service.reconcile()

    assert result.failed == 1
    assert result.audited == 0


def test_the_pending_message_is_the_exact_accepted_warning():
    assert PENDING_AUDIT_MESSAGE == (
        "Документ создан, но запись в журнал действий пока не добавлена. "
        "Приложение повторит попытку при следующем запуске или перед созданием следующего документа."
    )
    for forbidden in ("SQLite", "sqlite", "ledger", "operation_id", ".md", ".json", "/"):
        assert forbidden not in PENDING_AUDIT_MESSAGE


# --------------------------------------------------------------------------
# AuditLog repository compatibility
# --------------------------------------------------------------------------

def test_create_log_returns_the_inserted_row_id(tmp_path):
    config = DatabaseConfig(path=tmp_path / "audit-repo.sqlite")
    initialize_database(config)
    repository = AuditLogRepository(config)

    first = repository.create_log(action="client.created", entity_type="client", entity_id="1", summary="Client created: A")
    second = repository.create_log(action="client.updated", entity_type="client", entity_id="1", summary="Client updated: A")

    assert isinstance(first, int) and isinstance(second, int)
    assert second > first
    assert [row["id"] for row in audit_rows(config)] == [first, second]


def test_existing_audit_log_callers_still_behave_identically(tmp_path):
    """Representative existing call sites keep their transaction ownership."""
    config = DatabaseConfig(path=tmp_path / "existing-callers.sqlite")
    initialize_database(config)
    from app.domain.ingredients import IngredientDraft
    from app.schemas.settings import WorkshopProfileUpdateRequest
    from app.services.ingredients import IngredientService
    from app.services.settings import WorkshopProfileSettingsService

    # Two different existing ownership styles: the profile service opens a
    # `session`, the ingredient service opens a `transaction`. Both ignore the
    # newly returned ID and must be unaffected by it.
    WorkshopProfileSettingsService(config).update_profile(WorkshopProfileUpdateRequest(workshop_name="Мастерская"))
    ingredient = IngredientService(config).create_ingredient(
        IngredientDraft.create(name="Масло ши", category="oil", default_unit="g")
    )

    rows = audit_rows(config)
    actions = [row["action"] for row in rows]
    assert actions == ["workshop_profile.updated", "ingredient.created"]
    assert rows[1]["entity_id"] == str(ingredient.id)
    assert rows[1]["summary"] == "Ingredient created: Масло ши"


def test_create_log_honours_a_caller_owned_connection_and_its_rollback(tmp_path):
    config = DatabaseConfig(path=tmp_path / "caller-owned.sqlite")
    initialize_database(config)
    repository = AuditLogRepository(config)

    connection = sqlite3.connect(config.path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        row_id = repository.create_log(
            action="client.created", entity_type="client", entity_id="1", summary="Client created: A", connection=connection
        )
        assert isinstance(row_id, int)
        connection.rollback()
    finally:
        connection.close()

    assert audit_rows(config) == []


# --------------------------------------------------------------------------
# Typed finalization: verification failure is not a pending Journal entry
#
# The load-bearing distinction of this slice. A single `int | None` could not
# tell "the pair did not verify" apart from "the pair verified but its Journal
# entry did not commit", and the create path mapped both to `201 pending` — so a
# document that failed mandatory verification was reported to the user as
# created. These pin the three outcomes apart.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("outcome", ["ambiguous", "definitely_absent"])
def test_a_non_valid_verification_is_artifact_invalid_and_writes_no_event(tmp_path, monkeypatch, outcome):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    before = (document_path.read_bytes(), sidecar_path.read_bytes())
    operation_id = prepare(service, document_path, sidecar_path)

    monkeypatch.setattr(
        audit_module.ReportDocumentAuditService,
        "verify",
        lambda self, operation: audit_module.ReportDocumentVerification(outcome, "injected"),
    )

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.artifact_is_authoritative is False
    assert finalization.is_recorded is False
    assert finalization.audit_log_id is None
    assert audit_rows(config) == []
    # Unresolved and counted — never abandoned on the immediate create path, and
    # never silently forgotten.
    operation = ArtifactAuditOperationRepository(config).get_operation(operation_id)
    assert operation.status in ("prepared", "pending_audit")
    assert service.pending_count() == 1
    # The pair is left exactly as it is: this operation could not prove it owns
    # those files, so deleting them could destroy something else's.
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before


def test_a_real_size_mismatch_is_artifact_invalid(tmp_path):
    """A genuine verifier verdict, not an injected one, reaches the same outcome."""
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    # The recorded size no longer matches the bytes on disk.
    document_path.write_text("truncated", encoding="utf-8")

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.verification.outcome == "ambiguous"
    assert finalization.verification.reason == "size-mismatch"
    assert audit_rows(config) == []
    assert service.pending_count() == 1


def test_a_verifier_that_raises_is_artifact_invalid_and_destroys_nothing(tmp_path, monkeypatch):
    """A verifier defect proves nothing about the pair, so it cannot be trusted.

    It must still not escape — `finalize` runs after both files exist — but
    degrading it to `audit_pending` would let an unverified document reach the
    user as created with a merely pending Journal entry.
    """
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    before = (document_path.read_bytes(), sidecar_path.read_bytes())
    operation_id = prepare(service, document_path, sidecar_path)

    def defective(*_args, **_kwargs):
        raise TypeError("injected programming defect")

    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "verify", defective)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.artifact_is_authoritative is False
    assert audit_rows(config) == []
    assert service.pending_count() == 1
    assert (document_path.read_bytes(), sidecar_path.read_bytes()) == before


def test_an_unreadable_ledger_is_artifact_invalid_rather_than_a_guess(tmp_path, monkeypatch):
    """Authority was never established, so the pair must not be called valid."""
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)

    def failing_get(*_args, **_kwargs):
        raise sqlite3.OperationalError("injected ledger read failure")

    monkeypatch.setattr(ArtifactAuditOperationRepository, "get_operation", failing_get)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert finalization.artifact_is_authoritative is False
    assert finalization.verification is None
    assert document_path.exists() and sidecar_path.exists()


def test_a_missing_operation_is_artifact_invalid(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    finalization = service.finalize(new_operation_id(), reconciled_after_failure=False)
    assert finalization.outcome == "artifact_invalid"
    assert audit_rows(config) == []


def test_an_abandoned_operation_is_artifact_invalid(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    ArtifactAuditOperationRepository(config).mark_abandoned(operation_id)

    finalization = service.finalize(operation_id, reconciled_after_failure=False)

    assert finalization.outcome == "artifact_invalid"
    assert audit_rows(config) == []


def test_an_already_audited_operation_is_recorded_with_the_existing_id(tmp_path):
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)
    first = service.finalize(operation_id, reconciled_after_failure=False)

    again = service.finalize(operation_id, reconciled_after_failure=True)

    assert again.outcome == "recorded"
    assert again.audit_log_id == first.audit_log_id
    assert len(audit_rows(config)) == 1


def test_a_transient_verifier_fault_still_reconciles_exactly_once_afterwards(tmp_path, monkeypatch):
    """The unresolved operation is recoverable once the fault is removed."""
    config, documents_dir, service = setup(tmp_path)
    document_path, sidecar_path = write_pair(documents_dir)
    operation_id = prepare(service, document_path, sidecar_path)

    def defective(*_args, **_kwargs):
        raise TypeError("injected transient verifier fault")

    monkeypatch.setattr(audit_module.ReportDocumentAuditService, "verify", defective)
    assert service.finalize(operation_id, reconciled_after_failure=False).outcome == "artifact_invalid"
    assert audit_rows(config) == []
    monkeypatch.undo()

    first = service.reconcile()
    second = service.reconcile()

    assert first.audited == 1
    assert second.examined == 0
    rows = audit_rows(config)
    assert len(rows) == 1
    assert json.loads(rows[0]["metadata_json"])["reconciled_after_failure"] is True
    assert service.pending_count() == 0


# --------------------------------------------------------------------------
# Mutation protection for the typed outcome vocabulary
# --------------------------------------------------------------------------


def test_only_recorded_and_audit_pending_are_authoritative():
    """Renaming `artifact_invalid` into a success would defeat the whole slice."""
    Finalization = audit_module.ReportDocumentFinalization
    assert Finalization("recorded", audit_log_id=1).artifact_is_authoritative is True
    assert Finalization("audit_pending").artifact_is_authoritative is True
    assert Finalization("artifact_invalid").artifact_is_authoritative is False
    assert Finalization("recorded", audit_log_id=1).is_recorded is True
    assert Finalization("audit_pending").is_recorded is False
    assert Finalization("artifact_invalid").is_recorded is False


def test_the_create_path_refuses_an_invalid_artifact_and_keeps_the_pair(tmp_path, monkeypatch):
    """The create service, not just the finalizer, must enforce the boundary."""
    config, documents_dir, _service = setup(tmp_path)
    service = ReportDocumentService(config, documents_dir=documents_dir)

    monkeypatch.setattr(
        audit_module.ReportDocumentAuditService,
        "finalize",
        lambda self, operation_id, *, reconciled_after_failure: audit_module.ReportDocumentFinalization(
            "artifact_invalid"
        ),
    )

    with pytest.raises(audit_module.ReportDocumentArtifactUnverifiedError):
        service.create_overview_document(ReportOverviewDocumentCreateRequest(format=SUPPORTED_FORMAT))

    # The pair survives the refusal: ownership is exactly what failed to verify.
    assert len(list(documents_dir.glob("*.md"))) == 1
    assert len(list(documents_dir.glob("*.json"))) == 1
    assert audit_rows(config) == []


def test_the_create_path_still_accepts_a_verified_artifact_with_a_pending_journal(tmp_path, monkeypatch):
    config, documents_dir, _service = setup(tmp_path)
    service = ReportDocumentService(config, documents_dir=documents_dir)

    monkeypatch.setattr(
        audit_module.ReportDocumentAuditService,
        "finalize",
        lambda self, operation_id, *, reconciled_after_failure: audit_module.ReportDocumentFinalization(
            "audit_pending"
        ),
    )

    response = service.create_overview_document(ReportOverviewDocumentCreateRequest(format=SUPPORTED_FORMAT))

    assert response.audit_status == "pending"
    assert response.message == "Документ отчета создан."
    assert response.audit_message == PENDING_AUDIT_MESSAGE
