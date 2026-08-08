# Restore interaction and non-destructive validation-session profile

Status: **NORMATIVE PROFILE — ADR 0018 / CR-011**
Updated: `2026-08-08`

Normative sources:

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — selected interaction/control/picker/validation architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation plan;
- `docs/current-lifecycle.md` — current lifecycle authorization.

ADR 0018 architecture is unchanged by A1/A2 closure or A3 authorization.

## Current lifecycle

```text
PR #176 — MERGED — C4-II-A2 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A4 — PLANNED — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
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

Browser owns presentation only. Launcher owns control, picker, absolute selected
source path, validation-session authority and all future destructive authority.
No WebSocket, generic localhost command server, browser filesystem authority or
ordinary FastAPI Restore mutation is selected.

## A1 merged validation boundary

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

## A2 exact-run control plane — CLOSED

PR #176 reviewed head `681cb4050bec082db6b637285590e232880af739`
merged as `90a14dd9a11b83bc31a40e1d3fb9523f41772b88` after exact-head
race/A2/A1/C4-I/full regressions, direct-local-HTTP smoke and P0=0/P1=0/P2=0
audit.

A2 durable contract:

- concurrent stdlib control server on exact `127.0.0.1:<ephemeral>`;
- exact Host + configured local frontend Origin;
- one-use bootstrap using 32 random bytes and separate 32-random-byte-class run token;
- no wildcard CORS/cookie authority; no-store/no-cache responses;
- 15-second heartbeat / 60-second authenticated inactivity expiry;
- strict monotonic `command_seq` with sequence consumed before business preconditions;
- same-sequence/same-request idempotency and stale/future/conflict refusal;
- one selection/validation worker while heartbeat/state/cancel remain serviceable;
- cancel/expiry/reselection/close invalidate session/A1 authority;
- stale worker crossing the A2→A1 begin boundary cannot leave resurrected retained proof;
- runtime order: proved backend → control → ordinary browser; control close → backend stop.

Production A2 still uses `UnavailableSourceSelectionAdapter`; browser/control
request schema is pathless. Production browser navigation still carries no
control bootstrap/session material.

## A3 native picker — AUTHORIZED NEXT

A3 may replace only the production unavailable picker seam.

### Native picker ownership

Launcher owns the picker and absolute path:

- owned short-lived `/usr/bin/osascript` child;
- macOS Standard Additions `choose file`;
- fixed AppleScript, with no user-controlled text interpolation;
- no `shell=True`;
- no `System Events` automation;
- typed ordinary cancellation;
- selected POSIX path returned only to launcher memory;
- no new Python/application dependency.

Filename/type hints are presentation only. C4-I/A1 validation remains acceptance
authority.

### Picker process lifecycle

The existing A2 selection worker remains the one long-work owner. The A3 adapter
may own one child process for that worker. Cancel/expiry/close must invalidate
control/A1 authority immediately, signal/terminate the owned picker process when
active, and coordinate child wait/quiescence before the selection worker exits.
No detached or unaccounted picker child is allowed.

### Path privacy

The selected absolute POSIX path is launcher-private. It must not appear in:

- browser/control request payloads;
- control DTO/state;
- browser URL/query/fragment;
- user-visible error messages;
- logs containing raw selected path;
- backend API payloads.

It flows only through the launcher-internal source-selection result into merged
A1 candidate preparation and later launcher-private retained proof.

### Technical failure boundary

Picker technical errors return a fixed safe typed failure to the control layer.
Raw AppleScript/osascript stderr, stack traces and absolute paths remain local
technical detail and are not browser presentation.

## A3→A4 browser seam

Production product-browser launch URL remains unchanged during A3.
`open_runtime_browser(...)` must not append `#cw-control`, control port, bootstrap
capability or session token.

A4 owns `/backups/restore`, first production browser fragment handoff, immediate
fragment removal, `sessionStorage` token + non-secret `control_origin`, typed UX
and real non-destructive browser E2E smoke.

## Launcher runtime ownership

A3 preserves the already-verified A2 order:

```text
launcher lifecycle / recovery / startup
→ owned backend start + proved lock/socket handshake
→ exact-run Restore control plane
→ ordinary product browser URL unchanged
→ A2 selection worker owns A3 picker child when user selects
→ selected launcher-private path enters A1 validation
→ close/quiesce picker/control/A1
→ stop owned backend
→ release launcher lifecycle
```

If the picker cannot run safely, Restore source selection returns a safe typed
failure. No browser file input or alternate Restore transport is invented.

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

The ordinary backend remains running during non-destructive A1 validation, A2
control/session work and A3 picker selection. Backend exclusion/stop remains a
future destructive C4-II-B/C4-I boundary.

## Successor gates

A4 remains blocked until A3 is exact-head verified, merged and lifecycle-closed.
C4-II-B remains separately not authorized.
