# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-08`

Normative sources: ADR 0016 for destructive Restore; ADR 0018 for launcher control/picker/exact-run browser session; current lifecycle and C4-II-A slice plan for implementation status.

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Selected architecture

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → A2 action/session coordinator
                           ├── A3 native picker
                           └── A1 validation worker
                         → C4-I intake/staging/validation
```

Browser owns presentation only. Launcher owns loopback control, picker, selected absolute path, candidate proof and all future destructive authority.

## Closed A1/A2/A3 boundary

A1 owns candidate preparation and validation reuse. A2 owns exact Host/Origin, one-use bootstrap, run session, no-store CORS boundary, 15s heartbeat / 60s expiry, strict command ordering, idempotent retry and generation-gated publication. A3 owns exact `/usr/bin/osascript` + fixed Standard Additions `choose file`, typed Cancel, absolute POSIX path and picker-child quiescence.

## A3→A4 browser seam — CURRENT IMPLEMENTATION

### Production handoff

After the ordinary backend is proved ready and the launcher control plane is bound, A4 creates a browser-only `RuntimeConfig` copy with:

```text
http://127.0.0.1:<frontend-port>#cw-control=<ephemeral-port>:<bootstrap-token>
```

The bootstrap capability is never put in a query parameter. If handoff construction is unsafe, the control plane is closed and the ordinary product opens without Restore authority.

### Bootstrap consumer

`restore-control-entry.js` loads before the ordinary shell module. It captures only the exact `#cw-control` fragment and removes it synchronously using `history.replaceState(...)`. Unrelated legacy hashes are not consumed. Malformed Restore fragments are removed and fail closed.

The one-use capability is exchanged through `POST /v1/bootstrap`. The module-level capture binding is cleared immediately after the async exchange starts, so the bootstrap secret is not retained for the lifetime of the page.

Successful bootstrap stores only these run-scoped descriptors in `sessionStorage`:

- `control_origin`;
- `run_id`;
- session token.

The token is never stored in `localStorage`, a URL, a query, backend API state or product log.

### Reload and replay state

Reload reuses the stored descriptors only after authenticated `GET /v1/state` proves the same run. Invalid session or run mismatch clears the descriptors.

Strict A2 commands require a sequence that the browser must not guess. Non-secret same-tab retry metadata therefore lives in `history.state`:

```text
nextCommandSeq
pending { action, requestId, commandSeq } | null
```

This metadata cannot authorize filesystem or destructive work. A pending command records a network-uncertain non-destructive request and may only be retried with the exact same ID and sequence. New commands remain disabled until the pending command is resolved.

When reload descriptors exist but replay metadata is absent, sequence 1 is allowed only after the launcher proves pristine `idle / generation=0`. Any prior generation without replay metadata fails closed with restart guidance.

### Browser control requests

A4 uses only the closed A2 vocabulary:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

Authenticated requests use the exact control origin, Bearer Authorization header, `credentials: omit`, `cache: no-store` and `referrerPolicy: no-referrer`. Heartbeat remains 15 seconds. Active selecting/validating states are also polled so browser presentation follows launcher truth.

Response parsing is allowlist-based. State DTOs with unknown fields are refused so an accidental future `source_path`, staged path or internal field cannot silently become browser-visible.

## `/backups/restore` presentation

A4 adds a nested screen under the existing `Резервные копии` section and a secondary action from `/backups`. The UI explains that:

- file selection happens in the native macOS dialog;
- browser upload is not used;
- selection/validation does not modify current workshop data;
- accepted validation means only that the copy passed the non-destructive candidate check;
- final Restore has not started;
- no destructive action is available yet.

The screen handles unavailable, network uncertainty, pending retry, selecting, validating, accepted, rejected, cancelled and technical-failure states with Russian nontechnical copy. No absolute path or raw technical error is rendered.

`frontend/src/main.ts` remains unchanged; the A4 entry module integrates by exact nested route and bounded DOM ownership rather than moving Restore state into the shell monolith.

## Non-destructive proof

`scripts/smoke_restore_browser_session.py` builds/tests the frontend and drives the real TypeScript session runtime through a live A2 control plane, production A3 process adapter seam and real A1/C4-I validation. It verifies source bytes, working DB bytes, AuditLog count and durable Restore workspace remain unchanged.

## Future C4-II-B re-proof

C4-II-B remains separately not authorized. Before any destructive Restore it must reopen/re-prove the launcher-private original, compare `SourceIdentity`, recompute SHA-256, re-check sidecars, restage/revalidate, prove backend exclusion, create mandatory `before_restore` safety copy and only then enter C4-I execution. Browser session, history replay, filename and accepted presentation are never destructive authority.
