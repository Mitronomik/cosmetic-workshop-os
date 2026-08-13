# Progress

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

At that point Restore was still unimplemented and product release readiness was not claimed.

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

As of that entry C4-III was in progress with exact-head verification passed, exact-package verification blocked by the packaged-artifact prerequisite, and C4-III lifecycle closure not completed. Restore was still unimplemented and product release readiness was not claimed.

## 2026-08-12 — CR-012 accepted, D3 macOS package MVP authorized

PR #190 merged as `1a5061b236cf7f69bca9ba533553e21401b94ab8`. On that baseline, `CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification` is **ACCEPTED**, recorded normatively in [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](../docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md).

The exact-package verifier correctly reported `INCONCLUSIVE — ENVIRONMENT` because the required packaged artifact was unavailable. Separately, no packaging implementation had yet been authorized to produce that artifact. CR-012 closes only that authorization gap. It does not reclassify or amend the previously recorded verification result.

It authorizes the existing roadmap stage as the one bounded successor implementation task, with its purpose at the time recorded:

```text
D3 — macOS package MVP

Purpose at the time:
produce the packaged product artifact required for
C4-III exact-package verification.
```

D3 packages the existing local-first architecture — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip`, preferably containing a simple `CosmeticWorkshopOS.app`. It preserves the browser-first product surface and the ADR 0016/0018 Restore architecture, and authorizes no desktop application shell (Electron, Tauri, pywebview, PyObjC), no second product UI, no WebView replacement, no new Restore transport and no backend Restore endpoint. User data stays outside the package.

The older blanket statement — that packaging implementation had no authorization at all — is replaced by the narrower truthful rule: CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, installer redesign, auto-update, update download, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation, D4 and D5 remain NOT AUTHORIZED — consistent with the roadmap's own D3 non-goals.

This is a decision-only change. It changes no backend, frontend, launcher, packaging script, build script, dependency manifest, lockfile or CI workflow, and it creates no package. Product/runtime smoke is not applicable.

On that baseline C4-III stayed in progress with exact-head verification passed; exact-package verification stayed blocked by the packaged-artifact prerequisite and was never relabelled PASS; C4-III lifecycle closure stayed incomplete; Restore was still unimplemented and product release readiness was not claimed.

---

## 2026-08-12 — D3 macOS package MVP implemented

PR #191 merged as `9b2d3ffa243dfaba074e4cd48bf98b61e30ba952`, carrying the CR-012 / ADR 0019 authorization. On that baseline, `D3 — macOS package MVP` is **IMPLEMENTED**, outside C4-III.

```text
D3 — macOS package MVP — IMPLEMENTED
```

At that time the stage carried the additional note that C4-III exact-package verification was still to come; it has since run and passed, and the note is retired.

`make package-macos` now performs a real macOS build and produces `dist/CosmeticWorkshopOS-mac.zip` containing a user-openable `CosmeticWorkshopOS.app`. The three placeholder scripts — `scripts/build_frontend.sh`, `scripts/build_backend.sh`, `scripts/package_macos.sh` — are real implementations. Build products are not committed.

What the package contains: the unchanged launcher, the unchanged backend and its migrations, a self-contained relocatable CPython, the production frontend build, offline help and a build manifest. What it does not contain: any user database, backup, export, attachment, log, credential, secret, `.git`, `node_modules` or test suite. User data stays in the existing external user-data directory.

Preserved architecture. The backend is still a separate launcher-owned OS process started as `sys.executable -m app.launcher_backend_entrypoint`, keeping the backend-liveness lock, the pre-import socket bind and the inherited one-run `pass_fds` handshake exactly as audited. The launcher still owns Restore, the ADR 0018 loopback control plane and macOS picker are unchanged, and the ordinary system browser is still the presentation surface on the existing `http://127.0.0.1:5173` origin. **No protected closed Restore production file changed.** A real interpreter is bundled rather than a frozen binary precisely because freezing would break the `-m` and `sys.executable` contracts the Restore engine depends on.

New production-support code lives in `macos_package/`: the packaged entrypoint, a standard-library localhost frontend server that serves `frontend/dist` and proxies only `/api/*` to the local backend, fixed-catalogue macOS startup alerts for a Finder launch with no terminal, and the package-structure verifier that gates every build.

Build-only dependency under the six ADR 0019 conditions: `astral-sh/python-build-standalone` release `20260807`, CPython `3.12.13`, downloaded over HTTPS with a per-architecture SHA-256 pinned and verified before use, failing closed on mismatch, cached outside the repository. The end user installs nothing; the packaged product refuses to run on a foreign interpreter. Built for the current Mac architecture; universal binaries are out of scope.

No signing, notarization, DMG, installer, updater, release channel or upload was added. D4 and D5 remain NOT AUTHORIZED BY CR-012.

At the time of that entry C4-III stayed open on exact-head evidence alone: the exact-package prerequisite was closed, but exact-package verification was not yet passed, and the recorded `INCONCLUSIVE — ENVIRONMENT` classification stood unchanged as history. The D3 Level-5 package smoke proves the package/runtime delivery layer and is never reported as C4-III exact-package verification.

---

## 2026-08-12 — C4-III exact-package verification PASSED, Restore lifecycle closed

PR #192 (`D3 — Implement macOS package MVP`, implementation head `62bac3d9500994acc116ead2c7d6caf0b32d9ead`) merged as `0e1193264dc22979ca48e32a962aba916b6b520e`. The independent external test-only verifier then ran against the packaged runtime built from that exact published `main`.

Accepted verifier:

```text
published main:
0e1193264dc22979ca48e32a962aba916b6b520e

runner version:
c4-iii-restore-exact-package-v1.2

runner SHA-256:
2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694

return code: 0

PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED
PASS — FULL AUTOMATED SMOKE PASSED
```

Eight accepted exact-package scenarios on the packaged runtime:

1. current-schema Restore — `restore_completed`; selected source SHA-256 unchanged; `before_restore` safety copy retained; backend restarted successfully.
2. supported older-schema Restore — migration to the current schema succeeded; `restore_completed`; selected source unchanged; `before_restore` safety copy retained; backend restarted successfully.
3. invalid source rejection — rejected before destructive execution; working database unchanged; source unchanged; no durable Restore operation; no `before_restore` safety copy.
4. source changed after validation — stale retained source proof rejected; final browser/control state `restore_failed`; working database unchanged; no durable Restore operation; no `before_restore` safety copy.
5. pre-replacement interruption — starting phase `source_staged`; recovered to `aborted`; workspace unchanged; ordinary startup allowed.
6. actual hard interruption after accepted execute — real durable crash phase `replacement_intent`; the runner hard-stopped only its own packaged process group; the next packaged launch recovered through rollback to `rolled_back`; previous workspace restored; selected source unchanged; `before_restore` safety copy retained; ordinary startup recovered.
7. interrupted rollback — starting phase `rollback_in_progress`; recovered to `rolled_back`; previous workspace restored; safety copy retained; repeated launch remained safe and stable.
8. missing safety copy after replacement — starting phase `replacement_committed`; recovered to `recovery_blocked`; packaged exit code `3`; ordinary startup refused; operation evidence retained.

Runner cleanup after the accepted run: `owned processes left: none`, `owned ports still held: none`.

**Runner history is preserved truthfully and is not counted against the product.** An earlier runner version failed before package execution because the external fixture helper had an incorrect fixture `PYTHONPATH`; it was correctly classified `INCONCLUSIVE — RUNNER`. `v1.1` then produced a textual `FAIL — PRODUCT` during the hard-interruption probe, but inspection proved that verdict was caused by a runner programming error — `UnboundLocalError: cannot access local variable 'x' where it is not associated with a value` — so it is invalid as product evidence and is retained as historical runner-fault evidence, never as a real product failure. `v1.2` corrected the runner probe/classification boundary and produced the accepted full PASS. No verification attempt found a product defect and no defect-fix PR was required.

The verifier is external test-only evidence identified by version and SHA-256, and is deliberately not committed to this repository.

C4-III therefore closes on the combination of the previously accepted exact-head PASS on `81e8193596709b0c16d0ecad598458b3ea95fd9c` and this accepted exact-package PASS on `0e1193264dc22979ca48e32a962aba916b6b520e`. Neither half alone was ever sufficient. The earlier `INCONCLUSIVE — ENVIRONMENT` result is not rewritten, reclassified or upgraded by this closure; it remains the correct record of a run made before the packaged prerequisite existed.

This closure changeset is documentation, state and lifecycle-checker only. It changes no launcher, backend, frontend, migration, packaging-runtime, dependency or lockfile, and no Restore production, HTTP/control-plane or presentation behavior. The pre-change active documents are preserved byte-identically in `docs/history/c4-iii-pre-closure/`.

Resulting lifecycle: C4-III is DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED; `C4-III LIFECYCLE CLOSURE — COMPLETED BY THIS CHANGESET`; `Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`, as a consequence of the closure alone; `D3 — macOS package MVP — IMPLEMENTED`. `D4 — Update safety` and `D5 — Remote install checklist` remain NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE, signing, notarization, DMG, auto-update, release-channel, App Store, sandbox-migration and cloud/sync work remain unauthorized, and product release readiness remains NOT CLAIMED.
