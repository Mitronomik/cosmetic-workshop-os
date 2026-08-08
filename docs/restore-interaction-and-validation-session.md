# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-08`

## Current lifecycle

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
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
                           ├── A3 launcher-owned native picker
                           └── A1 validation worker
                         → C4-I intake/staging/validation
```

Browser owns presentation only. Launcher owns picker/path/control and all future destructive authority.

## Closed A1/A2/A3 boundaries

A1 remains the sole candidate-preparation authority and creates no durable Restore phase, safety copy, working-DB mutation or Restore AuditLog.

A2 remains the exact-run control/session authority with exact Host/Origin, atomic one-use bootstrap, run-scoped token, `Cache-Control: no-store`, 15-second heartbeat, 60-second expiry, strict command ordering and generation-gated publication.

A3 is closed at reviewed head `b0de148032d9b3d2f9912298897f8649c9b1692b`, merged as `9d95b0c39c4abd05d5a574c6cd8574b8e457f36b`. Its native picker remains `OSASCRIPT_PATH = Path("/usr/bin/osascript")`, fixed Standard Additions `choose file`, `shell=False`, no `System Events`, typed error `-128` cancellation, launcher-private POSIX path and owned terminate/reap + kill/reap fallback.

## A3→A4 browser seam — AUTHORIZED

A4 owns the first production browser bootstrap/session integration.

Launcher creates an exact-run bootstrap capability and opens the ordinary browser with control port + bootstrap only in the URL fragment, conceptually:

```text
http://127.0.0.1:5173/#cw-control=<ephemeral-port>:<bootstrap-token>
```

The fragment is never a query parameter and is not sent to the frontend server.

SPA must:

1. parse only the intended `cw-control` fragment grammar;
2. exchange it once via existing `POST /v1/bootstrap`;
3. immediately remove the fragment with `history.replaceState(...)` or equivalent;
4. retain only `control_origin`, optional opaque `run_id`, and run-scoped session token in `sessionStorage`;
5. never store token in `localStorage`;
6. use an explicit authorization header to the exact control origin;
7. on reload use descriptors + `GET /v1/state`;
8. on explicit invalid-token/run-mismatch clear stale descriptors;
9. send authenticated heartbeat at the established 15-second cadence;
10. use existing A2 select/cancel commands with random request IDs and monotonic `command_seq`.

## Screen ownership

A4 may add nested route `/backups/restore` and a human-readable entry from `/backups`. Missing/invalid launcher control session must fail closed with guidance to open/restart the application normally.

No `<input type="file">`, browser upload, path field or FastAPI Restore fallback is allowed.

## Path privacy

Selected absolute path stays inside launcher. Browser/control DTOs may show only safe filename/label and typed compatibility/state. Raw osascript stderr, SQLite errors, stack traces, internal paths and migration IDs remain outside browser presentation.

## A4 remains non-destructive

A4 exposes no destructive confirm/execute command. It must not call `execute_restore(...)`, create a `before_restore` safety copy, write durable Restore phase/state, replace/migrate the working DB, perform rollback/recovery mutation or write Restore AuditLog.

C4-II-B remains separately not authorized.

## Successor gate

A4 must pass frontend/session/security tests, closed A3/A2/A1/C4-I regressions, exact-head non-destructive browser smoke and independent P0=0 / P1=0 / P2=0 audit before merge. Lifecycle closes again after merge before any successor authorization.