# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

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

PR #179 reviewed closure head `72b04510efd6d1f104369a450ed1c4d4dfe063ad` merged as `52cc0b04e0b9531b6cc234c83cbcbb81e04a37bf`, closing A3 and authorizing only A4.

## Current A4 implementation boundary

A4 adds the browser presentation/session layer selected by ADR 0018:

```text
launcher control plane
→ browser URL fragment #cw-control=<ephemeral-port>:<bootstrap-token>
→ SPA removes fragment immediately
→ one-use POST /v1/bootstrap
→ run-scoped sessionStorage descriptors
→ /backups/restore presentation
→ existing A2 select/cancel/session
→ existing A3 native picker
→ existing A1/C4-I non-destructive validation
```

The browser never owns an absolute source path. It sends no file bytes, upload, bookmark or filesystem handle. The native picker remains launcher-owned.

Secrets are restricted to the one-use launch fragment and the run-scoped session token in `sessionStorage`. The non-secret strict-command replay metadata needed for safe reload/retry (`nextCommandSeq` and one pending request ID/action/sequence) lives only in same-tab `history.state`; it is not launcher authority. A network-uncertain command is retried with the exact same request ID and sequence. If replay state cannot be proved after prior activity, mutation fails closed with restart guidance.

A4 presents only non-destructive selection and validation. Even after an accepted candidate, the UI explicitly states that working data has not changed and exposes no destructive Restore button.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current authorization and gate;
- `docs/c4-ii-a-implementation-slices.md` — bounded A1→A4 implementation sequence.

C4-II-B destructive confirmation/execution remains **NOT AUTHORIZED**.

## Architectural invariants

Every change preserves local-first operation, user data outside code/package, API-first business architecture, safe historical data, recipe versions, first-class client recipes, lot/movement inventory, transactional production, safe import preview/confirmation, backup-before-migration and a human-readable non-technical UI.

Restore additionally preserves launcher filesystem/destructive authority, immutable selected source, pathless browser presentation and no destructive action before separately authorized C4-II-B.
