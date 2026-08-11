# Handoff

Updated: `2026-08-11`

## Current lifecycle

```text
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
C4-II-C — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed baseline

PR #186 final reviewed head `316358c65a851b46090121c7a6bc877b980176ba` merged as `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.

B3 accepted evidence: lifecycle/build PASS; focused Restore 30/30 PASS; browser smoke v4 PASS; final independent P0=0/P1=0/P2=0; final no-change gate PASS. Preserve the earlier `de827c57…` P1=1 audit as historical evidence; do not rewrite it as a PASS.

## Next implementation handoff

**C4-II-C — Truthful Restore completion/recovery/restart/support UX** is the only authorized next slice and is **frontend-only**.

Use existing merged states only:

```text
restore_completed
restore_failed
restore_blocked
```

Also handle **session/network uncertainty** without inventing final truth.

Expected primary file: `frontend/src/restore-control-presentation.ts`. `frontend/src/restore-control-entry.ts` may change only for bounded navigation/focus/help/restart affordance wiring.

Keep byte-identical unless separately authorized: launcher/**, backend/**, `frontend/src/restore-control-contract.ts`, `frontend/src/restore-control-runtime.ts`, `frontend/src/main.ts`, app navigation, migrations, dependencies, package resources, ADR 0016, ADR 0018.

Hard stops: no new launcher state; no new control endpoint; no browser filesystem authority; no destructive retry; no destructive cancel; no operation ID or durable phase in browser; no backend Restore ownership; no packaging redesign.

`restore_failed` must not infer rollback/unchanged data. `restore_blocked` must not offer normal work as safe. `restore_completed` may offer ordinary navigation only within merged B2 backend-ready semantics.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
