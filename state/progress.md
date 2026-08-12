# Progress

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

## 2026-08-11 — C4-II-C merged and exact-head verified

PR #188 reviewed head `1df21915fdcf4a708dc778a0e762d64830b5b880` merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`.

Accepted evidence:

- lifecycle checker PASS;
- frontend install/build PASS, 0 vulnerabilities;
- focused Restore control suite 34/34 PASS;
- browser smoke v5.4 PASS with real resume-without-replay final-state precedence and true invalidation paths;
- fresh independent audit P0=0/P1=0/P2=0 — PASS;
- final no-change exact-head gate PASS.

C4-II-C is now DONE — MERGED AND EXACT-HEAD VERIFIED.

## 2026-08-11 — C4-III authorized next

C4-III — Restore end-to-end verification and lifecycle closure — is the only authorized next Restore slice.

No production change is authorized by this lifecycle transition. C4-III must verify the merged chain across current/older schema, rejection, interruption, rollback, repeated launch, source immutability and safety-copy retention. Product defects found by verification require separate bounded fixes.

Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.

## 2026-08-12 — C4-III exact-head verification PASSED, exact-package INCONCLUSIVE

PR #189 merged as `81e8193596709b0c16d0ecad598458b3ea95fd9c`. An independently executed external verifier, version `c4-iii-restore-exact-head-v1`, SHA-256 `4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a`, ran against that exact merged head.

Outer gates:

```text
C4III EXACT-HEAD OUTER GATE: PASS
C4III EXACT-PACKAGE OUTER GATE: INCONCLUSIVE — ENVIRONMENT
C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE
```

Observed exact-head results:

```text
lifecycle PASS
focused_restore_pytest PASS
frontend_npm_ci PASS
frontend_build PASS
frontend_restore_tests PASS
destructive_e2e_current_and_older PASS

PASS — C4-III EXACT-HEAD VERIFICATION PASSED
```

Observed exact-package result:

```text
INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE

C4-III LIFECYCLE CLOSURE GATE:
BLOCKED — PACKAGE PREREQUISITE
```

The required packaged product artifact was unavailable, so the exact-package half could not run. That is an environment prerequisite gap — not a product failure and not a runner failure — and it is not recorded as PASS.

This checkpoint records that external result only. It reruns nothing, relabels nothing and changes no product, runtime, dependency or migration file. The pre-change active documents are preserved byte-identically in `docs/history/c4-iii-pre-partial-verification/`.

C4-III is now IN PROGRESS — EXACT-HEAD VERIFICATION PASSED. Exact-package verification is BLOCKED BY PACKAGED ARTIFACT PREREQUISITE and C4-III lifecycle closure is NOT COMPLETED.

Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.

## 2026-08-12 — CR-012 accepted, D3 macOS package MVP authorized

PR #190 merged as `1a5061b236cf7f69bca9ba533553e21401b94ab8`. On that baseline, `CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification` is **ACCEPTED**, recorded normatively in [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](../docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md).

The exact-package verifier correctly reported `INCONCLUSIVE — ENVIRONMENT` because the required packaged artifact was unavailable. Separately, no packaging implementation had yet been authorized to produce that artifact. CR-012 closes only that authorization gap. It does not reclassify or amend the previously recorded verification result.

It authorizes the existing roadmap stage as the one bounded successor implementation task, with its current purpose recorded:

```text
D3 — macOS package MVP — AUTHORIZED NEXT — NOT IMPLEMENTED

Current purpose:
produce the packaged product artifact required for
C4-III exact-package verification.
```

D3 packages the existing local-first architecture — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip`, preferably containing a simple `CosmeticWorkshopOS.app`. It preserves the browser-first product surface and the ADR 0016/0018 Restore architecture, and authorizes no desktop application shell (Electron, Tauri, pywebview, PyObjC), no second product UI, no WebView replacement, no new Restore transport and no backend Restore endpoint. User data stays outside the package.

The older blanket statement — that packaging implementation had no authorization at all — is replaced by the narrower truthful rule: CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, installer redesign, auto-update, update download, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation, D4 and D5 remain NOT AUTHORIZED — consistent with the roadmap's own D3 non-goals.

This is a decision-only change. It changes no backend, frontend, launcher, packaging script, build script, dependency manifest, lockfile or CI workflow, and it creates no package. Product/runtime smoke is not applicable.

C4-III stays IN PROGRESS — EXACT-HEAD VERIFICATION PASSED. Exact-package verification stays BLOCKED BY PACKAGED ARTIFACT PREREQUISITE and is never relabelled PASS. C4-III lifecycle closure stays NOT COMPLETED. Restore remains NOT IMPLEMENTED. Product release readiness remains NOT CLAIMED.
