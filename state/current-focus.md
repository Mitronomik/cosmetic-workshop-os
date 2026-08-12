# Current Focus — C4-III Restore end-to-end verification

Updated: `2026-08-12`

## Current lifecycle

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
CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
D3 — macOS package MVP — AUTHORIZED NEXT — NOT IMPLEMENTED
D4 — Update safety — NOT AUTHORIZED BY CR-012
D5 — Remote install checklist — NOT AUTHORIZED BY CR-012
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed baseline

PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`.

C4-II-C is closed on lifecycle PASS, frontend build PASS, focused Restore 34/34 PASS, browser smoke v5.4 PASS, fresh independent audit P0=0/P1=0/P2=0 and final no-change exact-head gate PASS.

## Current work

**C4-III — Restore end-to-end verification and lifecycle closure** is the only authorized open Restore slice. It is **IN PROGRESS — EXACT-HEAD VERIFICATION PASSED** and is not closed.

Verification must cover current-schema + supported older-schema Restore, rejection, interruption, rollback, repeated launch/startup recovery, source immutability, mandatory safety-copy retention and end-to-end lifecycle closure.

## Recorded external verification

On merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`, runner `c4-iii-restore-exact-head-v1`:

```text
lifecycle PASS
focused_restore_pytest PASS
frontend_npm_ci PASS
frontend_build PASS
frontend_restore_tests PASS
destructive_e2e_current_and_older PASS

PASS — C4-III EXACT-HEAD VERIFICATION PASSED

INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE

C4-III LIFECYCLE CLOSURE GATE:
BLOCKED — PACKAGE PREREQUISITE
```

## Blocking condition

C4-III cannot close because no packaged product artifact exists to run exact-package verification against. That is an environment prerequisite, not a product failure and not a runner failure. Do not relabel it as PASS and do not build packaging inside C4-III — the artifact is produced by the separate authorized task below.

Production Restore authority is closed. Do not change launcher/backend/contract/runtime/entry/presentation/main/navigation/ADRs in C4-III. Tests, isolated smoke runners and verification/lifecycle documentation may change. Any product defect requires a separate bounded fix PR.

## Next allowed task — D3 macOS package MVP

```text
D3 — macOS package MVP — AUTHORIZED NEXT — NOT IMPLEMENTED
```

`CR-012` is ACCEPTED; the normative decision is [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](../docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md). This is one bounded implementation task, run **outside** C4-III and merged separately from any C4-III verification claim.

It packages the existing architecture unchanged — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip`, preferably containing a simple `CosmeticWorkshopOS.app`. No desktop application shell, no second product UI, no WebView replacement, no new Restore transport, no backend Restore endpoint, no user data inside the package.

CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, auto-update, App Store, sandbox migration, release-channel infrastructure, D4 and D5 stay NOT AUTHORIZED. If the artifact contract turns out to need a new runtime framework, shell, sandbox model or Restore architecture change, STOP and open a new decision.

No package exists yet. Building it does not close C4-III; exact-package verification must still run and pass against the packaged runtime afterwards.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
