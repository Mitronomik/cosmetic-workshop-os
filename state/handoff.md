# Handoff

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted CR-011 architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
C4-II-A slice plan: `docs/c4-ii-a-implementation-slices.md`.

## Current lifecycle

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Last merged authorization

PR #173:

```text
reviewed head — 9f5722c5dec695588596d45daa5588092ce7f080
merge commit — aaedf2735660fb92eb627f7eeab327437d459b56
```

The current A1 branch starts from that exact merge.

## Current work — A1 validation-session core

Implemented:

- `RestoreCandidatePreparationService.prepare_restore_candidate(...)`;
- private system-temp validation run/session scratch;
- launcher UUID4 ownership/version markers and restrictive permissions;
- C4-I source intake + held descriptor + sidecar checks;
- C4-I two-pass stable staging;
- read-only C4-I candidate validation;
- source identity/digest re-proof before retained proof;
- typed presentation-safe state;
- generation/cancel/reselection invalidation;
- launcher-private source path + `SourceIdentity` + full SHA-256 proof;
- cleanup after success/rejection/cancel/failure and recognized prior-run scratch;
- targeted tests and exact-head service smoke runner.

Successful A1 validation deletes the staged temporary candidate. The retained
proof is memory-only and is not destructive authority. Future C4-II-B must still
reopen/re-prove/restage/revalidate.

## Safety boundary

A1 creates no durable Restore operation or phase, no `before_restore` safety copy,
no working-DB replacement/migration, no rollback/recovery mutation and no Restore
AuditLog event. It does not call `execute_restore(...)` and does not stop the
ordinary backend.

A1 also contains no A2/A3/A4 scope:

- no HTTP control plane / Host / Origin / CORS / bootstrap / token / `command_seq`;
- no `/usr/bin/osascript` picker;
- no browser source-path/file authority;
- no `/backups/restore` frontend route;
- no production browser bootstrap fragment.

## Required exact-head verification

Still pending on the final published A1 head:

```text
git status --short
→ git diff --check
→ python3 scripts/check_documentation_lifecycle.py
→ python3 -m pytest launcher/tests/test_restore_validation_session.py
→ existing C4-I Restore regression tests
→ python3 -m pytest backend/app/tests launcher/tests
→ python3 scripts/smoke_restore_validation_session.py --expected-head <HEAD>
→ clean status after smoke
→ independent exact-head audit
```

Do not claim PASS unless actually run. Merge only with P0=0 / P1=0 / P2=0.

## Next after A1 merge

Do not start A2 immediately from this branch. Update `main`, close A1 lifecycle
with reviewed head/merge evidence, then create a fresh A2 branch only after its
gate is explicitly opened. A3/A4 remain blocked and C4-II-B remains not
authorized.
