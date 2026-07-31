MIGRATION_ID = "0020_artifact_audit_operations"

TABLE_NAME = "artifact_audit_operations"


def upgrade(connection):
    """Create the bounded CR-009 artifact-audit operation ledger.

    Additive only: one new table plus its indexes. Nothing existing is read,
    rewritten or backfilled. Report documents, exports and backups created
    before this migration keep no ledger row and generate no historical
    AuditLog event — inventing one would fabricate history the application
    never observed (ADR 0013, "Legacy and startup behavior").

    The table is deliberately not a generic outbox. It is owned by the three
    artifact operations named in CR-009, and every vocabulary column is pinned
    by a `CHECK` so an unrelated caller cannot quietly widen it. `C3-II-B1`
    writes only `report_document` rows; `json_export` and `manual_backup` are
    reserved by the accepted decision but have no runtime writer yet.

    The two conditional `CHECK` constraints encode the accepted invariants that
    the ledger — not the calling service — is responsible for:

    - an `audited` row carries the AuditLog row it committed with, and a row in
      any other status carries none, so a half-finalized operation cannot claim
      an event it never inserted;
    - a `report_document` operation always records its metadata sidecar, because
      the document and its sidecar are one artifact unit and reconciliation
      cannot verify the unit without both names.

    The partial unique index is the durable half of duplicate-event protection:
    at most one *active* (`prepared` or `pending_audit`) operation may own one
    `(artifact_kind, primary_filename)` identity, so a second operation can
    never reconcile or audit an artifact that is already being tracked.
    Resolved rows (`audited`, `abandoned`) stay outside the index; they are
    retained for idempotency and diagnostics and must not permanently reserve a
    filename that the accepted identity rules allow to be reused.
    """
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS artifact_audit_operations (
            operation_id TEXT PRIMARY KEY,
            artifact_kind TEXT NOT NULL,
            primary_filename TEXT NOT NULL,
            companion_filename TEXT,
            status TEXT NOT NULL,
            audit_action TEXT NOT NULL,
            audit_log_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id),
            CHECK (length(trim(operation_id)) > 0),
            CHECK (length(trim(primary_filename)) > 0),
            CHECK (artifact_kind IN ('report_document', 'json_export', 'manual_backup')),
            CHECK (audit_action IN ('report_document.created', 'export.created', 'backup.created')),
            CHECK (status IN ('prepared', 'pending_audit', 'audited', 'abandoned')),
            CHECK (
                (status = 'audited' AND audit_log_id IS NOT NULL)
                OR (status <> 'audited' AND audit_log_id IS NULL)
            ),
            CHECK (
                artifact_kind <> 'report_document'
                OR (companion_filename IS NOT NULL AND length(trim(companion_filename)) > 0)
            )
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_artifact_audit_operations_active_identity
            ON artifact_audit_operations(artifact_kind, primary_filename)
            WHERE status IN ('prepared', 'pending_audit');

        CREATE INDEX IF NOT EXISTS idx_artifact_audit_operations_kind_status
            ON artifact_audit_operations(artifact_kind, status, created_at, operation_id);
        """
    )
