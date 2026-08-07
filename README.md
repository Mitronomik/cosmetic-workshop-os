# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The product goal is a
packaged application a non-technical user can run without GitHub, Git, Python,
Node.js, Docker or a terminal.

## Current product status

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

PR #174 reviewed head
`e0e5e8c0b5ccbf0a17c85952b5aacd40589aabb5` merged as
`504e776508c940554b3ee8659a201af21db8303c` after exact-head lifecycle/smoke,
17 targeted A1 tests, 514 existing C4-I Restore tests, 2415 full backend+launcher
tests and P0=0 / P1=0 / P2=0 audit.

PR #175 reviewed head
`b1a48d8f668fa984e3032f85c226f77e30d92e4e` merged as
`636645ece744752f6a753ae5a25a05297fd34e10`, closing A1 lifecycle and opening
only A2 as the next runtime slice.

## Closed A1 boundary

A1 provides the launcher-owned non-destructive candidate-validation core:

- `RestoreCandidatePreparationService` / `prepare_restore_candidate(...)`;
- private system-temp validation scratch;
- C4-I intake/staging/validation reuse;
- source identity + SHA-256 re-proof;
- generation/cancel/reselection invalidation;
- bounded presentation-safe result;
- launcher-private retained source proof;
- owned-only scratch cleanup.

A1 remains the single candidate-preparation authority.

## Current A2 implementation boundary

The current changeset implements the exact-run launcher-owned control/session
protocol around A1:

- stdlib concurrent HTTP server bound exactly to `127.0.0.1` on an ephemeral port;
- exact Host and configured local frontend Origin;
- one-use >=256-bit bootstrap capability with atomic consume;
- separate >=256-bit run-scoped session token;
- `Cache-Control: no-store`, no wildcard CORS and no cookie authority;
- 15s heartbeat / 60s authenticated inactivity expiry;
- heartbeat/state/cancel remain responsive while one worker owns selection or
  validation;
- >=128-bit request ID namespace + strict monotonic `command_seq`;
- expected-next sequence consumed before business precondition evaluation;
- idempotent same-request retry and stale/future/conflict rejection;
- A1 generation/cancel/proof invalidation on reselection/cancel/expiry/close;
- launcher lifetime wiring after proved backend start and before backend shutdown.

Production A2 still returns typed `picker_unavailable` through
`UnavailableSourceSelectionAdapter`; it obtains no filesystem path. The HTTP
schema contains no `path`, `source_path`, upload/file bytes or equivalent browser
filesystem authority.

The actual product-browser launch URL remains unchanged. A2 does not put
`#cw-control`, control port, bootstrap capability or session material into browser
navigation. A4 owns the first production fragment handoff and `/backups/restore`.

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
→ A2 — exact-run launcher control plane          ← current changeset / not closed
→ A3 — native macOS picker integration           ← blocked
→ A4 — browser /backups/restore + E2E UX         ← blocked
```

Each later slice starts from updated `main` only after its predecessor merge,
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

Every change must preserve local-first operation, user data outside code/package,
API-first business architecture, safe historical data, recipe versions,
first-class client recipes, lot/movement inventory, transactional production,
safe import preview/confirmation, backup-before-migration and a human-readable
non-technical UI.

Restore additionally preserves launcher ownership of filesystem/destructive
authority, immutable selected source, no browser absolute-path authority and no
destructive action before separately authorized C4-II-B.
