# C4-II-A implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-08`

This document bounds C4-II-A only. It does not change ADR 0018 and does not authorize C4-II-B destructive execution.

## Merged baseline

```text
PR #176 / A2 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
PR #177 / A3 authorization merge — e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263
PR #178 reviewed A3 head — b0de148032d9b3d2f9912298897f8649c9b1692b
PR #178 / A3 merge — 9d95b0c39c4abd05d5a574c6cd8574b8e457f36b
```

## Current slice status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
```

## Closed A3 — native macOS picker

A3 is closed at reviewed head `b0de148032d9b3d2f9912298897f8649c9b1692b`, merged as `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`.

Final accepted evidence: A3 14, A2 28, A1 17, C4-I 514, full backend+launcher 2457, exact-head native-picker smoke PASS, lifecycle PASS, clean status/head and P0=0 / P1=0 / P2=0.

Closed A3 contract remains:

- `MacOSNativeSourceSelectionAdapter`;
- exact `OSASCRIPT_PATH = Path("/usr/bin/osascript")`;
- fixed `use scripting additions` / `choose file` AppleScript;
- typed error `-128` cancel;
- `shell=False`, no `System Events`, no user-controlled script interpolation;
- launcher-private absolute POSIX path;
- terminate/reap + kill/reap fallback on cancel/expiry/close;
- existing A2 adapter seam → existing A1/C4-I validation;
- no new dependency.

## A4 — Browser Restore screen and non-destructive E2E flow — AUTHORIZED NEXT

### Scope

A4 may implement only the browser presentation/session layer selected by ADR 0018:

1. canonical nested route `/backups/restore`;
2. explicit human-readable “restore from backup” action from `/backups`;
3. first production launcher bootstrap handoff in URL fragment only:
   `#cw-control=<ephemeral-port>:<bootstrap-token>`;
4. frontend atomic bootstrap exchange through existing `POST /v1/bootstrap`;
5. immediate fragment removal with `history.replaceState(...)` or equivalent;
6. `sessionStorage` only for `control_origin`, optional opaque `run_id`, and run-scoped session token; never `localStorage`;
7. explicit Authorization header to the exact launcher control origin;
8. reload via `GET /v1/state`;
9. heartbeat at 15 seconds while session is active; existing 60-second launcher expiry remains authority;
10. select/cancel/reselect through existing A2 commands with >=128-bit random request IDs and strictly monotonic `command_seq`;
11. typed presentation-safe states and nontechnical fail-closed guidance;
12. real non-destructive E2E chain: browser → A2 control → A3 picker → A1/C4-I validation.

### Browser/filesystem seam

Browser remains presentation only. It must never submit `path`, `source_path`, file bytes, upload/blob, bookmark/handle or equivalent filesystem authority. No `<input type="file">` fallback.

### Bootstrap/session privacy

Bootstrap/session material must never be placed in query parameters, backend API payloads, logs or persistent storage. Fragment is consumed once and removed immediately. Session token is never written to `localStorage`.

### A4→C4-II-B seam

A4 is still non-destructive. It must not add destructive confirmation/execute, `execute_restore(...)`, durable Restore phase/state, `before_restore` safety copy, working-DB replacement/migration, rollback/recovery mutation or Restore AuditLog.

## Required A4 tests

At minimum prove:

- `/backups/restore` exact route and `/backups` entry;
- fragment parser accepts only the intended `cw-control` bootstrap grammar;
- query transport is absent;
- fragment is removed immediately after bootstrap attempt;
- bootstrap capability is not persisted;
- only permitted run descriptors enter `sessionStorage`; no `localStorage` token;
- reload success through `GET /v1/state`;
- explicit invalid token/run mismatch clears stale descriptors;
- missing launcher session fails closed with no browser file fallback;
- heartbeat lifecycle and cleanup;
- request IDs and monotonic `command_seq` behavior at the frontend client seam;
- select/cancel/reselect typed UX;
- browser DTO stays pathless even when picker/internal errors contain paths;
- production browser launch uses fragment only and preserves exact local origin;
- A3/A2/A1/C4-I regressions remain green;
- no destructive C4-II-B behavior.

## A4 exact-head smoke

A4 must include a real non-destructive macOS/browser smoke that exercises the production bootstrap/session flow and route while proving source/working DB/AuditLog/durable Restore state remain unchanged.

## PR discipline

A4 is a separate small PR. Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests and Acceptance criteria are mandatory. No unrelated changes. Merge only after exact-head tests/smoke and independent P0=0 / P1=0 / P2=0 audit.