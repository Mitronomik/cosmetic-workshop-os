# C4-II-A implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-08`

This document bounds `C4-II-A — Launcher Restore source selection and non-destructive validation presentation`.
It does not change ADR 0018 and does not authorize C4-II-B destructive execution.

## Merged authorization baseline

```text
PR #172 / CR-011 merge — 998596560db6780a677bdec363d1fd19db30c1b6
PR #173 merge — aaedf2735660fb92eb627f7eeab327437d459b56
PR #174 / A1 merge — 504e776508c940554b3ee8659a201af21db8303c
PR #175 / A2 authorization merge — 636645ece744752f6a753ae5a25a05297fd34e10
PR #176 / A2 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
PR #177 reviewed closure head — d767b957cb3debae584709f2bbadafebd8dd6a9e
PR #177 / A3 authorization merge — e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263
```

## Current slice status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

Each later slice starts from updated `main`; never branch from an unmerged or
not-yet-closed predecessor.

## A1 — Validation-session core — CLOSED

A1 remains the single candidate-preparation authority and directly reuses C4-I
source intake/staging/validation.

## A2 — Exact-run launcher control plane — CLOSED

PR #176 completed A2 at reviewed head
`681cb4050bec082db6b637285590e232880af739`, merged as
`90a14dd9a11b83bc31a40e1d3fb9523f41772b88`.

Final A2 proof: race 2, A2 28, A1 17, C4-I 514, full 2443, smoke PASS,
independent P0=0 / P1=0 / P2=0.

A2 durable boundary remains exact loopback/Host/Origin, atomic bootstrap, run
token, no-store/narrow CORS, 15s/60s liveness, strict command ordering, one
long-work owner, responsive heartbeat/state/cancel and stale-proof hardening.

## A3 — Native macOS picker integration — CURRENT IMPLEMENTATION

### Goal

Replace only the production unavailable source-selection seam with the
launcher-owned native macOS picker selected by ADR 0018, while preserving the
closed A2 control/session contract and merged A1 validation authority.

### Implemented in the current changeset

- `launcher/restore/macos_picker.py` implements
  `MacOSNativeSourceSelectionAdapter`;
- exact `/usr/bin/osascript` production helper;
- fixed `use scripting additions` + `choose file` AppleScript;
- no user-controlled AppleScript interpolation;
- `shell=False`; no `System Events`;
- AppleScript error `-128` becomes typed ordinary cancellation through an internal
  sentinel independent of localized stderr;
- successful output must be an absolute POSIX path and remains launcher-private;
- picker polls the existing A2 `cancel_event`;
- cancel/expiry/close terminates and reaps the owned child; timeout falls back to
  kill + reap;
- non-macOS or missing exact helper returns typed unavailable;
- picker technical failures remain launcher-internal and the closed A2 worker
  emits its fixed safe `selection_failed` result;
- production `launcher/runtime.py` injects the native adapter into the existing
  `RestoreControlPlane`; direct/test construction keeps the closed A2 unavailable
  default;
- selected path passes only to merged A1 `prepare_restore_candidate(...)`;
- no new Python/application dependency.

### Process ownership rules

The picker adapter owns exactly one child for one A2 selection worker. It never
detaches or spawns through a shell. Cancellation invalidates A2/A1 authority
immediately; process cleanup then quiesces/reaps the owned child before the
selection worker exits.

### Path privacy rules

The selected absolute POSIX path is launcher-private. Browser/control request,
state, URL and user-visible failures remain pathless. C4-I/A1 remains acceptance
authority; filename/type hints are presentation only.

### A3 automated proof

Targeted tests cover:

1. exact `/usr/bin/osascript` contract and fixed AppleScript;
2. no shell/System Events/user interpolation;
3. typed user cancellation;
4. pre-spawn cancellation;
5. terminate/reap and kill fallback;
6. unavailable helper/platform;
7. nonzero/empty/non-absolute result failure;
8. preservation of valid newline-containing POSIX paths;
9. control cancel and 60s expiry physically terminate owned child;
10. selected path passes through real A2 session to real A1 validation;
11. production runtime injects A3 adapter.

### A3 exact-head smoke

`scripts/smoke_restore_native_picker.py`:

```text
exact-head + clean checkout
→ non-interactive exact /usr/bin/osascript probe
→ production A3 adapter with launcher-owned process seam
→ real A2 loopback control
→ launcher-private selected path
→ real A1/C4-I validation
→ safe non-destructive state
→ prove source/working DB/AuditLog/durable Restore unchanged
```

The process seam avoids requiring an unattended test to click a modal GUI dialog;
production adapter command construction remains exact and is asserted by the
smoke.

### A3 non-goals

A3 must not implement:

- `/backups/restore` or frontend Restore UI;
- production browser bootstrap-fragment handoff;
- browser path/file/upload/handle authority;
- destructive confirmation/execute or `execute_restore(...)`;
- durable Restore operation/phase or `before_restore` safety copy;
- working-database replacement/migration;
- rollback/recovery mutation or Restore AuditLog;
- ordinary FastAPI Restore mutation endpoint;
- WebSocket/generic localhost command server;
- new dependency or packaging implementation.

## A4 — Browser Restore screen and non-destructive E2E flow — BLOCKED

A4 may open only after A3 merges, passes independent exact-head verification and
is lifecycle-closed from updated `main`. A4 will own `/backups/restore`, the first
production `#cw-control` fragment handoff/removal, `sessionStorage` and browser UX.
It still will not authorize destructive C4-II-B.

## Cross-slice constraints

Every A3/A4 PR preserves ADR 0016, ADR 0018, launcher-only filesystem authority,
pathless browser presentation, closed A1/A2 semantics, ordinary FastAPI as
business API only, non-destructive C4-II-A and separately gated C4-II-B.

## PR discipline

Every slice is a separate small PR with Scope, Non-goals, Architecture
constraints, Backend/Frontend requirements, Tests, Acceptance criteria, exact
changed-path review, exact-head smoke and independent P0=0/P1=0/P2=0 before merge.
