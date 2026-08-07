# Current Focus — PR #173 C4-II-A authorization and slicing

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 decision: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Current Restore profile: `docs/restore-interaction-and-validation-session.md`.
C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.
Current ledger: `state/change-requests.md`.
Searchable history: `docs/history/README.md`.

## Baseline

PR #172 / CR-011 is merged.

```text
PR #172 reviewed head — c51d5baa07e4cd8912b1973649c22b20f581e3d2
PR #172 merge commit — 998596560db6780a677bdec363d1fd19db30c1b6
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
```

## Current lifecycle

```text
PR #172 — MERGED — CR-011 ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED
C4-II-A1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

This authorization is normative only after PR #173 merges. PR #173 itself is
documentation/lifecycle only.

## Current task — PR #173

Authorize the already-decided C4-II-A architecture as four bounded implementation
slices and make A1 the only immediate runtime successor.

```text
A1 validation-session core
→ A2 exact-run launcher control plane
→ A3 native macOS picker integration
→ A4 browser /backups/restore + end-to-end non-destructive flow
```

A2–A4 remain blocked by predecessor merge + exact-head gate.

## Immediate successor after PR #173 merge

Only:

`C4-II-A1 — Validation-session core`.

A1 may implement:

- launcher-owned `prepare_restore_candidate(...)`-equivalent;
- isolated user-only validation scratch;
- shared-safe reuse/refactor of C4-I source intake/staging/validation;
- selection generation / stale / cancel / invalidation semantics;
- typed presentation-safe result model;
- launcher-private source path + `SourceIdentity` + SHA-256 retained proof;
- bounded owned-only cleanup;
- tests and service-level exact-head smoke.

A1 may **not** implement:

- HTTP control plane;
- browser bootstrap/session tokens or `command_seq`;
- native picker;
- frontend Restore route/UI;
- destructive confirmation or `execute_restore(...)`;
- durable Restore operation/phase;
- `before_restore` safety copy;
- working-DB replacement/migration;
- rollback/recovery mutation;
- Restore AuditLog;
- new dependency or packaging implementation.

## PR #173 restrictions

Do not modify runtime or tests in this authorization branch:

- `backend/`;
- `frontend/`;
- `launcher/`;
- dependency/lock files;
- migrations;
- workflows;
- packaging/updater implementation.

Do not start A1 from this unmerged branch.

## Required checks before PR #173 merge

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also verify docs/state/checker-only diff, run any repository-defined docs/link
checker if present, and perform fresh independent exact-head authorization audit.
P0=0, P1=0, P2=0 before merge.

Product smoke is not applicable because PR #173 changes no runtime behavior.

## After PR #173 merges

Update `main`, create a fresh A1 branch from merged `main`, and implement only the
A1 scope. Do not create A2 until A1 is reviewed, exact-head tested and merged.
C4-II-B remains separately not authorized.
