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
PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
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

A2 is not `DONE` merely because its implementation exists. It closes only after
the exact published head passes protocol/security/concurrency tests, A1/C4-I and
full regressions, the exact-head direct-local-HTTP smoke, independent audit, merge,
and a post-merge lifecycle update from new `main`.

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

### A1 closure / A2 authorization / PR #175

- reviewed head: `b1a48d8f668fa984e3032f85c226f77e30d92e4e`
- merge: `636645ece744752f6a753ae5a25a05297fd34e10`
- docs-only exact-head lifecycle gate: PASS
- independent exact-head audit: P0=0 / P1=0 / P2=0

The current A2 implementation branch starts directly from merge
`636645ece744752f6a753ae5a25a05297fd34e10`.

## Closed A1 boundary

A1 remains merged and exact-head verified. It provides the only launcher-owned
non-destructive candidate-preparation service:

- `RestoreCandidatePreparationService.prepare_restore_candidate(...)`;
- private owned validation scratch;
- direct C4-I source intake/staging/validation reuse;
- source identity/SHA-256 re-proof;
- generation/cancel/reselection invalidation;
- presentation-safe typed result;
- launcher-private retained path + `SourceIdentity` + SHA-256.

A2 does not duplicate or weaken that service.

## A2 implemented boundary — exact-run launcher control plane

The current changeset implements only the already-authorized A2 boundary:

- `launcher/restore/control_protocol.py` — typed presentation/session and
  launcher-owned source-selection adapter contracts;
- `launcher/restore/control_session.py` — one-use bootstrap, run-scoped session,
  15-second heartbeat / 60-second authenticated inactivity expiry, monotonic
  `command_seq`, idempotent retry, generation/cancel and one worker owner;
- `launcher/restore/control_plane.py` — stdlib concurrent HTTP boundary bound
  exactly to `127.0.0.1` on an OS-assigned ephemeral port;
- exact Host and configured local frontend Origin checks;
- no wildcard CORS, no cookie authority, `Cache-Control: no-store`;
- narrow endpoint vocabulary only:
  `POST /v1/bootstrap`, `GET /v1/state`, `POST /v1/heartbeat`,
  `POST /v1/restore/select`, `POST /v1/restore/cancel`;
- expected-next command sequence consumed atomically before business preconditions;
- malformed/auth/Host/Origin/schema/stale/future refusals occur before consumption;
- one launcher-owned selection/validation worker with generation-gated publication;
- runtime ownership: control plane starts after the owned backend proves lock +
  listening socket and closes before backend/lifecycle release;
- if control startup is unsafe, ordinary product operation continues without a
  fallback Restore transport;
- exact-head direct-local-HTTP smoke in `scripts/smoke_restore_control_plane.py`.

### Mandatory A2→A3 seam

Production A2 uses `UnavailableSourceSelectionAdapter` and returns typed
`picker_unavailable`. It obtains **no filesystem path**. Tests/smoke may inject a
launcher-owned fake adapter directly. HTTP payload schema has no path/file/upload
field and no test-only filesystem route.

The real `/usr/bin/osascript` picker remains A3 scope.

### Mandatory A2→A4 seam

`open_runtime_browser(...)` remains the ordinary existing product URL. The A2
runtime does **not** append `#cw-control`, bootstrap capability, control port or
session material to production browser navigation. First production bootstrap
fragment handoff and removal remain A4 scope together with `/backups/restore`.

## A2 hard prohibitions

The current A2 changeset must not:

- invoke `/usr/bin/osascript`, `subprocess` picker code or `shell=True`;
- expose browser-controlled `path`, `source_path`, file bytes, upload/blob,
  bookmark/handle or equivalent filesystem authority;
- add `/backups/restore` or frontend Restore code;
- put bootstrap/session capability in production URL/query/localStorage;
- add destructive execute/confirm command or call `execute_restore(...)`;
- create durable Restore phase/state or `before_restore` safety copy;
- replace/migrate the working database, rollback/recover or write Restore AuditLog;
- add an ordinary FastAPI Restore mutation endpoint;
- add WebSocket, generic localhost command server, dependency or packaging work.

ADR 0016 destructive semantics and ADR 0018 architecture remain unchanged.

## A2 verification gate

Before A2 can close, the exact published head must pass:

```text
clean checkout
→ git diff --check
→ python3 scripts/check_documentation_lifecycle.py
→ targeted A2 protocol/security/concurrency/runtime tests
→ A1 validation-session tests
→ existing C4-I Restore regression tests
→ full backend + launcher regression suite
→ python3 scripts/smoke_restore_control_plane.py --expected-head <HEAD>
→ clean checkout/head re-check
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

No PASS is claimed until those commands run on the exact published head.

## Successor gate

A3 remains blocked. After A2 passes its exact-head gate and merges:

1. update `main`;
2. record A2 reviewed head and merge evidence;
3. close A2 lifecycle/project memory;
4. only then authorize/create a fresh A3 branch from updated `main`.

A4 remains predecessor-gated. C4-II-B remains separately not authorized.

## C4-II-B boundary

C4-II-B remains **PLANNED — NOT AUTHORIZED**. No A2 token, browser state or
command is destructive authority. Future C4-II-B must reopen/re-prove the
launcher-private original path, compare `SourceIdentity`, recompute SHA-256,
re-check sidecars, re-stage/revalidate, prove backend exclusion, create mandatory
`before_restore` safety copy and only then enter existing C4-I destructive execution.

## Bounded supersession map

Older documents may retain dated C4/CR-011/A1/A2 status labels. Durable semantics
remain authoritative; only lifecycle labels are superseded by this profile:

- `docs/decisions/0016-launcher-assisted-restore.md` — durable C4-I safety remains;
- `docs/decisions/0017-c4-i-lifecycle-closure-and-c4-ii-decision-gate.md` — C4-I closure remains;
- ADR 0018 — selected interaction architecture remains unchanged;
- `docs/architecture.md`, `docs/roadmap.md`, `docs/backup-and-restore.md` — dated implementation status only.

## Project history

Searchable history under `docs/history/` is non-normative evidence. The five
protected pre-compaction snapshots remain byte-identical.
