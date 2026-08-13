# Handoff

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

PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12`. C4-II-C is DONE — MERGED AND EXACT-HEAD VERIFIED.

Accepted C4-II-C evidence: lifecycle/build PASS; Restore 34/34 PASS; browser smoke v5.4 PASS; fresh independent audit P0=0/P1=0/P2=0; final no-change gate PASS.

## Recorded C4-III verification result — exact-head half

An external verifier `c4-iii-restore-exact-head-v1` (SHA-256 `4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a`) ran on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c` and reported `lifecycle`, `focused_restore_pytest`, `frontend_npm_ci`, `frontend_build`, `frontend_restore_tests` and `destructive_e2e_current_and_older` all PASS — `PASS — C4-III EXACT-HEAD VERIFICATION PASSED`.

The exact-package half of that run returned `INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE`, leaving `C4-III LIFECYCLE CLOSURE GATE: BLOCKED — PACKAGE PREREQUISITE`. That classification was correct at the time and is preserved unchanged. It is never treated as a PASS, and packaging was never implemented inside C4-III to clear it.

## Recorded C4-III verification result — exact-package half

The independent external test-only verifier `c4-iii-restore-exact-package-v1.2` (SHA-256 `2e2abad2e10030faecc43ff5d95d55d2a384791d88099f18a3cb8ee6b6506694`) ran against the packaged runtime built from exact published `main` `0e1193264dc22979ca48e32a962aba916b6b520e`, returned code `0`, and reported:

```text
PASS — C4-III EXACT-PACKAGE RESTORE VERIFICATION PASSED
PASS — FULL AUTOMATED SMOKE PASSED
```

Accepted packaged evidence against the load-bearing verification targets:

- current-schema success — `restore_completed`, selected source SHA-256 unchanged, `before_restore` safety copy retained, backend restarted successfully;
- supported older-schema Restore — migration to the current schema succeeded, then `restore_completed` with the source unchanged and the safety copy retained;
- pre-mutation rejection — invalid source rejected before destructive execution; working database, source and durable state untouched, and no `before_restore` safety copy created;
- stale-proof rejection — a source changed after validation was rejected, final state `restore_failed`, working database unchanged, no durable Restore operation;
- interruption and conservative startup recovery — `source_staged` recovered to `aborted` with the workspace unchanged and ordinary startup allowed;
- rollback / failed truth — an **actual hard interruption after accepted execute** produced the real durable crash phase `replacement_intent`; the next packaged launch recovered through rollback to `rolled_back`, restoring the previous workspace with the source unchanged and the safety copy retained;
- interrupted rollback — `rollback_in_progress` recovered to `rolled_back`, safety copy retained, repeated launch safe and stable;
- blocked ordinary-startup refusal — `replacement_committed` with a missing safety copy recovered to `recovery_blocked`, packaged exit code `3`, ordinary startup refused, operation evidence retained;
- source immutability / proof binding and mandatory `before_restore` retention held across every accepted destructive scenario.

Runner cleanup: `owned processes left: none`, `owned ports still held: none`.

Runner history, preserved and **never counted as product defects**: an earlier version was correctly classified `INCONCLUSIVE — RUNNER` after an incorrect fixture `PYTHONPATH` stopped it before package execution; `v1.1` produced a textual `FAIL — PRODUCT` in the hard-interruption probe that inspection traced to a runner `UnboundLocalError`, making it invalid as product evidence; `v1.2` corrected the probe/classification boundary and produced the accepted PASS.

The verifier is external test-only evidence identified by version and SHA-256. It is not committed to this repository.

## Authorized handoff

C4-III — **Restore end-to-end verification and lifecycle closure** — is **DONE — EXACT-HEAD AND EXACT-PACKAGE VERIFIED**, closed by this changeset on the combination of both accepted halves.

The next agent inherits a **closed** Restore lifecycle. `Restore — IMPLEMENTED — C4-III VERIFIED AND LIFECYCLE-CLOSED`, purely as a consequence of that closure; no Restore runtime behavior changed to reach it.

Closed production files must remain byte-identical, including launcher/backend Restore authority, contract/runtime/entry, final C4-II-C presentation, main/navigation and ADRs. There is no open Restore slice to extend them under.

Do not read this closure as a release gate. Product release readiness stays **NOT CLAIMED**, `D4 — Update safety` and `D5 — Remote install checklist` stay **NOT AUTHORIZED BY CR-012 OR C4-III CLOSURE**, and signing, notarization, DMG, auto-update, release-channel, App Store, sandbox-migration and cloud/sync work stay unauthorized. Any of that needs a new decision or change request.

If a future defect appears in Restore, open a separate bounded defect-fix PR against the closed boundary rather than reopening C4-III.

## Completed task — D3 macOS package MVP

```text
D3 — macOS package MVP — IMPLEMENTED
```

`CR-012` is ACCEPTED; the normative decision is [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](../docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md).

One bounded implementation task, outside C4-III: it packaged the existing architecture unchanged — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip` containing `CosmeticWorkshopOS.app`. The package carries the launcher, a bundled self-contained CPython runtime, the production frontend build, migrations, configuration/resources and offline help. It carries no user database, backups, exports, attachments, logs, credentials, secrets or repository working data. The packaged user needs no Git, Python, Node.js, npm, Docker, GitHub, Codex, terminal or manual shell command.

Not introduced: Electron, Tauri, pywebview, a PyObjC shell, a second product UI, a WebView replacement for the browser UI, a new Restore transport, a backend Restore endpoint, or any change to ADR 0016/0018 Restore ownership and security semantics. CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization — signing, notarization, mandatory DMG, auto-update, App Store, sandbox migration, release-channel infrastructure, D4 and D5 stay NOT AUTHORIZED. The one build-only dependency is a pinned, checksum-verified relocatable CPython, under the six ADR 0019 conditions.

Build and run it with:

```bash
make package-macos
```

Building the artifact did not close C4-III and did not implement Restore. The external exact-package verifier had to run and pass against the packaged runtime, and it did — separately, and recorded above. The D3 Level-5 package smoke covers the package/runtime delivery layer and is never reported as C4-III exact-package verification.

`IMPLEMENTED` is D3's final status and claims nothing more than a built macOS package MVP — no release readiness, App Store readiness, notarization, signing, DMG, updater or universal packaging.

Product release readiness remains NOT CLAIMED.
