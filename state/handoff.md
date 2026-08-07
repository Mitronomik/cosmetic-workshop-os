# Handoff

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 decision: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Current Restore profile: `docs/restore-interaction-and-validation-session.md`.
C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.
Current ledger: `state/change-requests.md`.
Searchable history: `docs/history/README.md`.

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

This authorization becomes normative only after PR #173 merges.

## Last merged work — PR #172

CR-011 is accepted on `main`.

```text
reviewed head — c51d5baa07e4cd8912b1973649c22b20f581e3d2
merge commit — 998596560db6780a677bdec363d1fd19db30c1b6
```

ADR 0018 selects the launcher-owned authenticated loopback control plane,
launcher-owned `/usr/bin/osascript` picker, exact-run browser control session and
launcher-owned non-destructive validation boundary.

## Current work — PR #173

PR #173 is a documentation/lifecycle authorization task. It does not implement
runtime behavior.

It authorizes C4-II-A only as:

```text
A1 validation-session core
→ A2 exact-run launcher control plane
→ A3 native macOS picker integration
→ A4 browser /backups/restore + end-to-end non-destructive flow
```

Only A1 may begin after PR #173 merges. Each later slice requires its predecessor
to be independently reviewed, exact-head tested and merged first.

## A1 immediate scope after merge

A1 owns only:

- `prepare_restore_candidate(...)`-equivalent launcher service;
- isolated user-only validation scratch;
- reuse/shared-safe refactor of C4-I source intake/staging/validation;
- selection generation / stale / cancel / invalidation semantics;
- typed safe result;
- launcher-private source path + C4-I `SourceIdentity` + full SHA-256 proof;
- owned-only cleanup and recognized interrupted-scratch cleanup;
- tests and launcher/service-level exact-head smoke.

A1 explicitly excludes control-plane HTTP, browser tokens/bootstrap, `command_seq`,
native picker, frontend Restore UI, destructive confirmation/execution,
`before_restore` safety copy, working-DB replacement/migration, rollback/recovery,
Restore AuditLog, new dependencies and packaging implementation.

## A2/A3/A4 gates

- A2: blocked until A1 is merged and exact-head verified.
- A3: blocked until A2 is merged and exact-head verified.
- A4: blocked until A3 is merged and exact-head verified.

Every later slice starts from updated `main`, never from an unmerged predecessor
branch.

## C4-II-B boundary

C4-II-B remains not authorized.

No C4-II-A slice may call `execute_restore(...)` or create destructive authority.
Future C4-II-B must re-prove source identity + SHA-256, re-check sidecars,
re-stage/revalidate, prove backend exclusion, create mandatory `before_restore`
safety copy, and only then enter the existing C4-I destructive execution path.

## PR #173 restrictions

Do not modify runtime/tests/dependencies/migrations/workflows in PR #173.
Do not implement A1 on the unmerged authorization branch.

## Required PR #173 checks

```bash
git diff --check
python3 scripts/check_documentation_lifecycle.py
```

Also verify docs/state/checker-only diff, run any repository-defined docs/link
checker, and perform fresh exact-head read-only authorization audit. Merge only at
P0=0, P1=0, P2=0.

Product smoke is not applicable to PR #173.

## Next after PR #173 merge

Update `main`, create a fresh A1 branch from merged `main`, and implement only
C4-II-A1. Do not begin A2 or C4-II-B.
