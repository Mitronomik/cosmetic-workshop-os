# C4-II-B implementation authorization and slice plan

Status: **CLOSED NORMATIVE IMPLEMENTATION PLAN**
Updated: `2026-08-12`

This document records the closed C4-II-B slices and their closed C4-II-C successor. ADR 0016, ADR 0018 and current lifecycle authority remain controlling.

## Current slice status

```text
PR #190 — MERGED — C4-III PARTIAL VERIFICATION CHECKPOINT
PR #189 — MERGED — C4-II-C LIFECYCLE CLOSURE AND C4-III AUTHORIZATION
PR #188 — MERGED — C4-II-C EXACT-HEAD VERIFIED
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
C4-II-C — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-III — IN PROGRESS — EXACT-HEAD VERIFICATION PASSED
C4-III EXACT-PACKAGE VERIFICATION — BLOCKED BY PACKAGED ARTIFACT PREREQUISITE
C4-III LIFECYCLE CLOSURE — NOT COMPLETED
CR-012 — ACCEPTED — MINIMAL MACOS PACKAGED-ARTIFACT PREREQUISITE
Minimal macOS packaged-artifact prerequisite — AUTHORIZED NEXT — NOT IMPLEMENTED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed B1/B2/B3

B1 binds launcher-private source proof to C4-I intake. B2 owns one-shot launcher execution authority and safe ordinary-backend restart handoff. B3 owns explicit browser destructive confirmation, exact pending execute replay and pathless restoring/final-state parsing.

B3 final reviewed head `316358c65a851b46090121c7a6bc877b980176ba`; merge `b9ca2bd77d5f2be0ba406e9669c18f74e1955725`.

## Closed C4-II-C successor

PR #187 authorized C4-II-C. PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12`.

C4-II-C changes presentation only and is closed on frontend build PASS, focused Restore 34/34 PASS, browser smoke v5.4 PASS, fresh independent P0=0/P1=0/P2=0 audit PASS and final no-change gate PASS.

The final C4-II-C presentation is now a closed production boundary. It does not reopen B1/B2/B3 authority, contract/runtime, launcher/backend, main/navigation or ADRs.

## Successor

**C4-III — Restore end-to-end verification and lifecycle closure** is **IN PROGRESS — EXACT-HEAD VERIFICATION PASSED**.

It verifies the existing chain; it does not authorize new Restore authority or hidden product changes. Product defects discovered during verification require a separate bounded fix.

External exact-head verification of this closed B1→C4-II-C chain PASSED on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`, including `focused_restore_pytest`, `frontend_restore_tests` and `destructive_e2e_current_and_older`. That evidence does not close C4-III: exact-package verification remains `INCONCLUSIVE — ENVIRONMENT` and `C4-III LIFECYCLE CLOSURE — NOT COMPLETED`.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
