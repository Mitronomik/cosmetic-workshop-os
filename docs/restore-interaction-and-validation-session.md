# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-08`

Normative sources:

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — selected interaction/control/picker/validation architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation plan;
- `docs/current-lifecycle.md` — current lifecycle authorization.

ADR 0018 architecture is unchanged by A1 closure or the current A2 implementation.

## Current lifecycle

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — PLANNED — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Selected architecture

```text
browser SPA /backups/restore
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → action/session coordinator
                           ├── launcher-owned picker adapter
                           └── validation worker
                         → C4-I intake/staging/validation
```

Browser owns presentation only. Launcher owns control, future picker, absolute
selected source path, validation-session authority and all future destructive
authority. No WebSocket, generic localhost command server, browser filesystem
authority or ordinary FastAPI Restore mutation is selected.

## A1 merged validation boundary

PR #174 merged exact-head verified A1 at
`e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5` as
`504e776508c940554b3ee8659a201af21db8303c`.

A1 remains the only candidate-preparation service:

```text
new selection generation
→ private system-temp scratch session
→ C4-I open_selected_source / HeldSource
→ C4-I stable stage_source
→ source digest + identity + sidecar re-proof
→ C4-I validate_staged_candidate read-only
→ source digest + identity + sidecar re-proof again
→ delete staged validation candidate/session scratch
→ if generation remains current, retain launcher-private SourceIdentity + SHA-256
→ return typed presentation-safe result
```

A1 creates no durable Restore operation/phase, `before_restore` safety copy,
working-DB mutation/migration, rollback/recovery mutation or Restore AuditLog.

## A2 exact-run control plane — current implementation

The current changeset implements the local control/session protocol only.

### Bind and request authority

- stdlib `ThreadingHTTPServer`-equivalent concurrent server;
- bind exactly `127.0.0.1` on OS-assigned ephemeral port;
- exact `Host = 127.0.0.1:<bound-port>`;
- exact configured local frontend Origin;
- no wildcard CORS and no credentialed cookie authority;
- duplicate/missing authority headers fail closed;
- query/unknown path and broadened request schema fail closed;
- `Cache-Control: no-store`, `Pragma: no-cache` and `nosniff` on responses;
- no access logging of bootstrap/session material.

Narrow HTTP vocabulary remains exactly:

```text
POST /v1/bootstrap
GET  /v1/state
POST /v1/heartbeat
POST /v1/restore/select
POST /v1/restore/cancel
```

There is no destructive command and no generic filesystem/shell/SQL/backend proxy.

### Bootstrap and session

- launcher creates one-use bootstrap capability using 32 random bytes;
- bootstrap compare-and-consume is atomic under session lock;
- exactly one concurrent exchange can succeed;
- consumed bootstrap capability is cleared from coordinator memory;
- successful bootstrap creates a separate 32-random-byte-class run token;
- token is explicit Bearer authority, not cookie/query authority;
- heartbeat contract is 15 seconds;
- session expires after 60 seconds without authenticated activity;
- expiry invalidates session token, selection generation and A1 retained proof.

A2 deliberately does **not** transport bootstrap capability to the production
browser. It remains launcher-private until A4 adds the fragment consumer/removal
flow.

### Concurrency and worker ownership

Selection/validation runs on one launcher-owned worker while the HTTP server stays
concurrent. Heartbeat, `GET /v1/state` and cancel remain serviceable.

Cancellation, expiry, reselection and close invalidate A1/browser authority before
a late worker can publish. Worker publication is selection-generation gated. Final
session close waits for worker quiescence before A1 service cleanup.

### Request ordering

Mutating commands carry request ID plus strict monotonic `command_seq`.

```text
exact Host/Origin
→ session auth
→ JSON + exact schema
→ validate stale/future/conflict
→ atomically consume exact expected-next sequence
→ evaluate business preconditions
→ retain safe in-progress/final reply
```

Wrong Host/Origin/auth, malformed JSON/schema, stale or future requests do not
consume the sequence. A valid expected-next command consumes it **before**
business preconditions, so `action_in_progress` or another typed business
rejection cannot later become success by replay.

Same current sequence + same request ID + same command returns retained safe
state without re-execution. Same sequence with different request ID/command fails.

## A2→A3 source-selection seam

Production A2 uses `UnavailableSourceSelectionAdapter` and returns typed
`picker_unavailable`; it obtains **no filesystem path**.

Tests and exact-head smoke may inject a launcher-owned fake adapter directly into
the control/session code. Browser/control request schema cannot contain `path`,
`source_path`, upload/blob/file bytes, bookmark/handle or equivalent filesystem
authority.

A3 later replaces the unavailable adapter with launcher-owned:

```text
/usr/bin/osascript
→ macOS Standard Additions choose file
→ absolute POSIX path returned only to launcher memory
```

No `shell=True`, `System Events`, user text interpolation or new application
dependency is authorized.

## A2→A4 browser seam

The production product-browser launch URL remains unchanged during A2.
`open_runtime_browser(...)` does not append `#cw-control`, control port, bootstrap
capability or session token.

A4 owns `/backups/restore`, first production browser fragment handoff, immediate
fragment removal, `sessionStorage` token + non-secret `control_origin`, typed UX
and real non-destructive E2E macOS smoke.

A2 exact-head smoke uses a direct authenticated local HTTP harness instead.

## Launcher runtime ownership

The current A2 runtime wiring preserves the accepted order:

```text
launcher lifecycle / recovery / startup
→ owned backend start + proved lock/socket handshake
→ start exact-run Restore control plane
→ ordinary product browser URL unchanged
→ run
→ close control plane and quiesce A1 worker
→ stop owned backend
→ release launcher lifecycle
```

If the control plane cannot establish its exact local boundary safely, ordinary
workshop operation may continue with Restore control unavailable. No alternate
transport is invented.

## Future C4-II-B re-proof

Before any destructive Restore, separately authorized C4-II-B must:

```text
reopen launcher-private original path through C4-I intake
→ compare SourceIdentity
→ recompute/compare full SHA-256
→ re-check sidecars/self-containment
→ stage again
→ validate again
→ prove backend exclusion
→ create mandatory before_restore safety copy
→ only then enter existing C4-I destructive execution
```

Browser state/token/filename is never destructive authority.

## Backend lifecycle

The ordinary backend remains running during non-destructive A1 validation and A2
control/session work. Backend exclusion/stop remains a future destructive
C4-II-B/C4-I boundary.

## A2 verification

A2 is not closed until exact published-head tests prove loopback/Host/Origin/CORS,
bootstrap race, token/session expiry, request ordering, concurrency, A1 proof
invalidation, production `picker_unavailable`, unchanged browser navigation,
runtime ownership, non-destructive behavior, A1/C4-I regressions and exact-head
direct-local-HTTP smoke.

## Successor gates

A3 remains blocked until A2 is exact-head verified, merged and lifecycle-closed.
A4 remains blocked by A3. C4-II-B remains separately not authorized.
