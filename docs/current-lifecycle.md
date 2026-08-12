# Current project lifecycle and documentation authority

Status: **CURRENT — NORMATIVE LIFECYCLE PROFILE**
Updated: `2026-08-12`

ADR 0016 remains authoritative for destructive Restore. ADR 0018 remains authoritative for launcher control, picker and exact-run browser-session interaction. ADR 0017 remains authoritative for the C4 slice split and C4-III verification/lifecycle-closure purpose. ADR 0019 is authoritative for the bounded minimal macOS packaged-artifact prerequisite decided by `CR-012`; it amends none of the Restore ADRs.

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
CR-012 — ACCEPTED — MINIMAL MACOS PACKAGED-ARTIFACT PREREQUISITE
Minimal macOS packaged-artifact prerequisite — AUTHORIZED NEXT — NOT IMPLEMENTED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

macOS packaging, safe packaged update flow, installation verification and full release-candidate smoke remain incomplete.

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

This checkpoint records the external verification result. It does not rerun, relabel or extend that verification, and it changes no product or runtime behavior.

## C4-III status

**C4-III — Restore end-to-end verification and lifecycle closure** is **IN PROGRESS — EXACT-HEAD VERIFICATION PASSED**.

Its remaining blocking condition is a prerequisite, not a defect:

```text
C4-III EXACT-PACKAGE VERIFICATION — BLOCKED BY PACKAGED ARTIFACT PREREQUISITE
C4-III LIFECYCLE CLOSURE — NOT COMPLETED
```

The required packaged product artifact does not yet exist, so the exact-package half of the ADR 0017 evidence surface cannot be executed. C4-III must remain open and incomplete in that condition. It must not be closed on exact-head evidence alone, and packaging must not be implemented inside C4-III to unblock it. Producing that artifact is separate work under its own authorization, now recorded as `CR-012` below.

Reserved verification scope, from ADR 0017:

- current-schema Restore;
- supported older-schema Restore;
- rejection paths;
- interruption;
- rollback;
- repeated launch / startup recovery;
- selected-source immutability;
- mandatory safety-copy retention;
- end-to-end lifecycle closure.

C4-III is verification/lifecycle work, not authority redesign. It may add or refine focused tests, isolated external smoke runners, verification documentation and lifecycle/checker evidence. It must not silently change production behavior or reopen closed authority. Any product defect found by C4-III requires a separate bounded defect-fix PR before the verification gate can pass.

Exact-package verification required by ADR 0017 does not silently authorize packaging implementation. That prerequisite is currently unavailable, so that verification is recorded as incomplete rather than being unblocked by adding packaging/update work under C4-III.

## CR-012 — accepted packaged-artifact prerequisite

`CR-012 — Minimal macOS packaged-artifact prerequisite for C4-III exact-package verification` is **ACCEPTED**. The normative decision is [`decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](decisions/0019-c4-iii-packaged-artifact-prerequisite.md); this profile carries only the lifecycle reference.

It authorizes exactly one bounded successor implementation task, outside C4-III:

```text
Minimal macOS packaged-artifact prerequisite — AUTHORIZED NEXT — NOT IMPLEMENTED
```

That task packages the existing local-first architecture — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip`. It preserves the browser-first product surface and the ADR 0018 Restore architecture, introduces no desktop application shell, no second product UI, no new Restore transport and no backend Restore endpoint, and keeps user data outside the package.

The earlier blanket rule — that packaging implementation had no authorization at all — is now narrower and truthful: **only the bounded minimal packaged-artifact prerequisite is authorized; full D3 / release packaging remains outside this authorization.** Signing, notarization, mandatory DMG, installer redesign, auto-update, update download, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation, full D4 update safety and D5 remote-install work remain NOT AUTHORIZED.

No package exists. This decision does not create one, does not run exact-package verification, and does not advance C4-III lifecycle closure.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
