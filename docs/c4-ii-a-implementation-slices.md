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
```

## Current slice status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

A2 runtime work may begin only after this post-A1 lifecycle closure is merged to
`main`. Each later implementation slice starts from updated `main`; never branch
from an unmerged predecessor.

## A1 — Validation-session core — CLOSED

A1 merged in PR #174 and passed its exact-head gate at
`e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5`:

- `git diff --check`: PASS;
- lifecycle checker: PASS;
- real-service A1 smoke: PASS;
- targeted A1 tests: 17 passed;
- existing C4-I Restore regression: 514 passed, 34 deselected;
- full backend + launcher regression: 2415 passed;
- independent audit: P0=0 / P1=0 / P2=0.

A1 provides:

- `RestoreCandidatePreparationService.prepare_restore_candidate(...)`;
- private system-temp validation scratch:
  `<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/`;
- canonical-root/symlink protections, UUID4 run/session names, user-only
  permissions and exact ownership/version markers;
- direct C4-I reuse: `open_selected_source(...)`, `HeldSource` identity/digest,
  sidecar checks, `stage_source(...)`, `validate_staged_candidate(...)`;
- source identity/digest/self-containment re-proof;
- typed presentation-safe result with bounded display label;
- launcher-private retained canonical source path + `SourceIdentity` + SHA-256;
- generation/cancel/reselection invalidation;
- owned-only cleanup.

A1 did not implement HTTP control, picker, browser Restore UI or destructive
Restore.

## A2 — Exact-run launcher control plane — AUTHORIZED NEXT

### Goal

Implement the exact-run launcher-owned loopback control/session protocol around
A1 without implementing the real picker, browser Restore workspace or destructive
Restore.

### Authorized scope

- bind exactly `127.0.0.1` on an OS-assigned ephemeral port;
- validate exact Host and configured local frontend Origin;
- no wildcard CORS and no credentialed cookie authority;
- one-use bootstrap capability with at least 256 bits entropy;
- atomic compare-and-consume of bootstrap capability;
- separate run-scoped session token with at least 256 bits entropy;
- `Cache-Control: no-store` on control/session state;
- heartbeat every 15 seconds;
- authenticated inactivity expiry after 60 seconds;
- concurrent servicing while long work occurs outside the request loop;
- request ID with at least 128 bits entropy plus strict monotonic `command_seq`;
- expected-next sequence consumed before business precondition evaluation;
- idempotent retry semantics and stale/replay rejection;
- generation/cancel integration with A1;
- launcher start/stop ownership of the control plane;
- launcher-owned source-selection adapter/port boundary;
- typed state endpoint and typed safe control responses.

### Mandatory sequence semantics

Authentication, Host/Origin and syntax failures do **not** consume
`command_seq`. After authentication/syntax succeeds, an expected-next command
consumes its sequence atomically **before** business precondition evaluation.
Therefore a typed business rejection cannot later become success by replaying the
same sequence.

The same current sequence + same request ID may return the cached idempotent
result. Same sequence + different request ID, stale sequence or future sequence
must fail closed.

### Mandatory concurrency/liveness semantics

The HTTP request loop must remain serviceable while selection/validation work is
in flight. Heartbeat/state/cancel cannot depend on the long worker returning.
Cancellation/expiry invalidates A1 generation immediately; scratch cleanup waits
for the owning worker to quiesce.

### Mandatory A2→A3 seam

A2 must not implement a real native picker. Production A2 uses a launcher-owned
adapter returning typed `picker_unavailable` and obtains **no source path**.

Tests may inject a launcher-owned fake adapter directly into launcher/control
code. The browser may never provide source path, file bytes, upload/blob, file
handle/bookmark or filesystem authority. No temporary query/body field such as
`path` or `source_path`, no production test-bypass route and no generic
filesystem/shell/SQL endpoint is allowed.

A3 replaces the production `picker_unavailable` adapter with the real macOS
picker.

### Mandatory A2→A4 seam

The production product-browser launch URL remains unchanged in A2. Do not append
the bootstrap fragment to actual browser navigation yet. A4 owns the first
production launcher browser handoff together with fragment consumer/removal and
`sessionStorage` handling.

A2 exact-head smoke uses a direct authenticated local HTTP harness instead.

### A2 non-goals

A2 must not implement:

- real `/usr/bin/osascript` picker;
- `/backups/restore` or frontend Restore UI;
- production browser bootstrap-fragment handoff;
- destructive confirmation/execute command;
- `execute_restore(...)`;
- durable Restore operation/phase;
- `before_restore` safety-copy creation;
- working-database replacement/migration;
- rollback/recovery mutation;
- Restore AuditLog;
- ordinary FastAPI Restore mutation endpoint;
- WebSocket or generic localhost command server;
- new dependency or packaging implementation.

### Required A2 automated proof

At minimum prove:

1. exact loopback-only ephemeral bind;
2. wrong/missing Host rejected;
3. wrong/missing Origin rejected where Origin is required;
4. no wildcard CORS/cookie authority;
5. bootstrap capability is one-use under concurrent attempts;
6. bootstrap/session tokens meet entropy contract and are run-scoped;
7. state/session responses use `Cache-Control: no-store`;
8. heartbeat/session expiry semantics match 15s/60s contract;
9. heartbeat/state/cancel remain serviceable while long fake selection/validation runs;
10. invalid auth/syntax does not consume `command_seq`;
11. valid expected-next typed business rejection consumes its sequence;
12. same sequence + same request ID is idempotent;
13. same sequence + different request ID fails;
14. stale/future sequence fails closed;
15. duplicate concurrent select is rejected;
16. cancel/expiry/reselection invalidates A1 retained proof/generation;
17. production adapter returns `picker_unavailable` and obtains no path;
18. browser/request DTO contains no source-path field or file payload;
19. production browser URL remains unchanged;
20. no durable Restore state/safety copy/AuditLog/working-DB mutation;
21. A1 and existing C4-I regression remain green.

### Required A2 exact-head smoke

Use the real loopback control server and direct authenticated local HTTP client on
the exact published head. The production `picker_unavailable` seam may be tested
for its typed result, and a launcher-owned fake adapter may be injected directly
to prove A1 integration. Do not use a browser path/file bypass or synthetic final
HTTP result.

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

A3 replaces A2 `picker_unavailable` and may not add browser path fallback. The
production browser launch URL still remains unchanged; final browser handoff is
A4 scope.

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
- typed safe selecting/validating/accepted/rejected/cancelled/technical states;
- no absolute path/raw SQLite/migration IDs/stack/internal paths in browser;
- real A2 control + A3 picker + A1 validation integration;
- exact-head end-to-end non-destructive macOS smoke.

A4 must not implement destructive Restore confirmation, `execute_restore(...)`
control command, safety-copy creation, backend replacement/migration or C4-II-B.

## Cross-slice constraints

Every A2–A4 PR preserves:

- ADR 0016 destructive state machine unchanged;
- ADR 0018 launcher-owned control/picker/session architecture;
- browser presentation only, never absolute-path authority;
- ordinary FastAPI remains business API, not Restore mutation authority;
- C4-II-A strictly non-destructive;
- source byte-identical;
- A1 C4-I staging/validation semantics reused, not weakened;
- ordinary backend may remain running during non-destructive validation;
- no destructive authority before separately authorized C4-II-B;
- no hidden dependency/packaging/test-bypass decision;
- local-first nontechnical product workflow.

## PR discipline

Every slice is a separate small PR with Scope, Non-goals, Architecture
constraints, Backend/Frontend requirements as applicable, Tests, Acceptance
criteria, exact changed-path review, exact-head smoke appropriate to the slice,
independent audit and P0=0/P1=0/P2=0 before merge.
