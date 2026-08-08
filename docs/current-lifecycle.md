# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-08`

This document is the compact authority for current implementation lifecycle and PR sequencing. ADR 0016 remains authoritative for destructive Restore; ADR 0018 remains authoritative for launcher-owned control, picker and browser-session architecture.

## Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
PR #177 — MERGED — A2 CLOSED / A3 AUTHORIZED
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
macOS packaging — NOT COMPLETED
Product release readiness — NOT CLAIMED
```

A4 is the **only authorized next runtime slice**. C4-II-B remains separately not authorized.

## A3 closure evidence

PR #178 final reviewed head:
`b0de148032d9b3d2f9912298897f8649c9b1692b`

Merge/new main:
`9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`

The runtime tree was fully exercised at `4ae65f77c00e4db51bc8df7c057c583e2ad7c2bc`; the final reviewed head differed only by one documentation file (+2/-1), then passed the final exact-head bridge.

Accepted evidence:

- `git diff --check`: PASS;
- A3 targeted native-picker tests: 14 passed;
- closed A2 regression: 28 passed;
- A1 regression: 17 passed;
- C4-I Restore regression: 514 passed, 76 deselected;
- full backend + launcher: 2457 passed;
- exact-head A3 native-picker smoke: PASS;
- final documentation lifecycle checker: PASS;
- final exact-head A3 fast regression: 14 passed;
- clean status/head before and after;
- independent audit: P0=0 / P1=0 / P2=0.

## Closed A1/A2/A3 boundaries

A1 remains the sole launcher-owned non-destructive candidate-preparation authority.

A2 remains the exact-run loopback control/session authority: exact `127.0.0.1:<ephemeral>`, exact Host/configured Origin, atomic bootstrap, run-scoped token, no-store/narrow CORS, 15s heartbeat / 60s expiry, strict `command_seq`, responsive state/heartbeat/cancel, generation-gated publication and stale A2→A1 proof-race hardening.

A3 remains the production launcher-owned native picker boundary:

- `MacOSNativeSourceSelectionAdapter`;
- `OSASCRIPT_PATH = Path("/usr/bin/osascript")`;
- fixed Standard Additions `choose file` AppleScript;
- `shell=False`, no `System Events`, no user-controlled executable script text;
- typed error `-128` cancellation;
- absolute POSIX path only in launcher memory;
- owned terminate/reap and kill/reap fallback;
- cancel/expiry/close cannot leave picker authority or an owned child behind;
- selected path flows only through A2 into A1/C4-I validation.

## Authorized A4 boundary — browser Restore screen only

A4 may implement the browser presentation/session slice selected by ADR 0018:

- nested SPA route `/backups/restore` and human-readable entry from `/backups`;
- first production launcher browser handoff carrying only control port + one-use bootstrap capability in URL fragment, conceptually `#cw-control=<ephemeral-port>:<bootstrap-token>`;
- SPA consumes the fragment, exchanges it via `POST /v1/bootstrap`, then immediately removes the fragment with `history.replaceState(...)` or equivalent;
- only `control_origin`, optional opaque `run_id`, and run-scoped session token may live in `sessionStorage`; never `localStorage`;
- reload uses retained descriptors + `GET /v1/state`;
- explicit invalid-token/run-mismatch clears stale descriptors;
- heartbeat remains 15 seconds; launcher expiry remains 60 seconds;
- select/cancel/reselect use the existing A2 commands, random request IDs and monotonic `command_seq`;
- presentation of typed safe states from A1/A2/A3 only;
- missing/invalid launcher session fails closed with nontechnical open/restart guidance.

### A4 hard prohibitions

A4 must not:

- accept browser filesystem path, `source_path`, file bytes, upload/blob, bookmark/handle or `<input type="file">` fallback;
- place bootstrap/session token in query parameters, logs, persistent storage or backend API payloads;
- invent an ordinary FastAPI Restore mutation endpoint or alternate transport;
- add destructive confirm/execute command or call `execute_restore(...)`;
- create durable Restore phases, `before_restore` safety copy, working-DB replacement/migration, rollback/recovery mutation or Restore AuditLog;
- authorize C4-II-B.

## Successor gate

A4 must be exact-head verified, merged and lifecycle-closed before any successor is considered. C4-II-B requires a separate explicit authorization decision and retains all ADR 0016 re-proof/safety-copy/destructive gates.

Protected history under `docs/history/` remains byte-identical.