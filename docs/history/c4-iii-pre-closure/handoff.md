# Handoff

Updated: `2026-08-12`

## Current lifecycle

```text
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
C4-III — IN PROGRESS — EXACT-HEAD VERIFICATION PASSED
C4-III EXACT-PACKAGE VERIFICATION — NOT YET PASSED
C4-III LIFECYCLE CLOSURE — NOT COMPLETED
CR-012 — ACCEPTED — D3 MACOS PACKAGE MVP AUTHORIZATION
D3 — macOS package MVP — IMPLEMENTED — C4-III EXACT-PACKAGE VERIFICATION PENDING
D4 — Update safety — NOT AUTHORIZED BY CR-012
D5 — Remote install checklist — NOT AUTHORIZED BY CR-012
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed predecessor

PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12`. C4-II-C is DONE — MERGED AND EXACT-HEAD VERIFIED.

Accepted C4-II-C evidence: lifecycle/build PASS; Restore 34/34 PASS; browser smoke v5.4 PASS; fresh independent audit P0=0/P1=0/P2=0; final no-change gate PASS.

## Recorded C4-III verification result

An external verifier `c4-iii-restore-exact-head-v1` (SHA-256 `4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a`) ran on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c` and reported `lifecycle`, `focused_restore_pytest`, `frontend_npm_ci`, `frontend_build`, `frontend_restore_tests` and `destructive_e2e_current_and_older` all PASS — `PASS — C4-III EXACT-HEAD VERIFICATION PASSED`.

The exact-package half returned `INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE`, leaving `C4-III LIFECYCLE CLOSURE GATE: BLOCKED — PACKAGE PREREQUISITE`.

## Authorized handoff

C4-III — **Restore end-to-end verification and lifecycle closure** — is **IN PROGRESS — EXACT-HEAD VERIFICATION PASSED**.

The next agent inherits an open slice. Its original blocking prerequisite — no packaged product artifact to run exact-package verification against — has been closed by D3, outside C4-III. Do not treat the recorded INCONCLUSIVE as a PASS, do not close C4-III on exact-head evidence alone, and do not implement packaging to clear it inside C4-III. What remains is to write and run the independent exact-package verifier against the packaged runtime; producing the artifact was separate work under its own authorization — `CR-012`, described below.

Load-bearing verification targets:

- current-schema success;
- supported older-schema Restore;
- pre-mutation rejection;
- interruption and conservative startup recovery;
- rollback / failed truth;
- blocked ordinary-startup refusal;
- repeated launch;
- source immutability / proof binding;
- verified `before_restore` safety-copy retention;
- browser privacy and exact replay;
- lifecycle closure evidence.

Exact-head evidence for these targets is recorded above; the exact-package evidence required alongside it is still missing. It is now *obtainable*: build the package with `make package-macos` and run the verifier against the extracted `CosmeticWorkshopOS.app`, never against a source-tree fallback.

Closed production files must remain byte-identical, including launcher/backend Restore authority, contract/runtime/entry, final C4-II-C presentation, main/navigation and ADRs. C4-III may extend focused tests and external smoke runners.

If a verification case exposes a product defect, do not patch it inside the verification claim. Open a separate bounded defect-fix PR, test exact head, then resume C4-III.

## Completed task — D3 macOS package MVP

```text
D3 — macOS package MVP — IMPLEMENTED — C4-III EXACT-PACKAGE VERIFICATION PENDING
```

`CR-012` is ACCEPTED; the normative decision is [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](../docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md).

One bounded implementation task, outside C4-III: it packaged the existing architecture unchanged — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip` containing `CosmeticWorkshopOS.app`. The package carries the launcher, a bundled self-contained CPython runtime, the production frontend build, migrations, configuration/resources and offline help. It carries no user database, backups, exports, attachments, logs, credentials, secrets or repository working data. The packaged user needs no Git, Python, Node.js, npm, Docker, GitHub, Codex, terminal or manual shell command.

Not introduced: Electron, Tauri, pywebview, a PyObjC shell, a second product UI, a WebView replacement for the browser UI, a new Restore transport, a backend Restore endpoint, or any change to ADR 0016/0018 Restore ownership and security semantics. CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization — signing, notarization, mandatory DMG, auto-update, App Store, sandbox migration, release-channel infrastructure, D4 and D5 stay NOT AUTHORIZED. The one build-only dependency is a pinned, checksum-verified relocatable CPython, under the six ADR 0019 conditions.

Build and run it with:

```bash
make package-macos
```

Building the artifact did not close C4-III and did not implement Restore. The external exact-package verifier must still run and pass against the packaged runtime. The D3 Level-5 package smoke covers the package/runtime delivery layer and is never reported as C4-III exact-package verification.

Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
