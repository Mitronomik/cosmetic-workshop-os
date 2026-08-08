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
PR #176 reviewed A2 head — 681cb4050bec082db6b637285590e232880af739
PR #176 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
```

## Current slice status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

Each later slice starts from updated `main`; never branch from an unmerged or
not-yet-closed predecessor.

## A1 — Validation-session core — CLOSED

A1 merged in PR #174 and remains the single candidate-preparation authority. It
directly reuses C4-I `open_selected_source(...)`, held-source identity/digest/
sidecar proof, `stage_source(...)` and `validate_staged_candidate(...)`.

## A2 — Exact-run launcher control plane — CLOSED

PR #176 completed A2 at reviewed head
`681cb4050bec082db6b637285590e232880af739`, merged as
`90a14dd9a11b83bc31a40e1d3fb9523f41772b88`.

Final evidence:

- lifecycle checker: PASS;
- stale-A1-authority race regression: 2 passed;
- all A2 targeted tests: 28 passed;
- A1 regression: 17 passed;
- C4-I Restore regression: 514 passed, 62 deselected;
- full backend + launcher: 2443 passed;
- exact-head direct-local-HTTP smoke: PASS;
- independent audit: P0=0 / P1=0 / P2=0.

A2 durable boundary:

- exact `127.0.0.1:<ephemeral>` concurrent control server;
- exact Host + configured local frontend Origin;
- atomic one-use bootstrap + run-scoped session token;
- no wildcard CORS/cookie authority; no-store responses;
- 15s heartbeat / 60s inactivity expiry;
- strict monotonic `command_seq` and idempotent same-request retry;
- one long-work owner with responsive heartbeat/state/cancel;
- A1 proof/generation invalidation on reselect/cancel/expiry/close;
- stale A2→A1 begin race hardened before worker quiescence;
- runtime order proved backend → control → ordinary browser and
  control close → backend stop.

Production A2 still uses `UnavailableSourceSelectionAdapter`, so no production
source path exists until A3. Production browser navigation remains unchanged
until A4.

## A3 — Native macOS picker integration — AUTHORIZED NEXT

### Goal

Replace only the production `picker_unavailable` source-selection seam with the
launcher-owned native macOS picker selected by ADR 0018, while preserving the
closed A2 control/session contract and merged A1 validation authority.

### Authorized scope

- owned short-lived `/usr/bin/osascript` child;
- macOS Standard Additions `choose file`;
- fixed executable AppleScript;
- no user-controlled text interpolation into AppleScript;
- no `shell=True`;
- no `System Events` automation;
- typed ordinary picker cancellation;
- absolute POSIX path returned only inside launcher memory;
- picker process ownership, termination and wait/quiescence;
- cancel/expiry signal from existing A2 worker must terminate the owned picker;
- integrate through existing A2 `SourceSelectionAdapter` contract;
- selected path passes only to merged A1 `prepare_restore_candidate(...)`;
- no new Python/application dependency.

### Process ownership rules

The picker adapter owns exactly one child for one A2 selection worker. It must
not detach a process, spawn via shell, or leave an unaccounted child after
cancel/expiry/close. Cancellation invalidates control/A1 authority immediately;
process cleanup then quiesces the owned child before the selection worker exits.

### Path privacy rules

The absolute selected POSIX path is launcher-private. It may appear only in the
launcher-internal picker result/A1 retained proof path. Browser/control DTOs,
HTTP payloads, URLs, logs and user-visible errors must not expose it.

### A3 automated proof

At minimum prove:

1. exact executable `/usr/bin/osascript`;
2. fixed Standard Additions `choose file` script;
3. no `shell=True`, `System Events` or user-controlled script interpolation;
4. success yields launcher-private absolute POSIX path;
5. ordinary user cancel yields typed cancel;
6. cancel/expiry terminates owned child and waits for quiescence;
7. technical picker failure maps to safe typed failure without raw path/stderr;
8. browser/control request and state remain pathless;
9. real A2 selection coordinator receives the adapter result;
10. selected path flows through real merged A1 validation;
11. stale A2→A1 proof-race hardening remains green;
12. product browser URL remains unchanged;
13. no durable Restore/safety-copy/AuditLog/working-DB mutation;
14. A2/A1/C4-I/full regressions remain green.

Tests may inject a narrow process runner/factory to avoid unattended GUI dialogs.
Production code must still execute the exact macOS command when used normally.

### A3 exact-head smoke

Use the production A3 adapter boundary with a controlled process seam or
launcher-owned harness to prove:

```text
A2 select
→ native-picker adapter contract
→ launcher-private selected path
→ real A1/C4-I validation
→ typed non-destructive control state
```

The smoke must not add a browser path/file bypass and must not mutate durable
Restore/working database state.

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
- new dependency or packaging implementation;
- cloud sync/OCR/multiuser/advanced analytics.

## A4 — Browser Restore screen and non-destructive E2E flow — BLOCKED

### Entry gate

A3 must merge and be independently exact-head verified, then lifecycle-closed
from updated `main`.

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

Every A3/A4 PR preserves:

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
