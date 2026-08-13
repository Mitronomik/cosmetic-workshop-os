# D4 domain-model clarification — Update safety

Status: **NORMATIVE COMPANION TO ADR 0020 WHEN CR-013 IS MERGED**

This file is a bounded clarification of only the update-safety concepts in `docs/domain-model.md`. It does not replace the general domain model.

## Superseded conceptual assumptions

ADR 0020 supersedes these D4-specific interpretations:

- `AppSettings.app_version` is **not** a mutable application-version authority.
- `AppSettings.schema_version` is **not** a second numeric schema authority.
- The automatic `before_migration` backup does not require a new `BackupRecord` database row.
- `UpdateLog.backup_id` does not require a database foreign key for D4; it means the safe generated identity of the retained `before_migration` artifact.
- Durable `UpdateLog` truth lives outside the working database under launcher/startup ownership so it can survive migration failure.
- `rolled_back` is reserved and is not emitted by the selected staged strategy unless a real rollback transition is separately introduced.

## D4 conceptual UpdateLog

Minimum information:

```text
operation_id
from_app_version
to_app_version
from_schema_identity
to_schema_identity
before_migration_backup_identity
started_at
finished_at
status
failure_category
safe_failure_message
```

Statuses used by D4:

```text
started
completed
failed
```

`started` is durable and non-terminal. A repeated launch reconciles it conservatively against the canonical migration lineage. It does not trigger an automatic destructive retry.

## Schema identity

`from_schema_identity` and `to_schema_identity` represent the ordered `schema_migrations` lineage. A UI/log may abbreviate this to last-applied and target migration IDs, but no separately mutable `schema_version` counter is authoritative.

## Backup identity

`before_migration_backup_identity` is a safe generated artifact identity, preferably the generated backup filename. It is not an unrestricted absolute filesystem path and does not require a new `BackupRecord` subsystem.

## Authority

For conflicts limited to D4 update safety, ADR 0020 and this clarification are newer and more specific than the conceptual `AppSettings`, `BackupRecord` and `UpdateLog` field lists in `docs/domain-model.md`. All unrelated domain-model rules remain unchanged.
