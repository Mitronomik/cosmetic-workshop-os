# ADR - Durable file-backed artifact AuditLog semantics

## Status

Status: **Accepted**

Date: **2026-07-30**

Accepted — 2026-07-30. Recorded as `CR-009`.

This ADR closes the product-decision gap formerly called the broad
`C3-II-B — File-backed artifact AuditLog semantics` proposal. It does not
implement runtime behavior. It subdivides the remaining work and authorizes
only the first runtime slice after this documentation pull request merges.

| Slice | Status |
|---|---|
| `C3-II-B1` — durable ledger and report-document AuditLog coverage | `AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED` |
| `C3-II-B2` — JSON export AuditLog coverage | `BLOCKED BY CR-006 — NOT AUTHORIZED` |
| `C3-II-B3` — manual backup AuditLog coverage | `BLOCKED BY CR-004 — NOT AUTHORIZED` |

`C3` remains **incomplete**. `C4` remains
`INACTIVE — NEEDS PRODUCT DECISION`. Product release readiness is not claimed.

> **Current lifecycle pointer — not part of the accepted decision.** The table
> above records the slice authorization as it stood when this ADR was accepted
> on 2026-07-30, and the accepted product decision below is unchanged and is
> not reopened. Since then `C3-II-B1` has been implemented and merged through
> PR #163 — final reviewed head `afd65fd2878fa02a0d4dc4963812c80644a4e787`,
> merge commit `ef0297e41a731f082a2a21a46b361aa9aac36cfa`, merged
> `2026-08-01T05:30:38Z` — and is `DONE — MERGED AND EXACT-HEAD VERIFIED`.
> `C3-II-B2` and `C3-II-B3` are still blocked by `CR-006` and `CR-004`, both of
> which remain `needs evidence`; C3 is still incomplete, C4 is still inactive,
> and product release readiness is still not claimed. Current authority:
> `state/current-focus.md`.

## Context

The scoped operations create durable filesystem artifacts outside SQLite:

- a user-initiated manual SQLite backup;
- a user-initiated JSON export;
- a user-initiated report document.

The current report-document service already treats the Markdown/PDF document
and its metadata JSON file as one artifact unit. If either file cannot be
completed, its existing compensation removes the partial unit. Manual backup
and JSON export each create one file. None of the three current create paths
writes an AuditLog event.

The merged C3-II-A slice demonstrates the correct rule for a pure SQLite
mutation: the business mutation and AuditLog insert share one transaction.
That rule cannot be claimed for a filesystem artifact plus a SQLite row. A
product decision is required for the point where the artifact is complete but
AuditLog persistence fails.

## Scope

This decision covers only user-initiated creation of:

```text
manual SQLite backup
JSON export
report document
```

It does not cover:

```text
startup migration backups
restore
imports
database migrations
packaging
installation
update flow
cloud synchronization
arbitrary filesystem writes
a generic event bus
a generic job queue
a generic outbox for the whole application
```

## Decision

### The artifact is the authoritative primary result

Once a scoped artifact has been fully written and verified according to its
own artifact contract, that artifact is the authoritative primary result.

An AuditLog failure after artifact creation must never cause the application
to:

- delete the created artifact as compensation;
- claim that the artifact does not exist;
- return a total-operation failure while leaving the artifact on disk;
- silently return ordinary success with a permanently missing audit event;
- claim that filesystem creation and SQLite persistence were atomic.

The artifact remains available to the user.

### Result semantics before artifact creation

Before writing the artifact, the application must durably prepare one bounded
artifact-audit operation in SQLite.

If preparation fails:

- do not create the artifact;
- return a structured failure;
- do not create an AuditLog row;
- do not claim partial success.

Accepted generic error code:

```text
artifact_audit_tracking_unavailable
```

Accepted user-facing message:

```text
Не удалось безопасно подготовить создание файла. Файл не создан.
```

A runtime slice may use a more specific artifact noun while preserving this
meaning.

For B1, failure to commit the prepared operation returns HTTP `500` with this
exact safe detail:

```json
{
  "detail": {
    "code": "artifact_audit_tracking_unavailable",
    "message": "Не удалось безопасно подготовить создание документа. Документ не создан.",
    "next_action": "Повторите создание документа. Если ошибка повторяется, перезапустите приложение."
  }
}
```

No document file, metadata file, AuditLog row or prepared ledger row is
committed, and no partial success is claimed. Existing request-validation
errors remain unchanged.

### Artifact creation failure

If the artifact cannot be completed and verified:

- preserve the operation-specific existing error behavior;
- create no success AuditLog event;
- mark or reconcile the prepared operation as `abandoned`;
- never claim that the artifact was created.

For report documents, the document and metadata file remain one artifact unit.
Existing compensation for a document-file or metadata-file creation failure
remains valid and must not be weakened.

### Artifact created and AuditLog recorded

Return the existing HTTP `201 Created` result and the existing successful
artifact response, extended additively with:

```text
audit_status: recorded
audit_message: null
```

The existing primary `message` remains the artifact-result message.

### Artifact created but AuditLog finalization failed

The artifact remains authoritative and available. Return HTTP `201 Created`;
do not return `500` or `409` for the whole operation after the artifact has
been verified.

Return the artifact through the existing response shape plus:

```text
audit_status: pending
audit_message: <non-empty Russian warning>
```

The warning must name the bounded retry triggers: the next normal application
startup and, before creating the next artifact of that same scoped kind. It
must not imply an immediate, periodic or background retry. The exact B1
warning is:

```text
Документ создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего документа.
```

Later B2/B3 warnings use their artifact-specific noun and name those same two
bounded triggers. They must not say that artifact creation failed.

The frontend presents:

- success for the created artifact;
- a separate warning that Journal recording is pending;
- no false failure;
- no duplicate create request;
- no raw technical path or AuditLog metadata.

### Bounded durable operation ledger

One narrowly scoped SQLite table is authorized for only the three operations
in this ADR. Preferred name:

```text
artifact_audit_operations
```

It is not a generic event bus, generic outbox, generic task queue or general
workflow engine. The migration number is deferred to the runtime slice and
must be the next sequential migration after inspecting merged `main`.

The stable unique `operation_id` is the primary idempotency identity.

For B1, the conceptual schema and column constraints are:

```text
operation_id TEXT PRIMARY KEY
artifact_kind TEXT NOT NULL
primary_filename TEXT NOT NULL
companion_filename TEXT
status TEXT NOT NULL
audit_action TEXT NOT NULL
audit_log_id INTEGER
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
```

Allowed statuses:

```text
prepared
pending_audit
audited
abandoned
```

Ledger rules:

- `operation_id` is an opaque backend-generated canonical lowercase UUID
  string; it is never user-supplied or exposed through the Journal read API;
- a status `CHECK` permits only `prepared`, `pending_audit`, `audited` and
  `abandoned`;
- `audit_log_id` is nullable and references `audit_logs.id`;
- B1 creates only `artifact_kind = report_document` with
  `audit_action = report_document.created`; `json_export` and `manual_backup`
  are reserved future kinds and are not implemented by B1;
- `primary_filename` and nullable `companion_filename` are internal safe
  relative filenames required for deterministic reconciliation, never
  unrestricted absolute paths;
- both filename fields are validated on write and again on reconciliation
  read; empty names, absolute paths, directory separators, `..`, NUL and
  control characters are rejected;
- `companion_filename` is nullable at table level; every B1 report-document
  operation records its metadata filename there;
- one active operation may own one exact
  `(artifact_kind, primary_filename)` identity; a second active operation must
  not reconcile or audit that same artifact identity; here active means
  `prepared` or `pending_audit`;
- report-document filenames contain no request reason;
- future B2/B3 `primary_filename` values may contain the canonical
  filename-derived reason segment already accepted by CR-005;
- there is no separate `reason` column and no raw human reason, request reason,
  export-manifest reason or other separate user-authored text is stored;
- CR-005 filename behavior is not reopened;
- no artifact, export or report content is stored;
- no Workshop-profile value is stored;
- no phone number, email address, address or note is stored;
- the ledger is internal and is not a user-facing history viewer;
- audited and abandoned rows are retained for MVP idempotency and diagnostic
  safety;
- no cleanup policy is authorized by this decision.

Ledger filenames are never copied into AuditLog summary or metadata and are
never exposed through `GET /api/audit-logs`. Existing artifacts are not
renamed or rewritten.

### Required operation sequence

Every scoped create operation follows:

```text
validate and canonicalize request
→ reserve the final safe artifact identity
→ insert one prepared ledger row
→ commit the prepared row
→ create the artifact outside SQLite
→ verify the artifact according to its artifact contract
→ finalize AuditLog and ledger state in one SQLite transaction
```

For B1, the existing repository contract receives one bounded compatible
extension:

```text
AuditLogRepository.create_log(...) -> int
```

It returns the inserted AuditLog row ID from `cursor.lastrowid`, preserves the
existing parameters and optional caller-owned connection, and permits existing
callers to ignore the returned integer. B1 must not add a second AuditLog
insertion API, bypass `AuditLogRepository`, or change existing call-site
behavior.

The B1 finalizer uses one caller-owned SQLite connection and a
write-serialized transaction:

```text
BEGIN IMMEDIATE or an architecture-equivalent explicitly tested SQLite write lock
→ read operation by operation_id
→ if status = audited, return the existing audit_log_id without inserting
→ if status not in (prepared, pending_audit), do not insert
→ insert exactly one report_document.created AuditLog row
→ receive its row ID
→ update the ledger to audited with that audit_log_id
→ commit both
```

If finalization fails:

```text
artifact remains
→ ledger remains prepared or pending_audit
→ API returns 201 with audit_status=pending
→ no compensation delete
```

Do not open a second independent SQLite connection while the finalization
transaction is active. If the AuditLog insert or ledger update fails, both are
rolled back. No generic transaction framework is authorized.

### Reconciliation contract

Reconciliation is local, bounded and deterministic. It runs:

1. after database initialization and migrations during normal application
   startup;
2. before creating another artifact of a CR-009 scoped kind.

Ordinary GET/list/status endpoints do not mutate reconciliation state.

Do not add:

- a permanent background thread;
- a cloud worker;
- a timer daemon;
- a webhook;
- a network dependency;
- a user-visible terminal command;
- automatic unbounded retry.

For one `prepared` or `pending_audit` operation:

- resolve only the expected safe directory for its recorded `artifact_kind`;
- inspect only its recorded safe relative filenames;
- never scan arbitrary directories;
- never reconstruct operations from unrelated legacy filenames;
- never audit an artifact merely because a similarly named file exists;
- verify the complete artifact unit;
- if the artifact is valid, finalize idempotently;
- if it is definitely absent because creation failed, mark the operation
  `abandoned`;
- if the artifact state is ambiguous or unsafe, leave it pending and surface a
  warning rather than guessing.

For report documents, both the primary Markdown/PDF file and the metadata JSON
file must pass this complete verification before finalization or
reconciliation:

1. `primary_filename` and `companion_filename` pass safe-name validation;
2. both resolve inside the configured report-documents directory;
3. both exist and are regular files;
4. metadata JSON parses as the existing `ReportDocumentMetadata`;
5. metadata `filename` equals ledger `primary_filename`;
6. metadata `metadata_filename` equals ledger `companion_filename`;
7. metadata `document_type` is exactly `workshop_overview`;
8. metadata format is one of the currently supported generated formats;
9. the primary extension matches metadata format;
10. metadata ID agrees with the generated filename contract;
11. metadata `size_bytes` equals the current primary-file byte size;
12. the existing safe-path rules remain satisfied.

Verification does not rerender document content or compare it with current
report data, and it never rewrites the document or metadata file. If the pair
is definitely absent because creation failed, the operation becomes
`abandoned`. If it is mismatched, malformed, unsafe or ambiguous, do not audit
or delete it: leave it `prepared` or `pending_audit`, include it in
`pending_audit_count`, and surface the pending warning.

Startup reconciliation runs after successful database initialization and
migrations, is bounded to unresolved report-document operations, and completes
before the ordinary UI is served. Failure to finalize one pending event leaves
that operation unresolved, does not delete or rewrite the artifact, and does
not make the whole application unusable; startup completes with the pending
count/warning. This recovery behavior must not hide an independent migration
or database-initialization failure.

Pre-create reconciliation runs once before preparing the next report-document
operation. Failure to finalize an older valid artifact does not turn that
artifact into a failure. A new create may continue only if its new ledger
preparation can be committed safely; otherwise the new document is not
created and the exact B1 HTTP `500` contract applies. There is no loop or
unbounded retry.

For B1, `pending_audit_count` is the number of ledger rows satisfying:

```text
artifact_kind = report_document
status IN (prepared, pending_audit)
```

It excludes `audited` and `abandoned`. `GET
/api/report-documents/status` reads this count but performs no reconciliation.
A definitely absent incomplete artifact becomes `abandoned` and is no longer
counted; an ambiguous, unsafe or not-yet-finalized operation remains
unresolved and counted. The frontend presents the count only as a
pending-Journal warning, never as failed document creation.

### Duplicate-event protection

Exactly one AuditLog row may exist for one `operation_id`. Protection comes
from:

- the unique ledger `operation_id`;
- status checks inside the finalization transaction;
- `audit_log_id` stored with the audited operation;
- an idempotent finalizer;
- startup and pre-create reconciliation using that same finalizer.

Do not depend on filename uniqueness alone, filesystem scan order, raw
timestamp matching, reason text, frontend request deduplication alone,
reconstructing history from filenames, or deleting duplicate AuditLog rows
afterward.

The finalization transaction must either:

```text
insert AuditLog + mark operation audited
```

or commit neither.

B1 runtime tests must prove that sequential repeated finalization creates one
row; startup plus pre-create repeated finalization creates one row; two
concurrent finalizer attempts create exactly one row and one caller receives or
resolves the already-audited result; AuditLog insert failure leaves the
operation unresolved; and ledger-update failure rolls back the AuditLog
insert.

### Audit privacy and vocabulary

#### Report document

```text
action: report_document.created
entity_type: report_document
entity_id: operation_id
actor_type: user
persisted summary: Report document created
action_label: Документ отчёта создан
entity_label: Документ отчёта
display_summary: Документ отчёта создан
```

Allowed metadata keys:

```text
operation_id
document_type
format
reconciled_after_failure
```

#### JSON export

```text
action: export.created
entity_type: export_file
entity_id: operation_id
actor_type: user
persisted summary: JSON export created
action_label: Экспорт создан
entity_label: Экспорт
display_summary: Экспорт создан
```

Allowed metadata keys:

```text
operation_id
export_schema_version
reconciled_after_failure
```

#### Manual backup

```text
action: backup.created
entity_type: backup_file
entity_id: operation_id
actor_type: user
persisted summary: Backup created
action_label: Резервная копия создана
entity_label: Резервная копия
display_summary: Резервная копия создана
```

Allowed metadata keys:

```text
operation_id
reconciled_after_failure
```

For all three events, never persist or expose through AuditLog metadata or
summaries:

- absolute or relative path;
- filename;
- artifact reason;
- Workshop profile;
- report, export or database contents;
- entity counts;
- client information;
- phone, email or address;
- request or response payload;
- arbitrary user-authored text.

`reconciled_after_failure` is a boolean only.

The existing C3-I read API remains the only Journal read surface and continues
to exclude raw summary, metadata and entity ID. The three new actions are not
added to the suffix allowlist.

### Legacy and startup behavior

Existing backup, export and report-document files are not backfilled into the
ledger and do not generate historical AuditLog rows. Do not scan old files and
invent events, rewrite or rename old artifacts, modify existing report
documents, modify export manifests, or modify backup files.

The automatic `before_migration` startup backup is outside CR-009:

- it is not a manual user action;
- CR-009 runtime slices do not audit it;
- it continues to occur before a database migration;
- it must not depend on a ledger table that may not exist until after
  migration.

CR-009 does not reopen or resolve `CR-004`.

## Runtime subdivision

### C3-II-B1 - Durable ledger and report-document AuditLog coverage

Status after this documentation pull request merges:

```text
AUTHORIZED — NOT IMPLEMENTED
```

Scope:

- the next sequential migration for `artifact_audit_operations`;
- a bounded ledger repository/domain service;
- startup reconciliation after migrations;
- pre-create reconciliation for report documents;
- integration with report-document creation only;
- `report_document.created`;
- additive report-document create response fields `audit_status` and
  `audit_message`;
- additive report-document status field `pending_audit_count`;
- frontend success-plus-warning presentation;
- backend tests, frontend tests and focused exact-head smoke.

This slice is first because report documents have no active `needs evidence`
change request, their document-plus-metadata artifact boundary already exists,
and backup and export retain separate unresolved evidence gates.

### C3-II-B2 - JSON export AuditLog coverage

Status:

```text
BLOCKED BY CR-006 — NOT AUTHORIZED
```

It may reuse the accepted ledger only after `CR-006` determines export
create-response fallback reachability and accepted confirmation semantics.
This ADR neither resolves nor implements `CR-006`.

### C3-II-B3 - Manual backup AuditLog coverage

Status:

```text
BLOCKED BY CR-004 — NOT AUTHORIZED
```

It may reuse the accepted ledger only after `CR-004` determines SQLite backup
consistency behavior. This ADR neither resolves nor implements `CR-004`.

## Considered alternatives

### Delete the artifact when AuditLog fails

Rejected. A fully verified artifact is the primary result. Deleting it would
discard user data and can itself fail.

### Return total failure while keeping the artifact

Rejected. It would invite a duplicate create request and falsely claim that
the primary result failed.

### Return ordinary success and omit the event

Rejected. It silently leaves a permanent AuditLog gap.

### Claim filesystem and SQLite atomicity

Rejected. The local filesystem operation and SQLite transaction do not share a
real cross-resource transaction.

### Reconstruct events by scanning filenames

Rejected. It is ambiguous, privacy-unsafe and cannot provide the accepted
idempotency identity.

### Add a generic outbox or job system

Rejected for this scope. The MVP needs one bounded local ledger owned only by
the three named artifact operations.

## Consequences

- A later runtime slice must reserve and persist an operation before creating
  the artifact.
- An audit-finalization failure becomes truthful HTTP `201` partial success,
  not false total failure.
- Reconciliation is deterministic at startup and before the next scoped
  create; it is not a background service.
- Exactly-once AuditLog finalization is tied to `operation_id`, not filenames.
- The internal ledger intentionally retains completed and abandoned rows for
  the MVP.
- Existing artifacts and the startup migration-backup order remain unchanged.
- Only `C3-II-B1` is authorized after this documentation pull request merges.
- `C3-II-B2`, `C3-II-B3`, C4, Restore, packaging, installation, update and
  release-candidate smoke remain unauthorized.

## Verification boundary

This ADR is documentation only. It authorizes no migration, repository,
service, schema, API, frontend, test, dependency or generated-file change in
the decision pull request. Runtime verification belongs to the later B1 slice.
