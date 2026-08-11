# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

```text
PR #187 — MERGED — C4-II-C AUTHORIZATION BASELINE
PR #186 — MERGED — C4-II-B3 EXACT-HEAD VERIFIED
PR #185 — MERGED — B3 AUTHORIZATION BASELINE
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-C — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

PR #187 reviewed the B3 closure / C4-II-C authorization head `48e245811af706bb666620c6dda8033ff200967a` and merged as `7a746fbf98f50682b509c40a06335a2157f1a7b7`. C4-II-C is the only authorized implementation slice.

## Closed Restore authority through B3

C4-I remains the only destructive Restore engine. B1 binds launcher-private retained source proof to C4-I intake. B2 owns authenticated one-shot `/v1/restore/execute` authority transfer and ordinary-backend restart handoff. B3 owns explicit browser confirmation and exact destructive replay.

The browser has no filesystem/source authority. No source path, proof, digest, operation ID, database path, backup path or lock path crosses the browser boundary. No `/v1/restore/confirm` endpoint exists.

## C4-II-C implementation changeset

The current changeset implements **Truthful Restore completion/recovery/restart/support UX** without changing Restore authority or protocol.

Production change is limited to:

```text
frontend/src/restore-control-presentation.ts
```

Focused result-state tests are added to:

```text
frontend/test/restore-control-races.test.mjs
```

Delivered presentation behavior:

- `restore_completed` gives a clear successful result and ordinary navigation only because merged B2 semantics prove backend readiness;
- `restore_failed` says ordinary work is available but does **not** infer rollback, unchanged data or automatically restored old data;
- `restore_blocked` removes normal-work navigation and gives restart/help guidance;
- connection/session loss after destructive execution may have begun is shown as **unknown**, never converted to success/failure/rollback/unchanged-data truth;
- exact ambiguous execute replay remains available only as the same previous command;
- `restoring`, pending execute and blocked/unknown states do not offer normal-work navigation;
- no new state, DTO field, endpoint, destructive retry sequence or cancel authority is added.

Closed byte-identical seams remain: `launcher/**`, `backend/**`, `frontend/src/restore-control-contract.ts`, `frontend/src/restore-control-runtime.ts`, `frontend/src/restore-control-entry.ts`, `frontend/src/main.ts`, app navigation, migrations, dependencies, package resources, ADR 0016 and ADR 0018.

C4-III remains blocked. Restore remains **NOT IMPLEMENTED** until C4-II-C itself is exact-head verified, merged and lifecycle-closed. Product release readiness remains **NOT CLAIMED**.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-b-implementation-slices.md` — closed B1→B3 contract;
- `docs/restore-interaction-and-validation-session.md` — active browser/control interaction profile.
