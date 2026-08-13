# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-12`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction. ADR 0017 remains authoritative for the C4 slice split and C4-III verification/lifecycle-closure purpose. ADR 0019 is authoritative for the bounded `D3 — macOS package MVP` authorization decided by `CR-012`; it amends none of the Restore ADRs.

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

The macOS package MVP exists (D3). Safe packaged update flow, installation verification and full release-candidate smoke remain incomplete, and product release readiness is not claimed.

## C4-II-C closure baseline

- PR #188 final independently reviewed and exact-head-tested implementation head: `1df21915fdcf4a708dc778a0e762d64830b5b880`.
- PR #188 merge/new `main`: `6294f0044c792ced3ac56d213ea5333e33062f12`.
- Merged at: `2026-08-11T17:25:11Z`.
- PR #189 closed the C4-II-C lifecycle and authorized C4-III verification; its merge/new `main` is `81e8193596709b0c16d0ecad598458b3ea95fd9c`.
- The reviewed head is the C4-II-C parent of the merge commit; the merge introduced no additional product-file changes.

Accepted C4-II-C evidence:

- `git diff --check` PASS;
- documentation lifecycle checker PASS;
- 27 then-protected history blobs and 21 then-closed B1/C4-I/B2/B3/shell blobs verified before merge;
- frontend `npm ci` PASS with 0 vulnerabilities;
- frontend build PASS;
- focused Restore control suite **34 tests / 34 pass / 0 fail**;
- browser smoke v5.4 PASS, including completed/failed/blocked resume without replay, true 401/409 invalidation, ambiguous execute and narrow layout;
- fresh independent audit **P0=0 / P1=0 / P2=0 — AUDIT GATE PASS**;
- final no-change exact-head gate PASS;
- final local and remote head remained `1df21915fdcf4a708dc778a0e762d64830b5b880`.

Earlier failed audits and the aborted checker-only gate remain historical evidence and are preserved in `docs/history/c4-ii-c-pre-closure/` and the PR record; they are not relabelled as PASS.

## Closed authority chain through C4-II-C

```text
A3/A1 source selection + validation
→ B1 source-proof binding
→ B2 authenticated one-shot execute authority
→ C4-I sole destructive engine
→ B3 explicit browser confirmation + exact replay
→ pathless restoring/final launcher state
→ C4-II-C truthful final/recovery/support presentation
```

Closed production seams are now immutable unless separately authorized: launcher/backend Restore authority, `restore-control-contract.ts`, `restore-control-runtime.ts`, `restore-control-entry.ts`, final C4-II-C `restore-control-presentation.ts`, `main.ts`, app navigation, ADR 0016 and ADR 0018.

## C4-II-C final product truth

- `restore_completed` is authoritative success and may offer ordinary navigation because B2 publishes it only after ordinary-backend readiness is proved.
- `restore_failed` is authoritative failed Restore truth with ordinary work available, without rollback/unchanged-data/old-data-restored inference.
- `restore_blocked` is authoritative restart/help-only truth; ordinary work is not confirmed safe.
- pending/restoring post-execute uncertainty without an authoritative final result remains unknown.
- an authenticated final B2 snapshot remains authoritative if same-tab replay metadata is missing; replay loss blocks further Restore commands but does not erase the final result.
- true session/protocol invalidation with cleared snapshot remains unknown + restart-only.
- ambiguous pending execute replay remains the exact same request ID, command sequence and generation, never a new Restore.

## C4-III exact-head verification baseline

This section records the **first** of the two required C4-III verification halves, exactly as it was reported. It is preserved unchanged; the exact-package half it could not execute is recorded separately below and was satisfied later, by a different run against a different baseline.

An independently executed external C4-III exact-head verifier ran against merged `main` and produced the following outer gates:

```text
C4III EXACT-HEAD OUTER GATE: PASS
C4III EXACT-PACKAGE OUTER GATE: INCONCLUSIVE — ENVIRONMENT
C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE
```

Exact verification baseline:

```text
expected / observed merged main:
81e8193596709b0c16d0ecad598458b3ea95fd9c

runner SHA-256:
4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a

runner version:
c4-iii-restore-exact-head-v1
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

The exact-package prerequisite was unavailable. Under the project smoke classification this is `INCONCLUSIVE — ENVIRONMENT`: it is not a product failure and not a runner failure, and it must never be recorded, summarized or inferred as a PASS. Exact-head PASS and exact-package INCONCLUSIVE remain separately labelled results.

That historical result is **not rewritten and not reclassified**. It was correct when it was produced, because no packaged prerequisite existed at that time. The later exact-package PASS below is a separate run, against a separate baseline, and it supersedes nothing about how this one was classified.

## C4-III exact-package verification baseline

This section records the **second** required half. The external test-only verifier ran against the packaged runtime built from exact published `main`:

```text
expected / observed published main:
0e1193264dc22979ca48e32a962aba916b6b520e

runner version:
c4-iii-restore-exact-package-v1.2

runner SHA-256:
2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694

return code: 0
```

Accepted outer results:

```text
PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED
PASS — FULL AUTOMATED SMOKE PASSED
```

That baseline is the merge commit of PR #192 (`D3 — Implement macOS package MVP`, implementation head `62bac3d9500994acc116ead2c7d6caf0b32d9ead`), whose Level-5 package smoke had already passed independently before merge.

### Accepted exact-package scenarios

1. **current-schema Restore** — `restore_completed`; selected source SHA-256 unchanged; `before_restore` safety copy retained; backend restarted successfully.
2. **supported older-schema Restore** — migration to the current schema succeeded; `restore_completed`; selected source unchanged; `before_restore` safety copy retained; backend restarted successfully.
3. **invalid source rejection** — rejected before destructive execution; working database unchanged; source unchanged; no durable Restore operation; no `before_restore` safety copy.
4. **source changed after validation** — stale retained source proof rejected; final browser/control state `restore_failed`; working database unchanged; no durable Restore operation; no `before_restore` safety copy.
5. **pre-replacement interruption** — starting phase `source_staged`; recovered to `aborted`; workspace unchanged; ordinary startup allowed.
6. **actual hard interruption after accepted execute** — real durable crash phase observed at `replacement_intent`; the runner intentionally hard-stopped only its own packaged process group; the next packaged launch recovered through rollback to durable phase `rolled_back`; previous workspace restored; selected source unchanged; `before_restore` safety copy retained; ordinary startup recovered.
7. **interrupted rollback** — starting phase `rollback_in_progress`; recovered to `rolled_back`; previous workspace restored; safety copy retained; repeated launch remained safe and stable.
8. **missing safety copy after replacement** — starting phase `replacement_committed`; recovered to `recovery_blocked`; packaged exit code `3`; ordinary startup refused; operation evidence retained.

Scenario 6 is the load-bearing durability evidence: a real `replacement_intent -> rolled_back` recovery observed on the packaged runtime, not a simulated phase.

### Runner cleanup after the accepted run

```text
owned processes left: none
owned ports still held: none
```

### External runner history

Three external exact-package runner attempts preceded acceptance. All three are preserved truthfully, and **none of the first two is a product defect**:

- an earlier runner version failed before package execution because the external fixture helper had an incorrect fixture `PYTHONPATH`. It was correctly classified `INCONCLUSIVE — RUNNER`;
- `v1.1` produced a textual `FAIL — PRODUCT` during the hard-interruption probe. Inspection proved that verdict was caused by a runner programming error — `UnboundLocalError: cannot access local variable 'x' where it is not associated with a value` — so it is **invalid as product evidence** and is preserved as historical runner-fault evidence, never as a real product failure;
- `v1.2` corrected the runner probe/classification boundary and produced the accepted full PASS recorded above.

No product defect was found by any of the three attempts, and no product, runtime or migration file was changed in response to them.

The verifier is external test-only evidence and is **not committed to this repository**. It is identified by version and SHA-256 only.

## C4-III status

**C4-III — Restore end-to-end verification and lifecycle closure** is **DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED**.

Both required halves of the ADR 0017 evidence surface are now satisfied, and only their combination closes the slice:

```text
C4-III EXACT-HEAD VERIFICATION — PASS       81e8193596709b0c16d0ecad598458b3ea95fd9c
C4-III EXACT-PACKAGE VERIFICATION — PASS    0e1193264dc22979ca48e32a962aba916b6b520e
C4-III LIFECYCLE CLOSURE — COMPLETED BY THIS CHANGESET
```

Exact-head evidence alone never closed C4-III and never could have. The packaged prerequisite was produced by D3 outside C4-III under CR-012, and the D3 Level-5 package smoke was never counted as exact-package verification — D3 proves the package/runtime delivery layer, while the C4-III verifier exercises the packaged Restore flow.

Verified verification scope, from ADR 0017:

- current-schema Restore;
- supported older-schema Restore;
- rejection paths;
- interruption;
- rollback;
- repeated launch / startup recovery;
- selected-source immutability;
- mandatory safety-copy retention;
- end-to-end lifecycle closure.

C4-III was verification/lifecycle work, not authority redesign. It added focused tests, isolated external smoke runners, verification documentation and lifecycle/checker evidence. It changed no production behavior and reopened no closed authority. No accepted verification established a product defect, so no bounded defect-fix PR was required. The v1.1 runner emitted a textual `FAIL — PRODUCT`, but inspection proved that classification invalid as product evidence because it originated from the runner's own `UnboundLocalError`.

Exact-package verification required by ADR 0017 never silently authorized packaging implementation. While the prerequisite was unavailable that verification was recorded as incomplete, and the artifact was produced later by D3 under its own authorization rather than by adding packaging/update work under C4-III.

## C4-III lifecycle closure

`C4-III LIFECYCLE CLOSURE — COMPLETED BY THIS CHANGESET`.

Closure follows from the combination of the two accepted independent results and nothing else:

```text
accepted exact-head PASS      +  accepted exact-package PASS
81e8193596709b0c16d0ecad598458b3ea95fd9c
                                 0e1193264dc22979ca48e32a962aba916b6b520e
→ C4-III closed
→ Restore implemented
```

`Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`. Restore becomes implemented only as a consequence of this lifecycle closure; no Restore runtime behavior changed to reach it. The closure changeset is documentation, state and lifecycle-checker only.

What closure explicitly does **not** grant:

- `Product release readiness — NOT CLAIMED`. Exact-package verification proves packaged Restore behavior; it is not evidence of release readiness;
- `D4 — Update safety — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE`;
- `D5 — Remote install checklist — NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE`;
- no signing, notarization, DMG, installer, auto-update, release-channel, App Store, sandbox-migration, cloud-deployment or cloud-sync authorization.

Safe packaged update flow, installation verification and full release-candidate smoke remain separate future work needing separate authorization.

## CR-012 — accepted D3 macOS package MVP authorization

`CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification` is **ACCEPTED**. The normative decision is [`decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](decisions/0019-c4-iii-packaged-artifact-prerequisite.md); this profile carries only the lifecycle reference.

The exact-package verifier correctly reported `INCONCLUSIVE — ENVIRONMENT` because the required packaged artifact was unavailable. Separately, no packaging implementation had yet been authorized to produce that artifact. CR-012 closes only that authorization gap. It does not reclassify or amend the previously recorded verification result.

It authorized the existing roadmap stage as the one bounded successor implementation task, outside C4-III:

```text
D3 — macOS package MVP — IMPLEMENTED

Original purpose:
produce the packaged product artifact required for
C4-III exact-package verification.
```

That purpose is now served: the accepted exact-package run above executed against the packaged runtime built from this stage.

`D3 — macOS package MVP` is the roadmap's own stage. CR-012 authorizes it rather than introducing a parallel packaging phase, and D3's roadmap scope, tests and non-goals stay authoritative.

That task packages the existing local-first architecture — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip`. It preserves the browser-first product surface and the ADR 0018 Restore architecture, introduces no desktop application shell, no second product UI, no new Restore transport and no backend Restore endpoint, and keeps user data outside the package.

The earlier blanket rule — that packaging implementation had no authorization at all — is now narrower and truthful: **CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization.** Signing, notarization, mandatory DMG, installer redesign, auto-update, update download, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation, D4 update safety and D5 remote-install work remain NOT AUTHORIZED.

The decision itself created no package. The D3 implementation then did.

## D3 — implemented

```text
D3 — macOS package MVP — IMPLEMENTED
```

`IMPLEMENTED` is the final D3 status recorded here. It is deliberately conservative: it claims a built, verified-structure macOS package MVP and nothing more. It does not claim release readiness, App Store readiness, notarization, signing, a DMG, an updater or universal packaging, none of which D3 built or was authorized to build.

`make package-macos` produces `dist/CosmeticWorkshopOS-mac.zip` containing a user-openable `CosmeticWorkshopOS.app`. The package carries the unchanged launcher, the unchanged backend, a self-contained pinned CPython, the production frontend build, migrations and offline help. The end user needs no Git, Python, Node.js, npm, Docker, GitHub, Codex or terminal. User data stays in the existing external user-data directory. Build details are in [`packaging.md`](packaging.md).

D3 changed no protected closed Restore production file. The backend remains a separate launcher-owned process started through `app.launcher_backend_entrypoint` with the existing lock/socket handshake, the launcher remains the Restore authority, and the ordinary browser remains the presentation surface.

What D3 did **not** do:

- D3 did not run C4-III exact-package verification;
- D3 did not by itself advance C4-III lifecycle closure;
- it did not implement Restore;
- it did not make the product release-ready;
- it did not authorize D4, D5, signing, notarization, DMG, auto-update or App Store work.

The D3 Level-5 package smoke proves the package/runtime delivery layer, and it passed independently before PR #192 merged. It was never the C4-III exact-package gate. That gate was the separate independent verifier recorded above, run against the packaged runtime.

Product release readiness remains NOT CLAIMED.
