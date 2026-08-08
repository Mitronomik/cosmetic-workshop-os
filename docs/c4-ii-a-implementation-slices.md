# C4-II-A implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-08`

This document bounds implementation of
`C4-II-A — Launcher Restore source selection and non-destructive validation presentation`.
It does not change ADR 0018 and does not authorize C4-II-B destructive execution.

## Merged authorization baseline

```text
PR #172 / CR-011 merge — 998596560db6780a677bdec363d1fd19db30c1b6
PR #173 reviewed head — 9f5722c5dec695588596d45daa5588092ce7f080
PR #173 merge — aaedf2735660fb92eb627f7eeab327437d459b56
PR #174 reviewed A1 head — e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5
PR #174 merge — 504e776508c940554b3ee8659a201af21db8303c
PR #175 reviewed closure head — b1a48d8f668fa984e3032f85c226f77e30d92e4e
PR #175 merge — 636645ece744752f6a753ae5a25a05297fd34e10
```

## Current slice status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

Each later slice starts from updated `main`; never branch from an unmerged or
not-yet-closed predecessor.

## A1 — Validation-session core — CLOSED

A1 merged in PR #174 and passed its exact-head gate at
`e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`:

- lifecycle checker and A1 smoke: PASS;
- targeted A1 tests: 17 passed;
- existing C4-I Restore regression: 514 passed, 34 deselected;
- full backend + launcher regression: 2415 passed;
- independent audit: P0=0 / P1=0 / P2=0.

A1 remains the single candidate-preparation authority and directly reuses C4-I
`open_selected_source(...)`, held-source identity/digest/sidecar proof,
`stage_source(...)` and `validate_staged_candidate(...)`.

## A2 — Exact-run launcher control plane — CURRENT IMPLEMENTATION

### Goal

Implement the exact-run launcher-owned loopback control/session protocol around
A1 without implementing the real picker, browser Restore workspace or destructive
Restore.

### Implemented in the current changeset

- `launcher/restore/control_protocol.py` — typed control state and launcher-owned
  source-selection adapter contract;
- `launcher/restore/control_session.py` — one-use bootstrap, run-scoped session,
  command ordering, inactivity expiry, generation/cancel integration and one
  worker owner;
- `launcher/restore/control_plane.py` — stdlib `ThreadingHTTPServer` loopback
  boundary bound exactly to `127.0.0.1` on OS-assigned ephemeral port;
- exact Host and configured local frontend Origin checks;
- no wildcard CORS, no cookie authority and `Cache-Control: no-store`;
- endpoint vocabulary exactly:
  `POST /v1/bootstrap`, `GET /v1/state`, `POST /v1/heartbeat`,
  `POST /v1/restore/select`, `POST /v1/restore/cancel`;
- 256-bit-class bootstrap and session secrets from `secrets`;
- atomic compare-and-consume bootstrap with consumed capability cleared from
  coordinator memory;
- 15-second heartbeat contract and 60-second authenticated inactivity expiry;
- >=128-bit request-ID namespace plus strict monotonic `command_seq`;
- authentication/Host/Origin/schema/sequence validation before sequence consume;
- exact expected-next sequence consumed before business precondition evaluation;
- same-sequence/same-request idempotency and stale/future/conflict rejection;
- concurrent HTTP servicing while the one selection/validation worker is in flight;
- A1 generation/proof invalidation on reselect/cancel/expiry/close;
- generation-gated worker publication and worker quiescence before final A1 cleanup;
- launcher runtime start/stop ownership after proved backend startup;
- direct-local-HTTP exact-head smoke using injected launcher-owned fake picker and
  real A1/C4-I validation path.

### Mandatory sequence semantics

Authentication, Host/Origin, JSON/schema and sequence failures do **not** consume
`command_seq`. After those checks succeed, an expected-next command consumes its
sequence atomically **before** business precondition evaluation. Therefore
`action_in_progress` and other typed business refusals stay consumed and cannot
later become success by replay.

Same current sequence + same request ID + same command returns the retained safe
reply. Same sequence + different request ID/command conflicts. Stale and skipped
future sequences fail closed.

### Mandatory concurrency/liveness semantics

The HTTP request loop remains serviceable while selection/validation runs on its
launcher-owned worker. Heartbeat/state/cancel do not wait for that worker.
Cancellation/expiry invalidates session/A1 authority immediately; late worker
results cannot publish. Cleanup that owns worker scratch waits for quiescence.

### Mandatory A2→A3 seam

Production A2 uses `UnavailableSourceSelectionAdapter`, returns typed
`picker_unavailable`, and obtains **no source path**.

Tests/smoke may inject a launcher-owned fake adapter directly. Browser/control
requests may never provide source path, file bytes, upload/blob, file
handle/bookmark or equivalent filesystem authority. Select/cancel request schema
contains only `request_id` and `command_seq`. There is no query/body `path` or
`source_path`, test-bypass route or generic filesystem/shell/SQL endpoint.

A3 replaces the production `picker_unavailable` adapter with the real macOS
picker only after A2 closure.

### Mandatory A2→A4 seam

The production product-browser launch URL remains unchanged in A2. Runtime does
not append `#cw-control`, bootstrap capability, control port or session material
to actual product navigation. A4 owns first production handoff, fragment
consumer/removal, `sessionStorage` and `/backups/restore`.

A2 exact-head smoke therefore uses a direct authenticated local HTTP harness.

### A2 non-goals

A2 must not implement:

- real `/usr/bin/osascript` picker;
- `/backups/restore` or frontend Restore UI;
- production browser bootstrap-fragment handoff;
- destructive confirmation/execute command or `execute_restore(...)`;
- durable Restore operation/phase or `before_restore` safety copy;
- working-database replacement/migration;
- rollback/recovery mutation or Restore AuditLog;
- ordinary FastAPI Restore mutation endpoint;
- WebSocket or generic localhost command server;
- new dependency or packaging implementation.

### Required A2 automated proof

At minimum prove:

1. exact loopback-only ephemeral bind;
2. wrong/missing/duplicate Host rejected;
3. wrong/missing/duplicate Origin rejected;
4. no wildcard CORS/cookie authority;
5. bootstrap capability has exactly one concurrent winner;
6. bootstrap/session secrets meet entropy boundary and remain run-scoped;
7. state/session responses use `Cache-Control: no-store`;
8. heartbeat/session expiry match 15s/60s contract;
9. heartbeat/state/cancel stay responsive while fake long work runs;
10. invalid auth/Host/Origin/JSON/schema/sequence does not consume `command_seq`;
11. valid expected-next typed business rejection consumes its sequence;
12. same sequence + same request ID is idempotent;
13. same sequence + different request ID/command fails;
14. stale/future sequence fails closed;
15. duplicate select while worker owns the session returns consumed `action_in_progress`;
16. cancel/expiry/reselection invalidates A1 retained proof/generation;
17. production adapter returns `picker_unavailable` and obtains no path;
18. browser/request DTO contains no source-path/file authority;
19. production browser URL remains unchanged;
20. runtime orders backend start → control start → browser and control close → backend stop;
21. no durable Restore state/safety copy/AuditLog/working-DB mutation;
22. A1 and existing C4-I regression remain green.

### Required A2 exact-head smoke

Use the real loopback control server and direct authenticated local HTTP client on
the exact published head. Inject a launcher-owned fake adapter directly to prove
real A1 integration. Do not use browser path/file bypass or synthetic final HTTP
state.

## A3 — Native macOS picker integration

### Entry gate

A2 must be independently reviewed, exact-head tested/smoked, merged and lifecycle
closed from updated `main` first.

### Authorized scope after gate opens

- owned short-lived `/usr/bin/osascript` child;
- macOS Standard Additions `choose file`;
- no `shell=True`;
- no `System Events`;
- no user-controlled text interpolated into executable AppleScript;
- typed picker cancellation;
- absolute POSIX path returned only to launcher memory;
- picker worker ownership/termination;
- select → real picker → A1 candidate preparation;
- cancel/expiry invalidation and worker-quiescence cleanup.

A3 may not add browser path fallback. Production browser launch URL remains
unchanged until A4.

## A4 — Browser Restore screen and non-destructive E2E flow

### Entry gate

A3 merged + independently exact-head verified first.

### Authorized scope after gate opens

- exact SPA route `/backups/restore` and entry from `/backups`;
- first production launcher browser handoff carrying bootstrap in URL fragment;
- immediate fragment consumption/removal;
- `sessionStorage` run token + non-secret `control_origin`;
- fail-closed missing/invalid launcher session;
- select/cancel/reselect/reload;
- typed safe non-destructive states;
- real A2 control + A3 picker + A1 validation integration;
- exact-head end-to-end non-destructive macOS smoke.

A4 must not implement destructive Restore confirmation, `execute_restore(...)`,
safety-copy creation, backend replacement/migration or C4-II-B.

## Cross-slice constraints

Every A2–A4 PR preserves:

- ADR 0016 destructive state machine unchanged;
- ADR 0018 launcher-owned control/picker/session architecture;
- browser presentation only, never absolute-path authority;
- ordinary FastAPI remains business API, not Restore mutation authority;
- C4-II-A strictly non-destructive;
- A1/C4-I staging/validation semantics reused, not weakened;
- ordinary backend remains usable during non-destructive validation;
- no destructive authority before separately authorized C4-II-B;
- no hidden dependency/packaging/test-bypass decision;
- local-first nontechnical product workflow.

## PR discipline

Every slice is a separate small PR with Scope, Non-goals, Architecture
constraints, Backend/Frontend requirements, Tests, Acceptance criteria, exact
changed-path review, exact-head smoke, independent audit and
P0=0/P1=0/P2=0 before merge.
