# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-08`

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
launcher-owned interaction/control/picker/validation architecture.

## Current lifecycle

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
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

`C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED` becomes the active runtime
successor only after this post-A1 lifecycle-closure changeset is merged to
`main`. Do not start A2 from an unmerged closure branch.

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
- merge: `aaedf2735660fb92eb627f7eeab327437d459b56`
- authorization audit: P0=0 / P1=0 / P2=0

### C4-II-A1 / PR #174

- reviewed head: `e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`
- merge: `504e776508c940554b3ee8659a201af21db8303c`
- exact-head `git diff --check`: PASS
- documentation lifecycle checker: PASS
- A1 exact-head real-service smoke: PASS
- targeted A1 tests: 17 passed
- existing C4-I Restore regression: 514 passed, 34 deselected
- full backend + launcher regression: 2415 passed
- independent exact-head audit: P0=0 / P1=0 / P2=0

## Closed A1 boundary

A1 is now merged and exact-head verified. It provides only the launcher-owned
non-destructive validation-session core:

- `RestoreCandidatePreparationService.prepare_restore_candidate(...)`;
- private system-temp validation scratch under
  `<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/`;
- C4-I source intake, held-descriptor identity/digest/sidecar proof,
  `stage_source(...)` and `validate_staged_candidate(...)` reuse;
- source identity/SHA-256 re-proof;
- generation/cancel/reselection invalidation;
- typed presentation-safe result with bounded safe display filename;
- launcher-private retained canonical source path + `SourceIdentity` + SHA-256;
- owned-only scratch cleanup.

A1 did not add HTTP control, picker, frontend Restore UI, durable Restore state,
safety-copy creation, working-DB replacement/migration, rollback/recovery or
Restore AuditLog.

## A2 authorized boundary — exact-run launcher control plane

A2 may implement only the accepted ADR 0018 exact-run local control boundary:

- bind exactly `127.0.0.1` on an OS-assigned ephemeral port;
- exact Host and configured local frontend Origin validation;
- no wildcard CORS and no cookie-based authority;
- one-use bootstrap capability with at least 256 bits entropy and atomic consume;
- separate run-scoped session token with at least 256 bits entropy;
- `Cache-Control: no-store` on control/session state;
- 15-second heartbeat and 60-second authenticated inactivity expiry;
- concurrent request servicing so heartbeat/state/cancel are not blocked by long work;
- request ID with at least 128 bits entropy plus monotonic `command_seq`;
- expected-next sequence consumed before business precondition evaluation;
- idempotent retry and stale/replay rejection;
- integration with A1 generation/cancel/invalidation;
- launcher lifecycle ownership of control-plane start/stop;
- launcher-owned source-selection adapter boundary.

### Mandatory A2→A3 seam

A2 must **not** implement the real native picker. Production A2 uses a
launcher-owned adapter returning typed `picker_unavailable` and obtains no
filesystem path.

Tests may inject a launcher-owned fake adapter directly. The browser may never
supply `path`, `source_path`, file bytes, upload/blob, file handle/bookmark or any
filesystem authority. Do not add a test-only HTTP bypass route or generic
filesystem/shell/SQL command surface.

### Mandatory A2→A4 seam

The production product-browser launch URL remains unchanged in A2. A2 must not
append the bootstrap fragment to actual product navigation because the browser
consumer/removal logic does not exist until A4. Exact-head A2 smoke therefore
uses a direct authenticated local HTTP harness.

## A2 non-goals

A2 must not implement:

- real `/usr/bin/osascript` picker — A3;
- `/backups/restore` browser workspace — A4;
- production browser bootstrap-fragment handoff — A4;
- destructive Restore confirmation or `execute_restore(...)` — C4-II-B;
- ordinary FastAPI Restore mutation endpoint;
- durable Restore operation/phase or `before_restore` safety copy;
- working-DB replacement/migration, rollback or recovery mutation;
- Restore AuditLog;
- WebSocket, generic localhost command server, new dependency or packaging work.

## A2 verification gate

Before A2 can close, its exact published head must pass:

```text
clean checkout
→ git diff --check
→ documentation lifecycle checker
→ targeted A2 protocol/security/concurrency tests
→ A1 + existing C4-I Restore regression tests
→ full backend + launcher regression suite
→ exact-head A2 direct-local-HTTP smoke
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

A3 remains blocked until A2 is independently reviewed, exact-head verified,
merged and lifecycle/project memory is updated from new `main`.

## C4-II-B boundary

C4-II-B remains separately **PLANNED — NOT AUTHORIZED**. No A2 command may become
destructive authority. Future C4-II-B must reopen/re-prove the launcher-private
original path, compare `SourceIdentity`, recompute SHA-256, re-check sidecars,
re-stage/revalidate, prove backend exclusion, create mandatory `before_restore`
safety copy and only then enter existing C4-I destructive execution.

## Bounded supersession map

Older documents may retain dated C4/CR-011/A1 status labels. Durable semantics
remain authoritative; only lifecycle labels are superseded by this profile:

- `docs/decisions/0016-launcher-assisted-restore.md` — durable C4-I safety remains;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — C4-I closure remains;
- ADR 0018 — selected interaction architecture remains unchanged;
- `docs/architecture.md`, `docs/roadmap.md`, `docs/backup-and-restore.md` — dated implementation status only.

## Project history

Searchable history under `docs/history/` is non-normative evidence. The five
protected pre-compaction snapshots remain byte-identical.
