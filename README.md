# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The product goal is a
packaged application a non-technical user can run without GitHub, Git, Python,
Node.js, Docker or a terminal.

## Current product status

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

PR #173 reviewed head `9f5722c5dec695588596d45daa5588092ce7f080`
merged as `aaedf2735660fb92eb627f7eeab327437d459b56`.

The current A1 changeset starts from that merged baseline and implements only the
launcher-owned **non-destructive validation-session core**. It does not implement
HTTP control, browser session/bootstrap, native picker, frontend Restore UI or
destructive Restore.

## Current A1 boundary

Implemented in the current changeset:

- `RestoreCandidatePreparationService` / `prepare_restore_candidate(...)`;
- system-temp validation scratch under
  `<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/`;
- user-only scratch permissions and ownership-marker cleanup;
- direct reuse of C4-I `open_selected_source(...)`, held-descriptor staging and
  `validate_staged_candidate(...)`;
- typed presentation-safe accepted/rejected/cancelled/technical-failure results;
- generation/cancel/reselection invalidation;
- launcher-private retained source path + `SourceIdentity` + full SHA-256 proof;
- removal of staged validation scratch before accepted proof publication;
- automated A1 tests and an exact-head service-level smoke runner.

Explicitly absent:

- no `execute_restore(...)` call;
- no durable Restore operation or phase;
- no `before_restore` safety copy;
- no working-database replacement/migration;
- no rollback/startup-recovery mutation;
- no Restore AuditLog write;
- no HTTP control plane / `command_seq`;
- no `/usr/bin/osascript` picker integration;
- no `/backups/restore` frontend route or browser bootstrap handoff;
- no new runtime dependency or packaging implementation.

A2 remains blocked until A1 is independently reviewed, exact-head tested and
smoked, merged, and lifecycle/project memory is closed from updated `main`.

## Restore authority

Authority remains intentionally split:

- ADR 0016 — durable destructive Restore safety/state machine;
- ADR 0017 — C4-I lifecycle closure/history;
- ADR 0018 — interaction/control/picker/validation-session architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation plan;
- `docs/current-lifecycle.md` — current implementation authorization/status.

A1 does not amend ADR 0016 or ADR 0018. C4-II-B destructive confirmation and
execution remains **NOT AUTHORIZED**.

## C4-II-A sequence

```text
A1 — validation-session core                     ← current changeset
→ A2 — exact-run launcher control plane          ← blocked
→ A3 — native macOS picker integration           ← blocked
→ A4 — browser /backups/restore + E2E UX         ← blocked
```

Each later slice starts from updated `main` only after its predecessor merge,
exact-head gate and lifecycle update.

## Current verification gate

Before the A1 changeset can be considered complete:

```text
git diff --check
→ documentation lifecycle checker
→ targeted A1 tests
→ existing C4-I Restore regression tests
→ full backend + launcher regression suite
→ exact-head A1 service-level smoke
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

Do not claim A1 `DONE` or start A2 before that gate closes.

## Current authority map

1. [`docs/current-lifecycle.md`](docs/current-lifecycle.md)
2. applicable accepted ADR
3. [`docs/c4-ii-a-implementation-slices.md`](docs/c4-ii-a-implementation-slices.md)
4. [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
5. [`docs/implementation-plan.md`](docs/implementation-plan.md)
6. active [`state/`](state/) files

Searchable history remains under [`docs/history/`](docs/history/README.md). The
five protected pre-compaction snapshots must remain byte-identical.

## Architectural invariants

Every change must preserve local-first operation, user data outside code/package,
API-first business architecture, safe historical data, recipe versions,
first-class client recipes, lot/movement inventory, transactional production,
safe import preview/confirmation, backup-before-migration and a human-readable
non-technical UI.

Restore additionally preserves launcher ownership of filesystem/destructive
authority, immutable selected source, no browser absolute-path authority and no
destructive action before separately authorized C4-II-B.
