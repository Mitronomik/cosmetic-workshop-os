# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-07`

This document is the compact authority for current implementation lifecycle,
authorization and PR sequencing. It does not replace durable product, safety or
architecture contracts.

## Authority order

Resolve conflicts by scope and recency:

1. applicable `AGENTS.md`;
2. newest accepted ADR for the exact topic;
3. this file for lifecycle/authorization;
4. unsuperseded durable ADR semantics;
5. `docs/restore-interaction-and-validation-session.md`;
6. `docs/c4-ii-a-implementation-slices.md`;
7. `docs/implementation-plan.md`;
8. active `state/` files;
9. strategic references;
10. `docs/history/` evidence.

For Restore, ADR 0016 remains authoritative for the destructive twelve-phase
safety state machine and ADR 0018 remains authoritative for the selected
launcher-owned interaction/control/picker/validation architecture. The A1
implementation changeset does not amend either ADR and does not authorize C4-II-B.

## Current lifecycle

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
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
C4 — ACTIVE
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

`C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED` means runtime and
tests exist on the active A1 implementation branch, but the slice is not `DONE`
until exact-head tests/smoke/audit pass, the PR is merged, and lifecycle is updated
from merged `main`. A2 cannot start merely because A1 code exists.

## Verified merge baselines

### C4-I / PR #170

- reviewed head: `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`
- merge: `e6997281d2e0268ce54184d988c114bac71c35e2`

### Project-memory closure / PR #171

- reviewed head: `4978aa9a7c05117011eae1bc00276d5f98378d9b`
- merge: `76ab59216047222714a32f2793a789b3dc8df19a`

### CR-011 / PR #172

- reviewed head: `c51d5baa07e4cd8912b1973649c22b20f581e3d2`
- merge: `998596560db6780a677bdec363d1fd19db30c1b6`
- architecture gate: P0=0 / P1=0 / P2=0

### C4-II-A authorization / PR #173

- reviewed head: `9f5722c5dec695588596d45daa5588092ce7f080`
- merge commit: `aaedf2735660fb92eb627f7eeab327437d459b56`
- merged at: `2026-08-07T15:43:49Z`
- exact-head documentation/authorization gate: PASS
- authorization audit: P0=0 / P1=0 / P2=0

The current A1 branch was created directly from merge commit
`aaedf2735660fb92eb627f7eeab327437d459b56`.

## A1 implemented boundary

The current changeset implements only the non-destructive validation-session core:

- `launcher/restore/validation_session.py` —
  `RestoreCandidatePreparationService` and `prepare_restore_candidate(...)`;
- `launcher/restore/validation_scratch.py` — private system-temp run/session
  ownership and cleanup;
- reuse of C4-I `open_selected_source(...)`, `HeldSource` identity/digest,
  `stage_source(...)` and `validate_staged_candidate(...)`;
- typed presentation-safe result state;
- generation/cancel/reselection invalidation;
- launcher-private retained source path + `SourceIdentity` + full SHA-256 proof;
- staged validation candidate removed before successful proof publication;
- targeted tests;
- `scripts/smoke_restore_validation_session.py` exact-head service smoke.

Validation scratch is conceptually:

```text
<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/
```

It is separate from durable C4-I `<user-data>/restore` state, uses launcher-owned
UUID4 names and user-only permissions, and cleanup requires ownership markers.

## A1 hard prohibitions

A1 must not and the current implementation may not:

- call `execute_restore(...)`;
- create `RestoreOperationStateStore` state or any durable Restore phase;
- create a `before_restore` safety copy;
- replace or migrate the working database;
- perform rollback/startup-recovery mutation;
- write Restore AuditLog;
- stop the ordinary backend as part of candidate validation;
- implement HTTP control plane, bootstrap/session tokens or `command_seq`;
- invoke `/usr/bin/osascript` or implement a native picker;
- implement `/backups/restore` or any frontend Restore UI;
- add a new dependency or packaging implementation.

A1 result objects may expose only presentation-safe state, opaque run/session IDs,
generation, sanitized display filename, compatibility category and fixed guidance.
Absolute source path, `SourceIdentity` and SHA-256 are launcher-private retained
proof only.

## A1 verification gate

Before A1 closure and merge readiness:

```text
exact published head
→ clean checkout
→ git diff --check
→ python3 scripts/check_documentation_lifecycle.py
→ targeted A1 tests
→ existing C4-I Restore regression tests
→ full backend + launcher regression suite
→ exact-head scripts/smoke_restore_validation_session.py
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

No test or smoke result is considered PASS unless actually run on the exact
published head.

## Successor gate

A2 remains blocked. After A1 passes its exact-head gate and merges:

1. update `main`;
2. record A1 reviewed head and merge commit;
3. close A1 lifecycle/project memory;
4. only then authorize/create a fresh A2 branch from updated `main`.

A3/A4 remain predecessor-gated. C4-II-B remains separately not authorized.

## Bounded supersession map

Older documents may retain dated C4/CR-011/A1 authorization labels. Durable
semantics remain authoritative; only lifecycle labels are superseded by this
profile:

- `docs/decisions/0016-launcher-assisted-restore.md` — durable C4-I safety remains;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — C4-I
  closure remains;
- ADR 0018 — selected interaction architecture remains unchanged;
- `docs/architecture.md`, `docs/roadmap.md`, `docs/backup-and-restore.md` — dated
  implementation status only.

## Project history

Searchable history under `docs/history/` is non-normative evidence. The five
protected pre-compaction snapshots must remain byte-identical.

## Documentation consistency check

Run:

```bash
python3 scripts/check_documentation_lifecycle.py
```

The checker must verify the post-PR-173 baseline, A1 current-changeset status,
A1 runtime boundaries, A2/A3/A4 gates, C4-II-B prohibition, ADR authority,
required history paths and five exact historical Git blob identities.
