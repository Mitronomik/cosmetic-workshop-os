# C4-II-A implementation authorization and slice plan

Status: **NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-08`

This document bounds `C4-II-A — Launcher Restore source selection and non-destructive validation presentation`. It does not change ADR 0018 and does not authorize C4-II-B destructive execution.

## Merged baseline

```text
PR #176 / A2 merge — 90a14dd9a11b83bc31a40e1d3fb9523f41772b88
PR #177 / A3 authorization merge — e7ab91dd8e0c11da2cc0b2c30bf41d1dec89f263
PR #178 / A3 merge — 9d95b0c39c4abd05d5a574c6cd8574b8e457f36b
PR #179 reviewed closure head — 72b04510efd6d1f104369a450ed1c4d4dfe063ad
PR #179 / A4 authorization merge — 52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf
```

## Current slice status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B — PLANNED — NOT AUTHORIZED
```

## Closed predecessors

A1 owns non-destructive candidate preparation and C4-I validation reuse. A2 owns exact-run loopback authentication, liveness, strict request replay/sequence semantics and worker publication. A3 owns the native macOS picker, absolute source path and picker-child lifecycle.

## A4 — Browser Restore screen and non-destructive E2E flow — CURRENT IMPLEMENTATION

### Goal

Connect the existing browser product surface to the already-merged launcher control/picker/validation chain without giving the browser filesystem or destructive authority.

### Implemented launcher handoff

- `launcher/restore/browser_handoff.py` builds a browser-only config copy;
- exact local frontend origin is required;
- the only bootstrap transport is fragment `#cw-control=<ephemeral-port>:<bootstrap-token>`;
- no query transport;
- the original frozen runtime config is unchanged;
- a handoff construction failure closes the control plane and opens ordinary product UI without Restore controls.

### Implemented SPA session contract

`frontend/src/restore-control-contract.ts` and `restore-control-runtime.ts` implement:

1. exact `#cw-control` parsing;
2. synchronous fragment removal with `history.replaceState(...)` before shell route resolution;
3. one-use `POST /v1/bootstrap`;
4. storage of only `control_origin`, `run_id` and session token in `sessionStorage`;
5. no `localStorage` token persistence;
6. exact loopback control-origin validation;
7. Bearer token only in the Authorization header;
8. `credentials: omit`, `cache: no-store`, `referrerPolicy: no-referrer`;
9. reload via authenticated `GET /v1/state`;
10. invalid-session/run-mismatch descriptor cleanup;
11. 15-second heartbeat over merged 60-second A2 expiry;
12. exact response allowlists that reject unknown fields rather than accepting accidental path/internal fields;
13. cryptographic 128-bit request IDs;
14. strict monotonic `command_seq` handling aligned with closed A2 semantics;
15. state polling while selecting/validating;
16. no source path/file bytes/upload/bookmark/handle field.

### Reload/retry clarification

The sessionStorage allowlist stays exactly the three run-scoped descriptors selected by ADR 0018. Non-secret command replay metadata is therefore retained in same-tab `history.state`, never treated as launcher authority:

```text
version
runId
nextCommandSeq
pending { action, requestId, commandSeq } | null
```

The pending command exists only when the browser cannot know whether a non-destructive request reached A2. Retry uses the exact same request ID/sequence, so closed A2 idempotency decides the outcome. New commands are disabled until that uncertainty is resolved.

If a reload has valid launcher session descriptors but no replay metadata, command sequence 1 is reconstructed only from a proved pristine `idle / generation=0` state. Otherwise the browser fails closed with application-restart guidance instead of guessing the next sequence.

### UI implementation

- `/backups/restore` is an exact nested route under the existing `Резервные копии` shell section;
- `/backups` gets a secondary human-readable Restore entry action;
- `restore-control-entry.ts` is loaded before `main.js` and overlays only the bounded backup/Restore workspace;
- `frontend/src/main.ts` stays byte-identical;
- loading, unavailable, network-uncertain, pending-command, selecting, validating, accepted, rejected, cancelled and technical-failure states are human-readable Russian copy;
- accepted state explicitly says working data is unchanged and final Restore has not started;
- no destructive button is rendered.

### A4 verification assets

- `frontend/test/restore-control.test.mjs`;
- `launcher/tests/test_restore_browser_handoff.py`;
- updated launcher runtime integration tests;
- `frontend/scripts/smoke-restore-control-client.mjs`;
- `scripts/smoke_restore_browser_session.py`.

The smoke drives real A4 TypeScript session code → live A2 loopback control → production A3 adapter seam → real A1/C4-I validation and then proves source, working database, AuditLog and durable Restore state are unchanged.

### A4 non-goals

A4 must not implement:

- browser filesystem path/file/upload/bookmark/handle authority or `<input type="file">` fallback;
- secrets in query parameters, logs, backend business API or persistent storage;
- ordinary FastAPI Restore mutation endpoint;
- WebSocket/generic launcher command surface;
- destructive confirmation/execute or `execute_restore(...)`;
- durable Restore operation/phase;
- `before_restore` safety copy;
- working-database replacement/migration;
- rollback/recovery mutation;
- Restore AuditLog;
- packaging/cloud/OCR/multiuser/advanced analytics.

## C4-II-B — PLANNED — NOT AUTHORIZED

Future C4-II-B must separately reopen/re-prove the launcher-private original path, compare `SourceIdentity`, recompute SHA-256, re-check sidecars, restage/revalidate, prove backend exclusion, create mandatory `before_restore` safety copy and only then enter C4-I destructive execution. Browser state, token, filename and history replay metadata are never destructive authority.

## PR discipline

A4 remains one independently reviewed PR. Exact changed-path review, build/tests, cross-layer smoke, UI desktop/narrow/keyboard smoke and independent P0=0/P1=0/P2=0 are required before merge. A separate lifecycle/authorization decision follows before C4-II-B.
