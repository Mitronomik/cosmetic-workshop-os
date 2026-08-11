# C4-II-B implementation authorization and slice plan

Status: **CLOSED NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-11`

This document records the closed C4-II-B slices. ADR 0016 and ADR 0018 remain authoritative.

## Merged baseline

```text
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 / B1 merge — 5e13b50f1918dacbf8d54066c9156942a9adb895
PR #183 reviewed B2-authorization head — fa922f56c19a2dd33b6307ae0a197d476f91489b
PR #183 / B2-authorization merge — 4617b8c436eaa510fd545d863346595e2d808ea7
PR #184 reviewed B2 head — 1ae8bfcdf0f1f1798ce85eac0931925d029379c4
PR #184 / B2 merge — 266c50a77e5f353fa77701cb854629a99460667f
PR #185 reviewed B3-authorization head — f206cf4896abcc7e8ecd0266cacd3f8a6d89e22c
PR #185 / B3-authorization merge — f6589bdd7c403b6d400e3f5b7a0daea75b14632a
PR #186 reviewed B3 head — 316358c65a851b46090121c7a6bc877b980176ba
PR #186 / B3 merge — b9ca2bd77d5f2be0ba406e9669c18f74e1955725
```

## Current slice status

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

## Closed B1

B1 binds launcher-private A1 retained `SourceIdentity` + SHA-256 proof to the same C4-I `HeldSource` before destructive work. Base `RestoreRequest` remains selected-source-only. Proof mismatch refuses before `prepared`, safety copy or working-database mutation.

Accepted evidence remains 10/10 proof-binding tests, 10/10 privacy tests, 2480/2480 backend+launcher regression, external source-substitution smoke PASS and independent P0=0/P1=0/P2=0.

## Closed B2

B2 is the one-shot launcher destructive coordinator:

```text
browser/session
→ authenticated POST /v1/restore/execute
→ exactly-next command sequence consumed before business preconditions
→ accepted control generation + launcher-private retained proof
→ one in-memory RestoreExecutionIntent
→ retained source authority invalidated
→ pathless restoring
→ launcher main runtime invokes existing C4-I
→ safe ordinary-backend restart handoff
→ pathless restore_completed / restore_failed / restore_blocked
```

C4-I remains the sole destructive engine. HTTP/session workers do not execute C4-I. Browser generation is a stale-view guard, never source proof.

## Closed B3

B3 closes the browser explicit destructive confirmation and exact replay seam:

```text
accepted candidate
→ explicit native dialog
→ local dismiss/Escape OR explicit confirm
→ runtime captures current accepted generation
→ persist pending execute before HTTP
→ POST /v1/restore/execute
→ ambiguous retry uses same request ID, command sequence and generation
→ B2 remains destructive authority
→ browser polls pathless final states
```

Closed production surface:

```text
frontend/src/restore-control-contract.ts
frontend/src/restore-control-runtime.ts
frontend/src/restore-control-presentation.ts
frontend/src/restore-control-entry.ts
```

Final reviewed head `316358c65a851b46090121c7a6bc877b980176ba`; merge `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.

Accepted final evidence: lifecycle PASS; frontend build PASS; focused Restore **30/30 PASS**; browser smoke v4 PASS with one execute and zero cancel; independent final audit P0=0/P1=0/P2=0; final no-change gate PASS.

Historical audit failure is retained: head `de827c5789f165949d0dbcd4fbbda4f5d368d71f` had P1=1 because **pending execute presentation** could make a false unchanged/not-started claim. The corrected final head makes the uncertain execution state truthful.

Closed B3 guarantees include exact state parsing, fail-closed unknown state, no browser source/path/proof/digest authority, no `/v1/restore/confirm`, current-accepted generation ownership, backward-safe select/cancel replay, exact execute replay, persist-before-network, duplicate-submit prevention, local dismiss/Escape, safe initial focus, no destructive cancel/fake progress in `restoring`, pathless final states, and truthful pending-execute copy.

## Successor discipline

The C4-II-B group is closed. C4-II-C is the only authorized next implementation slice.

**C4-II-C — Truthful Restore completion/recovery/restart/support UX** is frontend-only and must not reopen launcher/backend/contract/runtime authority. No new launcher state, no new control endpoint, no browser filesystem authority, no destructive retry, no destructive cancel, no C4-III implementation.

C4-III remains PLANNED — NOT AUTHORIZED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
