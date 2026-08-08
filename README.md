# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The product goal is a
packaged application a non-technical user can run without GitHub, Git, Python,
Node.js, Docker or a terminal.

## Current product status

```text
PR #174 — MERGED — C4-II-A1 EXACT-HEAD VERIFIED
PR #175 — MERGED — A1 CLOSED / A2 AUTHORIZED
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

PR #176 reviewed head
`681cb4050bec082db6b637285590e232880af739` merged as
`90a14dd9a11b83bc31a40e1d3fb9523f41772b88` after exact-head lifecycle and
smoke, 2 stale-A1-authority race tests, 28 A2 targeted tests, 17 A1 tests,
514 C4-I Restore tests, 2443 full backend+launcher tests and independent
P0=0 / P1=0 / P2=0 audit.

## Closed A1 boundary

A1 remains the launcher-owned non-destructive candidate-validation authority:
private validation scratch, direct C4-I intake/staging/validation reuse, source
identity + SHA-256 re-proof, generation invalidation, bounded presentation-safe
result and launcher-private retained source proof.

## Closed A2 boundary

A2 now provides the exact-run launcher-owned control/session protocol around A1:

- concurrent stdlib HTTP server on exact `127.0.0.1:<ephemeral>`;
- exact Host and configured local frontend Origin;
- atomic one-use bootstrap + separate run-scoped session token;
- no wildcard CORS/cookie authority and no-store responses;
- 15s heartbeat / 60s authenticated inactivity expiry;
- strict monotonic `command_seq` + idempotent same-request retry;
- one long-work owner while state/heartbeat/cancel remain responsive;
- A1 proof/generation invalidation on reselect/cancel/expiry/close;
- stale A2→A1 begin race hardened before owned-worker quiescence;
- launcher runtime owns control only after proved backend start and closes it
  before backend stop.

Production A2 still uses `UnavailableSourceSelectionAdapter`; browser/control
requests have no path/file authority and production browser navigation still
carries no control bootstrap/session material.

## Authorized A3 boundary

A3 is the only authorized next runtime slice. It may replace
`picker_unavailable` with the launcher-owned native macOS picker selected by
ADR 0018:

```text
/usr/bin/osascript
→ macOS Standard Additions choose file
→ absolute POSIX path only in launcher memory
→ existing A2 SourceSelectionAdapter seam
→ existing A1 candidate preparation
```

A3 must use a fixed script, no `shell=True`, no `System Events`, no
user-controlled AppleScript interpolation, typed cancellation and owned child
termination/quiescence. It adds no dependency.

A3 **does not** authorize browser path fallback, `/backups/restore`, production
bootstrap-fragment handoff or any destructive Restore behavior. A4 and C4-II-B
remain closed.

## Restore authority

Authority remains intentionally split:

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0017 — C4-I lifecycle closure/history;
- ADR 0018 — interaction/control/picker/validation-session architecture;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation plan;
- `docs/current-lifecycle.md` — current implementation authorization/status.

C4-II-B destructive confirmation/execution remains **NOT AUTHORIZED**.

## C4-II-A sequence

```text
A1 — validation-session core                     ← DONE / merged
→ A2 — exact-run launcher control plane          ← DONE / merged
→ A3 — native macOS picker integration           ← AUTHORIZED NEXT
→ A4 — browser /backups/restore + E2E UX         ← blocked
```

Each later slice starts from updated `main` only after predecessor merge,
exact-head gate and lifecycle update.

## Current authority map

1. [`docs/current-lifecycle.md`](docs/current-lifecycle.md)
2. applicable accepted ADR
3. [`docs/c4-ii-a-implementation-slices.md`](docs/c4-ii-a-implementation-slices.md)
4. [`docs/restore-interaction-and-validation-session.md`](docs/restore-interaction-and-validation-session.md)
5. [`docs/implementation-plan.md`](docs/implementation-plan.md)
6. active [`state/`](state/) files

Searchable history remains under [`docs/history/`](docs/history/README.md). The
five protected pre-compaction snapshots must remain byte-identical.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package,
API-first business architecture, safe historical data, recipe versions,
first-class client recipes, lot/movement inventory, transactional production,
safe import preview/confirmation, backup-before-migration and a human-readable
non-technical UI.

Restore additionally preserves launcher ownership of filesystem/destructive
authority, immutable selected source, no browser absolute-path authority and no
destructive action before separately authorized C4-II-B.
