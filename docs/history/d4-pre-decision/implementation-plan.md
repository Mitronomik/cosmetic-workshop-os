# cosmetic-workshop-os — Active implementation plan

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

## Closed predecessor

PR #188 reviewed exact head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`, closing C4-II-C.

Accepted C4-II-C evidence: lifecycle PASS; frontend install/build PASS; focused Restore **34/34 PASS**; browser smoke v5.4 PASS; fresh independent audit P0=0/P1=0/P2=0; final no-change exact-head gate PASS.

Final C4-II-C production file `frontend/src/restore-control-presentation.ts` is now a closed boundary together with the already-closed contract/runtime/entry/launcher/backend/main/navigation seams.

PR #189 closed the C4-II-C lifecycle and authorized C4-III; it merged as `81e8193596709b0c16d0ecad598458b3ea95fd9c`.

## Current implementation window

### C4-III — Restore end-to-end verification and lifecycle closure

Status: **DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED**. Lifecycle closure is carried by this changeset.

Goal:

```text
merged launcher-assisted Restore chain
→ verify current-schema Restore
→ verify supported older-schema Restore
→ verify rejection + interruption + rollback
→ verify repeated launch / startup recovery
→ prove source immutability + safety-copy retention
→ exact end-to-end evidence
→ lifecycle closure
```

### Allowed scope

- focused verification tests and test-only harnesses;
- isolated external exact-head smoke runners;
- verification/checklist documentation;
- lifecycle/state/checker updates required to record evidence;
- no production behavior change unless separately authorized as a bounded defect fix.

### Required verification

At minimum, C4-III must cover the reserved ADR 0017 verification surface:

1. current-schema successful Restore;
2. supported older-schema Restore through the existing migration/startup rules;
3. invalid/rejected candidate paths before destructive mutation;
4. interruption at safety-critical boundaries and conservative startup recovery;
5. rollback and `restore_failed` truth;
6. `restore_blocked` / recovery-blocked ordinary-startup refusal;
7. repeated launch after completed, failed/rolled-back and blocked outcomes;
8. immutable selected source / B1 proof binding;
9. mandatory verified `before_restore` safety-copy retention;
10. browser path/privacy and one-shot/exact-replay invariants;
11. exact-head or exact-package evidence with autonomous timeouts/cleanup;
12. independent P0/P1/P2 audit and final no-change gate.

Use the project smoke classification exactly: PASS / FAIL PRODUCT / INCONCLUSIVE RUNNER / INCONCLUSIVE ENVIRONMENT. Manual `Ctrl+C` invalidates PASS.

### Recorded verification progress — exact-head half

An external exact-head verifier (`c4-iii-restore-exact-head-v1`, SHA-256 `4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a`) ran on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`:

```text
C4III EXACT-HEAD OUTER GATE: PASS
C4III EXACT-PACKAGE OUTER GATE: INCONCLUSIVE — ENVIRONMENT
C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE
```

| Gate | Result |
|---|---|
| `lifecycle` | PASS |
| `focused_restore_pytest` | PASS |
| `frontend_npm_ci` | PASS |
| `frontend_build` | PASS |
| `frontend_restore_tests` | PASS |
| `destructive_e2e_current_and_older` | PASS |
| exact-head outer gate | **PASS — C4-III EXACT-HEAD VERIFICATION PASSED** |
| exact-package outer gate | **INCONCLUSIVE — ENVIRONMENT** — prerequisite unavailable |
| lifecycle closure gate | **BLOCKED — PACKAGE PREREQUISITE** |

At the time of that run only the exact-head half was satisfied. The exact-package half stayed `INCONCLUSIVE — ENVIRONMENT` because the packaged product artifact did not exist, and it is never rewritten as PASS, FAIL PRODUCT or INCONCLUSIVE RUNNER. Building one was not authorized inside C4-III; it was the separate authorized D3 successor task below.

### Recorded verification progress — exact-package half

The independent external test-only verifier (`c4-iii-restore-exact-package-v1.2`, SHA-256 `2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694`) ran against the packaged runtime built from exact published `main` `0e1193264dc22979ca48e32a962aba916b6b520e` and returned code `0`:

```text
PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED
PASS — FULL AUTOMATED SMOKE PASSED
```

| Accepted packaged scenario | Result |
|---|---|
| current-schema Restore | `restore_completed`, source SHA-256 unchanged, `before_restore` retained, backend restarted |
| supported older-schema Restore | migration to the current schema succeeded, then `restore_completed`, source unchanged, `before_restore` retained |
| invalid source rejection | rejected before destructive execution; database, source and durable state untouched; no safety copy |
| source changed after validation | stale retained source proof rejected; `restore_failed`; database unchanged; no durable operation |
| pre-replacement interruption | `source_staged` → `aborted`; workspace unchanged; ordinary startup allowed |
| actual hard interruption after accepted execute | real durable `replacement_intent` → recovered `rolled_back`; workspace restored; source unchanged; `before_restore` retained |
| interrupted rollback | `rollback_in_progress` → `rolled_back`; safety copy retained; repeated launch safe |
| missing safety copy after replacement | `replacement_committed` → `recovery_blocked`; packaged exit code `3`; ordinary startup refused |
| runner cleanup | `owned processes left: none`; `owned ports still held: none` |

Item 11 of the required verification list asks for exact-head **or** exact-package evidence with autonomous timeouts/cleanup. Both required halves are satisfied, and C4-III closes only on their combination.

Runner attempts before acceptance are preserved as runner faults and are **not product defects**: one `INCONCLUSIVE — RUNNER` caused by an incorrect fixture `PYTHONPATH`, and a `v1.1` textual `FAIL — PRODUCT` traced to a runner `UnboundLocalError`, which is invalid as product evidence. `v1.2` corrected the probe/classification boundary. The verifier stays external, identified by version and SHA-256, and is not committed here.

### Successor task — D3 macOS package MVP

Status: **IMPLEMENTED**. Decided by `CR-012` / [`decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](decisions/0019-c4-iii-packaged-artifact-prerequisite.md). It ran **outside** C4-III and was never merged into the C4-III verification claim. `IMPLEMENTED` claims a built macOS package MVP only — not release readiness, App Store readiness, notarization, signing, a DMG, an updater or universal packaging.

Goal:

```text
existing local-first architecture
→ package it unchanged
→ CosmeticWorkshopOS-mac.zip
→ self-contained user-openable macOS artifact
→ real exact-package C4-III verification becomes runnable
```

Bounded scope: launcher, bundled backend runtime, production frontend build, migrations, required configuration/resources and required offline help — packaged around the unchanged topology launcher → backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory. No user database, backups, exports, attachments, logs, credentials, secrets or repository working data inside the package. User data stays external and survives replacement/restart. No desktop application shell, second product UI, WebView replacement, new Restore transport or backend Restore endpoint. A build-only packaging tool is allowed only under the six ADR 0019 conditions; otherwise STOP and open a new decision.

CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, installer redesign, auto-update, update download, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation, D4 and D5 remain NOT AUTHORIZED — the roadmap D3 non-goals stay authoritative.

The artifact was a verification prerequisite. It did not close C4-III by itself, did not implement Restore and did not make the product release-ready. The stated condition — artifact exists **and** the external exact-package verifier runs and passes against the packaged runtime — has since been met, and only then did C4-III close.

As built: `make package-macos` produces `dist/CosmeticWorkshopOS-mac.zip` containing `CosmeticWorkshopOS.app`, with a pinned checksum-verified self-contained CPython, the production frontend served by a standard-library localhost listener with an `/api/*` proxy, and the backend still a separate launcher-owned process using the unchanged `app.launcher_backend_entrypoint` handshake. No protected closed Restore production file changed. See [`packaging.md`](packaging.md).

### Architecture constraints

C4-III did not authorize, and its closure does not authorize:

- a new Restore engine or second destructive path;
- a new launcher/control/backend endpoint or DTO field;
- browser filesystem/source authority;
- destructive cancel, blind retry or new request sequence;
- durable phase reconstruction in frontend;
- production refactor hidden inside verification;
- packaging or updater implementation or redesign inside the C4-III slice, including producing a `.app`, `.dmg`, ZIP or packaged runtime under the C4-III verification claim — that work belongs to the separate CR-012 successor task above;
- D4, D5, signing, notarization, auto-update or App Store work — not authorized by CR-012, and never to be performed inside C4-III;
- C4 lifecycle completion without the required evidence.

No verification attempt revealed a product defect, so no bounded defect-fix PR was needed. Had one appeared, the rule was to STOP the verification claim, fix it separately, rerun the affected checks and only then resume C4-III.

C4 lifecycle completion required the full evidence surface and got it: accepted exact-head PASS **and** accepted exact-package PASS. `Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`, as a consequence of that closure only.

Closure ends the Restore implementation programme. It starts no new one: `D4 — Update safety` and `D5 — Remote install checklist` remain NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE, and product release readiness remains NOT CLAIMED. Safe packaged update flow, installation verification and full release-candidate smoke still need separate authorization.
