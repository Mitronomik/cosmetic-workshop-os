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

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains
authoritative for launcher-owned interaction/control/picker/validation.

## Current lifecycle

```text
PR #173 — MERGED — C4-II-A SLICED AUTHORIZATION
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
PR #177 — MERGED — A2 CLOSED / A3 AUTHORIZED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
CR-010 — ACCEPTED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
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

A3 is implemented only in the current changeset. It is not `DONE` until its exact
published head passes the gate below, merges, and lifecycle is closed from updated
`main`. A4 and C4-II-B remain closed.

## Verified merge baselines

### C4-I / PR #170
- reviewed head: `ac95e2990efa979b3ded6cb48f91ddd0750aa7c8`
- merge: `e6997281d2e0268ce54184d988c114bac71c35e2`

### CR-011 / PR #172
- reviewed head: `c51d5baa07e4cd8912b1973649c22b20f581e3d2`
- merge: `998596560db6780a677bdec363d1fd19db30c1b6`
- architecture gate: P0=0 / P1=0 / P2=0

### C4-II-A1 / PR #174
- reviewed head: `e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`
- merge: `504e776508c940554b3ee8659a201af21db8303c`
- A1: 17 passed; C4-I: 514 passed; full: 2415 passed; smoke PASS; audit 0/0/0.

### C4-II-A2 / PR #176
- reviewed head: `681cb4050bec082db6b637285590e232880af739`
- merge: `90a14dd9a11b83bc31a40e1d3fb9523f41772b88`
- stale-A1-authority race regression: 2 passed
- all A2 targeted tests: 28 passed
- A1: 17 passed
- C4-I: 514 passed, 62 deselected
- full backend + launcher regression: 2443 passed
- exact-head A2 smoke: PASS
- independent audit: P0=0 / P1=0 / P2=0

### A2 closure / A3 authorization / PR #177
- reviewed head: `d767b957cb3debae584709f2bbadafebd8dd6a9e`
- merge: `e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263`
- docs lifecycle gate: PASS
- changed paths: exactly 12 docs/state/checker files
- independent closure audit: P0=0 / P1=0 / P2=0

The current A3 branch starts directly from merge
`e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263`.

## Closed A1 boundary

A1 remains the single launcher-owned non-destructive candidate-preparation
authority: private validation scratch, direct C4-I intake/staging/validation,
source identity/SHA-256 re-proof, generation invalidation and launcher-private
retained source proof.

## Closed A2 boundary

A2 remains the exact-run control/session authority: exact loopback + Host/Origin,
atomic one-use bootstrap, run token, no-store/narrow CORS, 15s/60s liveness,
strict `command_seq`, one long-work owner, responsive heartbeat/state/cancel,
generation-gated publication and stale A2→A1 proof-race hardening.

The default `UnavailableSourceSelectionAdapter` remains available for direct/test
construction. A3 does not weaken or replace that closed A2 test seam.

## A3 implemented boundary — native macOS picker

The current changeset adds only the already-authorized native source-selection
adapter:

- `launcher/restore/macos_picker.py` — `MacOSNativeSourceSelectionAdapter`;
- exact production helper constant `/usr/bin/osascript`;
- fixed Standard Additions `choose file` AppleScript;
- no user-controlled script interpolation;
- `shell=False`; no `System Events`;
- error `-128` converted to typed ordinary cancellation by an internal sentinel;
- selected result must be an absolute POSIX path and remains launcher-private;
- A2 `cancel_event` is polled while the picker child runs;
- cancel/expiry/close terminates and reaps the owned child, with kill fallback;
- technical picker failures surface only through the existing safe A2
  `selection_failed` boundary;
- production `runtime.start_restore_control_plane(...)` injects the native adapter
  into the existing A2 `RestoreControlPlane`;
- selected path flows only into merged A1 candidate preparation;
- no new runtime dependency.

The picker does not decide whether a file is a valid backup. A1/C4-I intake and
validation remain acceptance authority.

### A3 verification assets

- `launcher/tests/test_restore_native_picker.py`;
- `launcher/tests/test_restore_native_picker_session.py`;
- `launcher/tests/test_restore_native_picker_runtime.py`;
- `scripts/smoke_restore_native_picker.py`.

The smoke performs a non-interactive probe of the exact system
`/usr/bin/osascript`, then uses a launcher-owned process seam to exercise real
A2 control → A3 adapter → A1/C4-I validation without requiring unattended GUI
interaction.

## A3 hard prohibitions

The current A3 changeset must not:

- add browser-controlled `path`, `source_path`, file bytes, upload/blob,
  bookmark/handle or equivalent filesystem authority;
- add `/backups/restore` or any frontend Restore implementation;
- append `#cw-control`, control port, bootstrap capability or session token to
  production browser navigation;
- add destructive confirmation/execute or call `execute_restore(...)`;
- create durable Restore phase/state, `before_restore` safety copy, working-DB
  replacement/migration, rollback/recovery mutation or Restore AuditLog;
- add an ordinary FastAPI Restore mutation endpoint;
- add WebSocket/generic localhost command server;
- add dependency or packaging implementation.

## A3 exact-head verification gate

Before A3 can close, the exact published head must pass:

```text
clean checkout
→ git diff --check e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ targeted A3 native-picker/process/cancel/runtime tests
→ all closed A2 control/session/security/concurrency regressions
→ A1 validation-session regressions
→ existing C4-I Restore regressions
→ full backend + launcher regression suite
→ python3 scripts/smoke_restore_native_picker.py --expected-head <HEAD>
→ clean status/head re-check
→ independent exact-head code/architecture audit
→ P0=0 / P1=0 / P2=0
```

No PASS is claimed until these run on the final published A3 head.

## Successor gate

A4 remains blocked. After A3 passes its exact-head gate and merges, lifecycle must
be closed from updated `main` before A4 may start. C4-II-B remains separately not
authorized.

## C4-II-B boundary

Future C4-II-B must reopen/re-prove the launcher-private original path, compare
`SourceIdentity`, recompute SHA-256, re-check sidecars, re-stage/revalidate, prove
backend exclusion, create mandatory `before_restore` safety copy and only then
enter existing C4-I destructive execution. Browser state/token/filename is never
destructive authority.

## Project history

Searchable history under `docs/history/` is non-normative evidence. The five
protected pre-compaction snapshots remain byte-identical.
