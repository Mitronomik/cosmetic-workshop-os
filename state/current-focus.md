# Current Focus — C4-II-A1 validation-session core

Updated: `2026-08-07`

Current lifecycle authority: `docs/current-lifecycle.md`.
Accepted architecture: `docs/decisions/0018-launcher-restore-interaction-and-validation-session.md`.
Slice plan: `docs/c4-ii-a-implementation-slices.md`.

## Baseline

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
PR #173 reviewed head — 9f5722c5dec695588596d45daa5588092ce7f080
PR #173 merge commit — aaedf2735660fb92eb627f7eeab327437d459b56
```

Current A1 branch starts from that merge commit.

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

## Current task

Finish and verify **C4-II-A1 — Validation-session core** only.

Implemented on the current branch:

- launcher-owned `RestoreCandidatePreparationService`;
- `prepare_restore_candidate(...)` non-destructive boundary;
- system-temp validation scratch with UUID4 run/session ownership markers and
  restrictive user-only permissions;
- direct reuse of C4-I `open_selected_source(...)`, `stage_source(...)` and
  `validate_staged_candidate(...)`;
- source identity + digest re-proof after staging and after candidate validation;
- generation/cancel/reselection invalidation;
- typed presentation-safe result;
- launcher-private retained path + `SourceIdentity` + full SHA-256 proof;
- cleanup of staged candidate before accepted proof publication;
- recognized previous-run scratch cleanup primitive;
- targeted tests and exact-head A1 smoke runner.

## Hard scope boundary

Do not implement in A1:

- control-plane HTTP / Host / Origin / CORS / bootstrap / session token;
- `command_seq`;
- `/usr/bin/osascript` picker;
- frontend `/backups/restore`;
- browser source path/file authority;
- `execute_restore(...)`;
- durable Restore operation/phase;
- `before_restore` safety copy;
- working-DB replacement/migration;
- rollback/recovery mutation;
- Restore AuditLog;
- packaging or dependencies.

C4-I `engine.py`, destructive state machine, replacement and safety-copy semantics
remain unchanged.

## Verification still required

No PASS is claimed until run on the exact published head:

```text
git diff --check
python3 scripts/check_documentation_lifecycle.py
python3 -m pytest launcher/tests/test_restore_validation_session.py
existing C4-I Restore tests
python3 -m pytest backend/app/tests launcher/tests
python3 scripts/smoke_restore_validation_session.py --expected-head <HEAD>
independent exact-head audit
```

Gate: P0=0 / P1=0 / P2=0.

## Next

A2 remains blocked. After A1 merges, update `main`, close A1 lifecycle/project
memory and only then create a fresh A2 branch. C4-II-B remains separately not
authorized.
