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
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
safe packaged update flow — NOT COMPLETED
installation verification — NOT COMPLETED
full release-candidate smoke — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

A3 is the **only** authorized next runtime slice. A4, C4-II-B, C4-II-C and C4-III
remain predecessor/separate-decision gated.

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
- lifecycle checker + A1 smoke: PASS
- targeted A1: 17 passed
- C4-I Restore regression: 514 passed, 34 deselected
- full backend + launcher: 2415 passed
- independent audit: P0=0 / P1=0 / P2=0

### A1 closure / A2 authorization / PR #175

- reviewed head: `b1a48d8f668fa984e3032f85c226f77e30d92e4e`
- merge: `636645ece744752f6a753ae5a25a05297fd34e10`
- docs lifecycle gate: PASS
- audit: P0=0 / P1=0 / P2=0

### C4-II-A2 / PR #176

- reviewed head: `681cb4050bec082db6b637285590e232880af739`
- merge: `90a14dd9a11b83bc31a40e1d3fb9523f41772b88`
- `git diff --check`: PASS
- documentation lifecycle checker: PASS
- stale-A1-authority race regression: 2 passed
- all A2 targeted tests: 28 passed
- merged A1 tests: 17 passed
- C4-I Restore regression: 514 passed, 62 deselected
- full backend + launcher regression: 2443 passed
- exact-head direct-local-HTTP A2 smoke: PASS
- independent exact-head audit: P0=0 / P1=0 / P2=0

## Closed A1 boundary

A1 remains the single launcher-owned non-destructive candidate-preparation
authority:

- `RestoreCandidatePreparationService.prepare_restore_candidate(...)`;
- private owned validation scratch;
- direct C4-I source intake/staging/validation reuse;
- source identity/SHA-256 re-proof;
- generation/cancel/reselection invalidation;
- presentation-safe typed result;
- launcher-private retained source proof.

## Closed A2 boundary

A2 is merged and exact-head verified. It owns the exact-run launcher Restore
control/session boundary:

- stdlib concurrent HTTP server bound exactly to `127.0.0.1:<ephemeral>`;
- exact Host + configured local frontend Origin;
- one-use 256-bit-class bootstrap and separate run-scoped token;
- no wildcard CORS/cookie authority; no-store responses;
- 15-second heartbeat / 60-second authenticated inactivity expiry;
- strict monotonic `command_seq` with idempotent same-request replay;
- one long-work owner while heartbeat/state/cancel remain serviceable;
- cancel/expiry/reselection/close invalidate A1 proof/generation;
- stale A2→A1 begin race hardened so retained proof cannot resurrect after
  cancellation/expiry before worker quiescence;
- runtime order remains proved backend → control → ordinary browser and
  control close → backend stop.

A2 still uses `UnavailableSourceSelectionAdapter` in production. The browser has
no source path/file authority and product navigation still carries no control
bootstrap/session material.

## Authorized A3 boundary — native macOS picker only

A3 may now replace the production `picker_unavailable` seam with the launcher-owned
native picker already selected by ADR 0018:

- owned short-lived `/usr/bin/osascript` child;
- macOS Standard Additions `choose file`;
- fixed executable AppleScript with no user-controlled text interpolation;
- no `shell=True`;
- no `System Events` automation;
- typed ordinary picker cancellation;
- selected absolute POSIX path returned only to launcher memory;
- cancel/expiry must terminate the owned picker child and coordinate quiescence;
- selected path flows only through the existing A2 `SourceSelectionAdapter` seam
  into the merged A1 candidate-preparation service;
- no new Python/application dependency.

### A3 hard prohibitions

A3 must not:

- add browser-controlled `path`, `source_path`, upload/blob/file bytes,
  bookmark/handle or equivalent filesystem authority;
- add `/backups/restore` or any frontend Restore implementation;
- append `#cw-control`, control port, bootstrap capability or session token to
  production browser navigation;
- add destructive confirmation/execute or call `execute_restore(...)`;
- create durable Restore phase/state, `before_restore` safety copy, working-DB
  replacement/migration, rollback/recovery mutation or Restore AuditLog;
- add an ordinary FastAPI Restore mutation endpoint;
- add WebSocket/generic localhost command server;
- add packaging/cloud sync/OCR/multiuser/advanced-analytics scope.

## A3 verification gate

Before A3 can close, the final exact published head must prove at minimum:

```text
clean checkout
→ git diff --check
→ python3 scripts/check_documentation_lifecycle.py
→ targeted native-picker adapter/process/cancel tests
→ A2 control/session/security/concurrency regressions
→ A1 validation-session regressions
→ existing C4-I Restore regressions
→ full backend + launcher regression suite
→ exact-head A3 smoke that proves picker-adapter → A2 → A1 integration without browser path authority
→ clean checkout/head re-check
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

The real GUI picker does not authorize destructive Restore. A3 remains strictly
non-destructive.

## Successor gate

A4 remains blocked. After A3 passes exact-head verification and merges:

1. update `main`;
2. record A3 reviewed head and merge evidence;
3. close A3 lifecycle/project memory;
4. only then authorize/create A4 from updated `main`.

C4-II-B remains separately not authorized.

## C4-II-B boundary

Future C4-II-B must reopen/re-prove the launcher-private original path, compare
`SourceIdentity`, recompute SHA-256, re-check sidecars, re-stage/revalidate, prove
backend exclusion, create mandatory `before_restore` safety copy and only then
enter existing C4-I destructive execution. Browser state/token/filename is never
destructive authority.

## Project history

Searchable history under `docs/history/` is non-normative evidence. The five
protected pre-compaction snapshots remain byte-identical.
