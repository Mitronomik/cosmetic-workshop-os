# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-08`

This is the compact authority for current implementation lifecycle and authorization. ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction.

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED
C1 — COMPLETED
C2 — COMPLETED
C3 — COMPLETED — MERGED, EXACT-HEAD VERIFIED AND HARDENED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
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

## Verified A3 closure / A4 authorization baseline

PR #178:
- reviewed head `b0de148032d9b3d2f9912298897f8649c9b1692b`;
- merge `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`;
- A3 14, A2 28, A1 17, C4-I 514, full backend + launcher: 2457 passed;
- native-picker smoke PASS;
- independent audit P0=0 / P1=0 / P2=0.

PR #179:
- reviewed head `72b04510efd6d1f104369a450ed1c4d4dfe063ad`;
- merge `52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf`;
- lifecycle checker PASS;
- exactly 12 docs/state/checker paths;
- A3 closed and only A4 authorized.

The current A4 branch starts directly from merge `52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf`.

## Closed A1/A2/A3 boundaries

A1 remains the single non-destructive candidate-preparation authority and reuses C4-I intake/staging/validation. A2 remains exact loopback/Origin/Host, one-use bootstrap, run token, no-store/narrow CORS, 15s/60s liveness, strict command ordering and generation-gated worker publication. A3 remains the launcher-owned exact `/usr/bin/osascript` picker with fixed `choose file`, typed cancel, launcher-private absolute path and owned child terminate/reap.

## A4 current implementation — browser session and Restore workspace

A4 implements only presentation/session behavior selected by ADR 0018.

### Launcher handoff

`launcher/restore/browser_handoff.py` creates a browser-only copy of `RuntimeConfig` whose local frontend URL carries:

```text
#cw-control=<ephemeral-port>:<one-use-bootstrap-token>
```

No query parameter is used. The ordinary runtime config is not mutated. If a safe fragment cannot be built, the control plane is closed and the ordinary product still opens without Restore authority.

### SPA bootstrap and secret lifetime

`frontend/src/restore-control-entry.ts` is loaded before `main.js`. It synchronously captures and removes only the `#cw-control` fragment before the shell resolves the route. The module-level capture binding is then cleared after starting the exchange.

The browser sends the one-use capability only as JSON to `POST /v1/bootstrap`. Successful bootstrap stores only:

- `control_origin`;
- opaque `run_id`;
- run-scoped session token;

in `sessionStorage`. No Restore secret is written to `localStorage`, query parameters or backend business API state.

### Reload and strict command replay

ADR 0018 permits only the run-scoped descriptors above in `sessionStorage`. The browser therefore keeps non-secret protocol replay metadata in same-tab `history.state`:

- next expected `command_seq`;
- at most one pending non-destructive command `{action, requestId, commandSeq}`.

This is browser retry metadata, not launcher authority. On a network-uncertain mutation, the exact same request ID and sequence is retried. A successful HTTP command reply advances the next sequence even when its business result is a typed no-op/rejection, matching the closed A2 consume-before-preconditions rule.

On reload, stored session descriptors are re-proved with `GET /v1/state`. If history replay metadata is absent, mutation may initialize at sequence 1 only when launcher state proves pristine `idle / generation=0`; after any prior generation the browser fails closed and asks the user to restart the application.

### Browser runtime and UI

A4 provides:

- nested `/backups/restore`, owned by the existing `Резервные копии` shell section;
- a human-readable secondary entry action from `/backups`;
- exact-origin Bearer requests with `credentials: omit`, `cache: no-store`, `referrerPolicy: no-referrer`;
- 15-second heartbeat and authenticated state polling while selection/validation is active;
- select/cancel/reselect over existing A2 endpoints only;
- exact response-shape validation: unknown DTO fields are rejected, including accidental path-bearing fields;
- Russian loading/unavailable/network/pending/selecting/validating/accepted/rejected/cancelled/technical-failure presentation;
- fail-closed open/restart guidance when launcher session authority is absent or protocol replay cannot be proved;
- no destructive confirmation/execute action.

`frontend/src/main.ts` remains byte-identical at Git blob `ea98a76638bddcb5a92b9ba31941508f8a816d42`; A4 is isolated in `restore-control-*` modules rather than expanding the shell monolith.

## A4 hard prohibitions

A4 must not add browser-controlled absolute paths, `<input type="file">`, file bytes, upload/blob/bookmark/handle authority, `localStorage` token persistence, ordinary FastAPI Restore mutation, WebSocket/generic launcher commands, `execute_restore(...)`, durable Restore phases, `before_restore` safety copy, working-DB replacement/migration, rollback/recovery mutation or Restore AuditLog.

C4-II-B remains separately not authorized.

## A4 verification assets

- `launcher/tests/test_restore_browser_handoff.py`;
- updated `launcher/tests/test_restore_control_runtime.py`;
- `frontend/test/restore-control.test.mjs`;
- `frontend/tsconfig.test.restore-control.json`;
- `frontend/scripts/smoke-restore-control-client.mjs`;
- `scripts/smoke_restore_browser_session.py`.

The exact-head smoke builds/tests the frontend, drives the real browser-session TypeScript runtime through a live launcher A2 control plane, production A3 adapter process seam and real A1/C4-I validation, then proves source/working DB/AuditLog/durable Restore state remain unchanged.

## Exact-head verification gate

A4 is not `DONE` until the final published head passes:

```text
clean checkout
→ git diff --check 52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf...HEAD
→ python3 scripts/check_documentation_lifecycle.py
→ npm run build
→ npm run test:restore-control
→ launcher A4 targeted tests
→ closed A3/A2/A1 regressions
→ C4-I Restore regression
→ full backend + launcher regression
→ relevant frontend regression suite
→ python3 scripts/smoke_restore_browser_session.py --expected-head <HEAD>
→ desktop + narrow-screen + keyboard/focus review of /backups and /backups/restore
→ clean status/head
→ independent P0/P1/P2 audit
```

No PASS is claimed until these run on the final published A4 head.

## Successor gate

C4-II-B remains **PLANNED — NOT AUTHORIZED**. A4 merge does not itself authorize destructive Restore. A separate post-merge lifecycle/architecture gate is required before any C4-II-B implementation.
