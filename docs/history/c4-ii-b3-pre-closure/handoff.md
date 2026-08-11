# Handoff

Updated: `2026-08-11`

Current lifecycle authority: `docs/current-lifecycle.md`. Restore authority: ADR 0016 and ADR 0018. Current B plan: `docs/c4-ii-b-implementation-slices.md`.

## Current lifecycle

```text
PR #185 — MERGED — B3 AUTHORIZED
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed B2 baseline

```text
PR #184 reviewed head — 1ae8bfcdf0f1f1798ce85eac0931925d029379c4
PR #184 merge/new main — 266c50a77e5f353fa77701cb854629a99460667f
PR #185 reviewed B3-authorization head — f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c
PR #185 merge/new main — f6589bdd7c403b6d400e3f5b7a0daea75b14632a
```

B2 remains closed on accepted exact-head tests, corrected external process smoke, independent `P0=0/P1=0/P2=0` and final clean-head gate.

## Current B3 implementation

```text
accepted parsed snapshot
→ explicit local confirmation dialog
→ dismiss/Escape locally OR destructive confirm
→ runtime derives current accepted generation
→ persist pending execute before fetch
→ POST /v1/restore/execute
   exact request_id + command_seq + generation
→ ambiguous result retains exact pending execute
→ retry resends same request_id + command_seq + generation
→ B2 owns destructive authority
→ browser polls restoring / final launcher states
```

The current implementation changes only focused Restore frontend modules/tests plus lifecycle docs/checker. `main.ts` remains unchanged. No launcher/backend/migration/dependency/package-resource code is changed.

`restoring` has no select/cancel/re-confirm/destructive-cancel UI and shows no fake progress. Final B2 states present safe launcher messages only. Local confirmation is invalidated if the accepted generation/view changes.

## Verification still required

Do not present B3 as closed until all are real exact-head evidence:

- `git diff --check` + lifecycle checker;
- frontend build/type-check;
- focused Restore control tests;
- A4 bootstrap/session/select/cancel/replay regressions;
- exact execute/replay/duplicate-submit proof;
- desktop and narrow-screen Restore smoke;
- keyboard focus/Escape dialog smoke;
- clean exact head/worktree;
- independent `P0=0/P1=0/P2=0` audit.

## Not B3

No `/v1/restore/confirm`, browser filesystem authority, destructive cancel, launcher/backend Restore change, durable phase/recovery redesign, C4-II-C or C4-III authorization.