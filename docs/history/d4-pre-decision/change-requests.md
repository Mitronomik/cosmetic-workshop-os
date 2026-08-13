# Change Requests

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

## Restore decisions

CR-011 remains **ACCEPTED**. ADR 0018 remains normative for launcher-owned loopback control, picker/session security and browser path privacy. ADR 0016 remains normative for destructive Restore durable truth. ADR 0017 defines C4-III as end-to-end verification and lifecycle closure.

PR #188 merged as `6294f0044c792ced3ac56d213ea5333e33062f12` and C4-II-C is now closed. PR #189 merged as `81e8193596709b0c16d0ecad598458b3ea95fd9c` and authorized C4-III verification.

## C4-III authorization — closed

C4-III verified the already-decided and merged Restore architecture. No new Change Request is needed for verification-only tests, isolated smoke runners, evidence documentation or lifecycle closure, and none was opened: C4-III closed within its original authorization.

If further Restore work appears to require a new launcher state, endpoint, DTO field, browser filesystem authority, durable phase, backend behavior, destructive command, packaging architecture or other product/architecture change, STOP and open a separate decision/change request or bounded defect-fix PR as appropriate. C4-III is closed and cannot absorb it.

Building the packaged artifact was **not** C4-III work. It was the separate CR-012 successor task recorded below, and it was not performed inside the C4-III verification slice.

C4-III closed on the combination of the accepted exact-head PASS (`81e8193596709b0c16d0ecad598458b3ea95fd9c`, runner `c4-iii-restore-exact-head-v1`) and the accepted exact-package PASS (`0e1193264dc22979ca48e32a962aba916b6b520e`, runner `c4-iii-restore-exact-package-v1.2`, SHA-256 `2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694`). That closure authorizes no further stage: `D4` and `D5` remain NOT AUTHORIZED, and product release readiness remains NOT CLAIMED.

## CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification

Status: **ACCEPTED** — 2026-08-12. Normative decision: [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](../docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md).

C4-III exact-head verification PASSED on `81e8193596709b0c16d0ecad598458b3ea95fd9c`. PR #190 recorded the exact-package result and merged as `1a5061b236cf7f69bca9ba533553e21401b94ab8`.

The exact-package verifier correctly reported `INCONCLUSIVE — ENVIRONMENT` because the required packaged artifact was unavailable. Separately, no packaging implementation had yet been authorized to produce that artifact. CR-012 closes only that authorization gap. It does not reclassify or amend the previously recorded verification result.

CR-012 authorized the existing roadmap stage as the one bounded successor implementation task:

```text
D3 — macOS package MVP — IMPLEMENTED

Original purpose:
produce the packaged product artifact required for
C4-III exact-package verification.
```

`D3 — macOS package MVP` is the roadmap's own stage; CR-012 authorizes it rather than inventing a parallel packaging phase, and D3's roadmap scope, tests and non-goals stay authoritative. D3 packages the existing local-first topology — launcher → localhost backend → built frontend → ordinary system browser → external user-data directory — into `CosmeticWorkshopOS-mac.zip`, preferably containing a simple `CosmeticWorkshopOS.app`. It packages the product; it does not replace it. ADR 0016 and ADR 0018 Restore semantics, the browser-first presentation surface and the external user-data rules stay unchanged. No desktop application shell — Electron, Tauri, pywebview, PyObjC — no second product UI, no WebView replacement for the browser UI, no new Restore transport and no backend Restore endpoint is authorized.

Bounded authorization rule: **CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization.** Signing, notarization, mandatory DMG, installer redesign, auto-update, update download, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation beyond testing this artifact, D4 update safety and D5 remote-install work all remain **NOT AUTHORIZED** by CR-012 — none of them belong to D3, and the roadmap's D3 non-goals stay authoritative. ADR 0019 holds the full artifact contract, package contents, exclusions, build-only-tool conditions and stop conditions.

Producing the artifact was a verification prerequisite, never product release readiness. The stated condition — that the artifact exist **and** the external exact-package verifier run and pass against it — has since been met in full; the accepted result is recorded below and in [`docs/current-lifecycle.md`](../docs/current-lifecycle.md).

### CR-012 implementation status

D3 is implemented. `make package-macos` produces `dist/CosmeticWorkshopOS-mac.zip` containing `CosmeticWorkshopOS.app`, packaging the existing topology unchanged. No protected closed Restore production file changed, no desktop application shell was introduced, and the one build-only dependency — a pinned, checksum-verified relocatable CPython — satisfies the six ADR 0019 conditions. No stop condition was hit, so no new decision was required.

That closed the artifact prerequisite and nothing else. The recorded `INCONCLUSIVE — ENVIRONMENT` classification from the earlier run is preserved as history and is never rewritten. Writing and running the exact-package verifier remained C4-III work under ADR 0017, and it has now been done: runner `c4-iii-restore-exact-package-v1.2`, SHA-256 `2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694`, return code `0`, `PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED` against packaged `main` `0e1193264dc22979ca48e32a962aba916b6b520e`. Two earlier runner attempts (`INCONCLUSIVE — RUNNER`, and a `v1.1` textual `FAIL — PRODUCT` proved to be a runner `UnboundLocalError`) are preserved as runner-fault history and are not product defects.

CR-012 stays bounded by its own terms. The C4-III closure it enabled does not extend it: `D4`, `D5`, signing, notarization, DMG, auto-update, release-channel infrastructure, App Store, sandbox migration and cloud deployment/sync all remain NOT AUTHORIZED. Product release readiness remains NOT CLAIMED.
