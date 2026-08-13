# Current Focus — C4-III Restore lifecycle closed

Updated: `2026-08-12`

## Current lifecycle

```text
PR #192 — MERGED — D3 MACOS PACKAGE MVP
PR #191 — MERGED — CR-012 / D3 AUTHORIZATION
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
C4-III — DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED
C4-III EXACT-HEAD VERIFICATION — PASS
C4-III EXACT-PACKAGE VERIFICATION — PASS
C4-III LIFECYCLE CLOSURE — COMPLETED BY THIS CHANGESET
CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
D3 — macOS package MVP — IMPLEMENTED
D4 — Update safety — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE
D5 — Remote install checklist — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE
Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED
Product release readiness — NOT CLAIMED
```

## Closed baseline

PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`.

C4-II-C is closed on lifecycle PASS, frontend build PASS, focused Restore 34/34 PASS, browser smoke v5.4 PASS, fresh independent audit P0=0/P1=0/P2=0 and final no-change exact-head gate PASS.

## Current work

**C4-III — Restore end-to-end verification and lifecycle closure** was the last authorized open Restore slice. It is **DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED**, and this changeset carries its lifecycle closure.

Verification covered current-schema + supported older-schema Restore, rejection, interruption, rollback, repeated launch/startup recovery, source immutability, mandatory safety-copy retention and end-to-end lifecycle closure.

## Recorded external verification — exact-head half

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

That exact-package `INCONCLUSIVE — ENVIRONMENT` is preserved exactly as recorded. There was no packaged product artifact to run against — an environment prerequisite, not a product failure and not a runner failure. It is never relabelled as PASS, and packaging was not built inside C4-III to clear it; it was built by the separate authorized D3 task below.

## Recorded external verification — exact-package half

On published `main` `0e1193264dc22979ca48e32a962aba916b6b520e`, runner `c4-iii-restore-exact-package-v1.2`, SHA-256 `2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694`, return code `0`:

```text
PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED
PASS — FULL AUTOMATED SMOKE PASSED
```

Eight accepted scenarios on the packaged runtime:

1. current-schema Restore — `restore_completed`, selected source SHA-256 unchanged, `before_restore` safety copy retained, backend restarted successfully;
2. supported older-schema Restore — migration to the current schema succeeded, `restore_completed`, selected source unchanged, `before_restore` safety copy retained;
3. invalid source rejection — rejected before destructive execution, working database unchanged, no durable Restore operation, no `before_restore` safety copy;
4. source changed after validation — stale retained source proof rejected, final state `restore_failed`, working database unchanged, no durable Restore operation, no `before_restore` safety copy;
5. pre-replacement interruption — starting phase `source_staged`, recovered to `aborted`, workspace unchanged, ordinary startup allowed;
6. actual hard interruption after accepted execute — real durable crash phase `replacement_intent`, next packaged launch recovered through rollback to `rolled_back`, previous workspace restored, selected source unchanged, `before_restore` safety copy retained;
7. interrupted rollback — starting phase `rollback_in_progress`, recovered to `rolled_back`, safety copy retained, repeated launch safe and stable;
8. missing safety copy after replacement — starting phase `replacement_committed`, recovered to `recovery_blocked`, packaged exit code `3`, ordinary startup refused, operation evidence retained.

Runner cleanup: `owned processes left: none`, `owned ports still held: none`.

Runner history preserved truthfully and never counted as product defects: one earlier `INCONCLUSIVE — RUNNER` from an incorrect fixture `PYTHONPATH`, and a `v1.1` textual `FAIL — PRODUCT` proved to be a runner `UnboundLocalError` and therefore invalid as product evidence. `v1.2` corrected the probe/classification boundary and produced the accepted PASS.

The verifier is external test-only evidence, identified by version and SHA-256, and is not committed to this repository.

## Closure condition

C4-III closes on the combination of the accepted exact-head PASS and the accepted exact-package PASS, and on nothing else. Exact-head evidence alone was never sufficient.

`Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`, as a consequence of this closure only.

Production Restore authority stays closed. Do not change launcher/backend/contract/runtime/entry/presentation/main/navigation/ADRs. Product release readiness stays NOT CLAIMED; `D4` and `D5` stay NOT AUTHORIZED. Any further Restore or release/distribution work needs a new decision or change request.

## Completed task — D3 macOS package MVP

```text
D3 — macOS package MVP — IMPLEMENTED
```

`CR-012` is ACCEPTED; the normative decision is [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](../docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md). It was one bounded implementation task, run **outside** C4-III and merged separately from any C4-III verification claim.

It packages the existing architecture unchanged — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory. `make package-macos` produces `dist/CosmeticWorkshopOS-mac.zip` containing `CosmeticWorkshopOS.app`. No desktop application shell, no second product UI, no WebView replacement, no new Restore transport, no backend Restore endpoint, no user data inside the package. No protected closed Restore production file changed.

Delivered:

- `scripts/build_frontend.sh`, `scripts/build_backend.sh`, `scripts/package_macos.sh` — real implementations, no longer placeholders;
- `macos_package/` — packaged entrypoint, standard-library production-frontend server with `/api/*` proxy, fixed-catalogue macOS startup alerts, package-structure verifier;
- a build-only pinned relocatable CPython `3.12.13` with per-architecture SHA-256 verification, so the end user needs no Python and no Node.

CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, auto-update, App Store, sandbox migration, release-channel infrastructure, D4 and D5 stay NOT AUTHORIZED.

Building it did not close C4-III. The separate exact-package verifier had to run and pass against the packaged runtime, and it did. The D3 Level-5 package smoke proved the package/runtime delivery layer only and was never reported as C4-III exact-package verification.

`IMPLEMENTED` is the final D3 status: a built macOS package MVP, and no claim of release readiness, App Store readiness, notarization, signing, DMG, updater or universal packaging.

Product release readiness remains NOT CLAIMED.
