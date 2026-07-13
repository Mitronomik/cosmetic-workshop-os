# Current focus

Slice A1b2 is active: clean up Backup and Export user-facing capability copy only.

## Runtime scope
- `/backups`
- `/exports`
- `dashboardBackupReminder()`

## Exact non-goals
- Do not change Reports, Help Center, route/navigation readiness metadata, Import, Demo Data, Settings, or other application sections.
- Do not implement restore, import from export, CSV/XLSX/PDF export, cloud upload/sync, scheduled backups/exports, file browser, Finder integration, path redesign, or download/copy-path controls.
- Do not change backend files, API fields, DTOs, endpoints, folder locations, filenames, request counts, disabled rules, state transitions, CSS, dependencies, or lockfiles.
- Do not change `docs/implementation-plan.md`.
- Do not assign or predict a future pull request number.

## Source checks
- Start from the actual latest available main baseline; PR #110 merge commit `f157814358b1a461f6f63d54d46ad2dd6f3a7145` must be included.
- Inspect `loadBackups`, `submitBackupCreate`, `loadExports`, `submitExportCreate`, `dashboardBackupReminder`, and all `/backups` and `/exports` render functions before editing.
- Preserve dynamic filenames and raw path values exactly as returned by the application; only surrounding static labels may change.
- Classify remaining technical-copy search hits as in-scope, identifiers, dynamic values/messages, out-of-scope, or deferred A1b3/A5 findings.

## Build and backend baseline
- Run repository hygiene checks, `git diff --check`, frontend build, and backend pytest.
- Backend pytest result must be reported honestly against the known previous baseline of 463 passed / 5 failed without fixing unrelated backend failures.

## GitHub review gate
- Publish a focused branch named `codex/a1b2-backup-export-copy` if remote access is available.
- Create a GitHub PR only after committing changes; do not mention Hermes or any external audit system.
