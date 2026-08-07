# C4-II-A implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-07`

This document bounds implementation of
`C4-II-A — Launcher Restore source selection and non-destructive validation presentation`.
It does not change ADR 0018 and does not authorize C4-II-B destructive execution.

## Merged authorization baseline

```text
PR #172 / CR-011 merge — 998596560db6780a677bdec363d1fd19db30c1b6
PR #173 reviewed head — 9f5722c5dec695588596d45daa5588092ce7f080
PR #173 merge commit — aaedf2735660fb92eb627f7eeab327437d459b56
```

## Current slice status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A2 — PLANNED — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

Each later implementation slice starts from updated `main`; never branch from an
unmerged predecessor.

## A1 — Validation-session core

### Goal

Implement launcher-owned non-destructive candidate preparation without control
plane, picker, browser UI or destructive Restore.

### Current implementation

The current A1 changeset implements:

- `RestoreCandidatePreparationService.prepare_restore_candidate(...)`;
- launcher-owned validation-session generation/invalidation state;
- private system-temp scratch:
  `<system-temp>/cosmetic-workshop-os/restore-validation/<run-id>/<session-id>/`;
- UUID4 run/session names, restrictive user-only permissions and exact
  ownership/version markers;
- direct reuse of C4-I `open_selected_source(...)`, `HeldSource` identity/digest,
  sidecar checks, `stage_source(...)` and `validate_staged_candidate(...)`;
- source digest/identity/self-containment re-proof after staging and after
  validation;
- typed presentation-safe result state;
- launcher-private retained canonical source path + `SourceIdentity` + SHA-256;
- cancellation/reselection/stale-generation proof invalidation;
- cleanup after success/rejection/cancel/failure plus owned prior-run cleanup;
- targeted tests;
- exact-head real-service smoke on temporary SQLite sources.

Successful A1 validation removes the staged candidate before retained proof is
published. The retained proof is memory-only and is not destructive authority.

### A1 non-goals

A1 must not implement HTTP control plane, browser bootstrap/session tokens,
`command_seq`, native picker, frontend Restore route/UI, destructive confirmation,
`execute_restore(...)`, durable Restore operation/phase, `before_restore` safety
copy, working-database replacement/migration, rollback/startup-recovery mutation,
Restore AuditLog, new dependency or packaging implementation.

A1 must not stop the ordinary backend merely to validate an isolated source copy.

### Required A1 proof

Before A1 is closed:

1. current schema accepted;
2. supported older schema accepted without migrating source/working DB;
3. newer/foreign/empty/corrupt/directory/symlink/sidecar/working-DB rejected;
4. normal selected source byte-identical;
5. working database unchanged;
6. no durable Restore operation/phase;
7. no `before_restore` safety copy;
8. no Restore AuditLog write;
9. stale/cancelled generation cannot retain source proof;
10. reselection clears previous proof before new staging;
11. scratch cleanup is owned-only and restrictive;
12. technical errors expose fixed presentation-safe vocabulary;
13. all existing C4-I Restore tests remain green;
14. exact-head A1 smoke passes on real temporary SQLite files.

## A2 — Exact-run launcher control plane

### Entry gate

A1 must be independently reviewed, exact-head tested/smoked, merged and lifecycle
closed from updated `main` first.

### Authorized scope after gate opens

- bind exactly `127.0.0.1` on OS-assigned ephemeral port;
- exact Host and configured local frontend Origin;
- no wildcard CORS / no credentialed cookie authority;
- one-use >=256-bit bootstrap capability and atomic compare-and-consume;
- >=256-bit run-scoped session token;
- `Cache-Control: no-store`;
- 15-second heartbeat / 60-second authenticated inactivity expiry;
- concurrent servicing while long work runs elsewhere;
- >=128-bit request ID + monotonic `command_seq`;
- valid next sequence consumed before business precondition evaluation;
- idempotent retry / stale replay rejection;
- generation/cancel integration with A1;
- launcher startup/shutdown ownership of control plane;
- launcher-owned source-selection port/interface.

### Mandatory A2→A3 seam

A2 must not implement real native picker. Production A2 uses a launcher-owned
unavailable adapter returning typed `picker_unavailable` and obtains **no source
path**.

Tests may inject a launcher-owned fake picker adapter. The browser may never
provide source path, file bytes or filesystem handle. No temporary query/body
field such as `path`, `source_path`, upload/blob or production test-bypass route
is allowed.

The production browser launch URL remains unchanged until A4. A2 may test the
control plane through a direct local authenticated HTTP harness; it must not
append the bootstrap fragment to real product browser navigation yet.

A2 must not implement real picker, `/backups/restore`, destructive command,
ordinary FastAPI Restore endpoint, generic shell/filesystem/SQL proxy, WebSocket
or hidden dependency.

## A3 — Native macOS picker integration

### Entry gate

A2 merged + independently exact-head verified first.

### Authorized scope

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

### Authorized scope

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

Every A1–A4 PR preserves:

- ADR 0016 destructive state machine unchanged;
- ADR 0018 launcher-owned control/picker/session architecture;
- browser presentation only, never absolute-path authority;
- ordinary FastAPI remains business API, not Restore mutation authority;
- C4-II-A strictly non-destructive;
- source byte-identical;
- no second weaker staging/validation implementation;
- ordinary backend may remain running during non-destructive validation;
- no destructive authority before separately authorized C4-II-B;
- no hidden dependency/packaging/test-bypass decision;
- local-first nontechnical product workflow.

## PR discipline

Every slice is a separate small PR with Scope, Non-goals, Architecture
constraints, Backend/Frontend requirements as applicable, Tests, Acceptance
criteria, exact changed-path review, exact-head smoke appropriate to the slice,
independent audit and P0=0/P1=0/P2=0 before merge.

## After A1

Even after A1 merges, A2 remains blocked until lifecycle/project memory records
the reviewed A1 head and merge evidence from updated `main`. C4-II-B remains
separately not authorized throughout A1–A4.
