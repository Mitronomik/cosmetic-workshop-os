# cosmetic-workshop-os — Active implementation plan

Project: `cosmetic-workshop-os`
Client-facing name: **Мастерская косметолога**
Status: **active current implementation sequence**
Updated: `2026-08-11`

## Current lifecycle

```text
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
C4-II-B3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-C — PLANNED — NOT AUTHORIZED
C4-III — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Merged baseline

```text
PR #182 reviewed B1 head — 27726058af4f373ab65225ecf4d1a945f1c53067
PR #182 merge/new main — 5e13b50f1918dacbf8d54066c9156942a9adb895
PR #183 reviewed B2-authorization head — fa922f56c19a2dd33b6307ae0a197d476f91489b
PR #183 merge/new main — 4617b8c436eaa510fd545d863346595e2d808ea7
PR #184 reviewed B2 head — 1ae8bfcdf0f1f1798ce85eac0931925d029379c4
PR #184 merge/new main — 266c50a77e5f353fa77701cb854629a99460667f
```

## Closed implementation — C4-II-B2

B2 is merged and exact-head verified. Its closed launcher flow remains:

```text
POST /v1/restore/execute
  exact body: request_id + command_seq + generation
→ authenticated/session/replay checks
→ consume exactly-next sequence before business preconditions
→ require current accepted control generation + current retained A1 proof
→ copy launcher-private authority into one RestoreExecutionIntent
→ invalidate retained source authority
→ HTTP returns safe restoring state without running C4-I
→ launcher main runtime consumes intent synchronously
→ ProofBoundRestoreRequest
→ existing execute_restore(..., LauncherLifecycleContext)
→ existing C4-I owns all destructive semantics
→ safe ordinary-backend restart/result handoff
```

Accepted B2 evidence:

- focused B2/runtime tests: **37 PASS**;
- launcher regression: **636 PASS**;
- backend regression: **1867 PASS**;
- full backend + launcher: **2503/2503 PASS**;
- frontend Restore regression: **16/16 PASS**;
- autonomous anti-hang gate: **PASS**;
- corrected external exact-head isolated process smoke: **PASS**;
- independent audit: **P0=0 / P1=0 / P2=0**;
- final no-change exact-head / clean-worktree gate: **PASS**.

The earlier eight-hour manually interrupted run remains invalid evidence. The first external smoke runner remains `INCONCLUSIVE RUNNER`.

## Protected implementation boundaries

The lifecycle checker pins the accepted merged B1/C4-I/B2 production implementation and the pre-B3 frontend baseline. No ordinary FastAPI backend, migration, dependency or packaging resource is in B3 authorization scope.

## Current implementation window — C4-II-B3

B3 is the only authorized next slice. It is frontend-only explicit destructive confirmation/presentation wiring.

```text
accepted
→ explicit destructive confirmation
→ local dismiss OR authenticated execute
→ exact request_id + command_seq + generation
→ merged B2 authority transfer
→ pathless restoring/final launcher state
```

B3 may parse exactly the four merged B2 states: `restoring`, `restore_completed`, `restore_failed`, `restore_blocked`. Unknown states remain fail-closed.

The browser may add action `execute` calling only `/v1/restore/execute`. `/v1/restore/confirm` is not authorized. No launcher/backend change is authorized.

### B3 load-bearing replay

Current select/cancel replay persists action/request ID/command sequence. Execute additionally requires the accepted generation.

An ambiguous execute retry must preserve the **same request ID, command sequence and generation** and resend the exact same body. It must not allocate a new request ID or sequence. Existing select/cancel replay remains backward-safe. No filesystem authority may enter browser persisted replay state.

### B3 UX boundary

Only current `accepted` may open destructive confirmation. Dismiss is local and sends neither execute nor implicit cancel. Repeated confirmation cannot duplicate execute.

`restoring` disables duplicate destructive actions and destructive cancel affordances while heartbeat/state polling continues. It shows no fake phase or percentage.

Completed/failed/blocked may minimally present only the safe launcher message. Rich truthful result/recovery/restart/support UX remains C4-II-C scope.

## Forbidden scope

No launcher/backend Restore change, no `/v1/restore/confirm`, no browser filesystem authority, no second Restore engine, no phase/recovery redesign, no Restore AuditLog change, no new dependency, no packaging redesign, no C4-II-C/C4-III authorization.

## Required B3 proof before merge

Future B3 must prove contract parsing, exact execute schema/privacy, explicit confirmation, dismiss semantics, duplicate-submit protection, exact replay of request ID/command sequence/generation, restoring behavior, minimal final state presentation, existing A4 regression and ordinary navigation regression, plus appropriate exact-head smoke and independent audit.

## Next action

Implement B3 as one bounded Draft PR → run focused frontend contract/replay/confirmation tests and A4 regression → appropriate browser/control smoke → independent audit → merge only when exact-head evidence is green → separate B3 lifecycle closure before any C4-II-C authorization.
