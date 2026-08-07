# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-07`

Historical pre-compaction plan remains byte-identical at
`docs/history/implementation-plan/2026-08-06-pre-compaction.md`.

## 1. Source of truth

1. applicable `AGENTS.md`;
2. newest accepted ADR for the exact topic;
3. `docs/current-lifecycle.md`;
4. unsuperseded durable ADR semantics;
5. `docs/restore-interaction-and-validation-session.md`;
6. `docs/c4-ii-a-implementation-slices.md`;
7. this plan;
8. active `state/` files;
9. `docs/history/` evidence.

## 2. Merged baseline

```text
PR #170 / C4-I merge — e6997281d2e0268ce54184d988c114bac71c35e2
PR #171 merge — 76ab59216047222714a32f2793a789b3dc8df19a
PR #172 / CR-011 merge — 998596560db6780a677bdec363d1fd19db30c1b6
PR #173 / sliced authorization merge — aaedf2735660fb92eb627f7eeab327437d459b56
```

PR #173 final reviewed head:
`9f5722c5dec695588596d45daa5588092ce7f080`.

The current A1 branch was created from exact merged PR #173 main.

## 3. Current lifecycle

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

## 4. Current implementation window — C4-II-A1

Goal: implement the launcher-owned non-destructive candidate-preparation boundary
without any A2/A3/A4 or C4-II-B scope.

Implemented in the current changeset:

- `launcher/restore/validation_session.py`:
  - `RestoreCandidatePreparationService`;
  - `prepare_restore_candidate(...)`;
  - typed accepted/rejected/cancelled/technical-failure result;
  - generation/cancel/reselection invalidation;
  - launcher-private retained `SourceIdentity` + SHA-256 proof.
- `launcher/restore/validation_scratch.py`:
  - system-temp run/session namespace;
  - UUID4-only launcher names;
  - user-only permissions;
  - ownership/version markers;
  - owned-only current/interrupted cleanup.
- direct reuse of existing C4-I:
  - `open_selected_source(...)`;
  - `HeldSource.revalidate()` / `digest()` / sidecar proof;
  - `stage_source(...)` two-pass stable staging;
  - `validate_staged_candidate(...)` read-only validation.
- targeted A1 tests in `launcher/tests/test_restore_validation_session.py`.
- exact-head service smoke in `scripts/smoke_restore_validation_session.py`.

The implementation deliberately uses the existing C4-I staging algorithm instead
of creating a second weaker copy/validation path.

## 5. A1 non-goals / forbidden scope

A1 does not authorize and must not contain:

- HTTP control plane, Host/Origin/CORS/bootstrap/session protocol;
- `command_seq` or control-plane replay ledger;
- real native picker or `/usr/bin/osascript` invocation;
- frontend Restore route/UI or production browser bootstrap fragment;
- ordinary FastAPI Restore endpoint;
- `execute_restore(...)` invocation;
- durable Restore operation/phase creation;
- `before_restore` safety copy;
- working database replacement/migration;
- rollback/startup-recovery mutation;
- Restore AuditLog write;
- new application dependency;
- packaging implementation.

The ordinary backend is not stopped by A1 candidate validation.

## 6. A1 safety contract

For one source selection A1 must:

```text
new generation + clear old proof
→ create private validation scratch session
→ C4-I open_selected_source / held descriptor
→ C4-I stable two-pass staging into temporary candidate
→ re-prove source identity/self-containment/digest
→ C4-I read-only validate_staged_candidate
→ re-prove source again
→ delete temporary candidate/session scratch
→ if generation is still current, retain launcher-private path + SourceIdentity + SHA-256
→ return presentation-safe typed result
```

Any rejection, cancellation, technical failure, reselection, invalidation or
service close clears retained proof. A late/stale generation cannot become new
source authority.

Scratch is not durable Restore state and lives under:

`<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/`.

## 7. Required A1 tests

Must prove at least:

1. current-schema source accepted;
2. supported older schema accepted without migrating source/working DB;
3. newer/foreign/empty/corrupt/directory/symlink/sidecar/working-DB classes reject;
4. selected source remains byte-identical in normal validation;
5. working database remains unchanged;
6. no durable Restore operation/phase exists;
7. no `before_restore` safety copy is created;
8. no Restore AuditLog row is written;
9. stale/cancelled generation cannot retain proof;
10. reselection clears previous proof before new staging;
11. technical failures expose fixed safe text only;
12. scratch uses restrictive permissions and cleanup is owned-only;
13. existing C4-I Restore tests remain green.

## 8. Exact-head verification gate

Run on the exact published A1 head:

```text
git status --short
→ git diff --check <A1-base>...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ python3 -m pytest launcher/tests/test_restore_validation_session.py
→ C4-I Restore regression tests
→ python3 -m pytest backend/app/tests launcher/tests
→ python3 scripts/smoke_restore_validation_session.py --expected-head <HEAD>
→ verify clean status again
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

The smoke must use real temporary SQLite sources and the real candidate-preparation
service/C4-I staging/validation; synthetic final-result injection is insufficient.

## 9. Successor gates

A2 remains blocked until A1 passes the gate, merges, and lifecycle/project memory
is updated from merged `main`.

A2 then owns only exact-run loopback control/session protocol and uses the accepted
`picker_unavailable` production seam until A3. A3 owns the real macOS picker. A4
owns the first production browser bootstrap-fragment handoff and `/backups/restore`.

C4-II-B destructive confirmation/execution remains separately not authorized.

## 10. Current next action

```text
Finish A1 implementation review
→ publish draft PR
→ run exact-head tests + smoke in clean checkout
→ resolve every P0/P1/P2 finding
→ merge only after evidence is complete
→ close A1 lifecycle from updated main before starting A2
```
