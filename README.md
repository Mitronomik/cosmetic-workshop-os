# cosmetic-workshop-os

Client-facing product name: **Мастерская косметолога**.

A local-first working system for a cosmetic workshop. The user product must run without requiring GitHub, Git, Python, Node.js, Docker or a terminal.

## Current product status

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

PR #188 reviewed exact C4-II-C head `1df21915fdcf4a708dc778a0e762d64830b5b880` and merged as `6294f0044c792ced3ac56d213ea5333e33062f12` at `2026-08-11T17:25:11Z`. PR #189 closed the C4-II-C lifecycle and merged as `81e8193596709b0c16d0ecad598458b3ea95fd9c`.

## Closed Restore implementation chain through C4-II-C

C4-I remains the only destructive Restore engine. B1 binds launcher-private retained source proof to C4-I intake. B2 owns authenticated one-shot `/v1/restore/execute` authority transfer and ordinary-backend restart handoff. B3 owns explicit browser confirmation and exact destructive replay. C4-II-C owns truthful final/recovery presentation without changing Restore authority.

Accepted C4-II-C evidence on the reviewed head:

- `git diff --check` PASS;
- lifecycle checker PASS;
- frontend install/build PASS with 0 vulnerabilities;
- focused Restore control suite **34/34 PASS**;
- browser smoke v5.4 PASS, including real resume-without-replay final-state precedence, true 401/409 invalidation, ambiguous execute and narrow layout;
- fresh independent audit **P0=0 / P1=0 / P2=0 — PASS**;
- final no-change exact-head gate PASS;
- final local and remote head unchanged.

The browser still has no filesystem/source authority. No source path, proof, digest, operation ID, database path, backup path or lock path crosses the browser boundary. No `/v1/restore/confirm` endpoint exists.

## Current work

**C4-III — Restore end-to-end verification and lifecycle closure** is **IN PROGRESS — EXACT-HEAD VERIFICATION PASSED**. It is the only open Restore slice.

Its purpose is verification and closure of the already-merged Restore chain: current-schema and supported older-schema Restore, rejection paths, interruption, rollback, repeated launch, source immutability, safety-copy retention and lifecycle closure.

An external exact-head verifier ran on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c` and reported:

```text
lifecycle PASS
focused_restore_pytest PASS
frontend_npm_ci PASS
frontend_build PASS
frontend_restore_tests PASS
destructive_e2e_current_and_older PASS

PASS — C4-III EXACT-HEAD VERIFICATION PASSED
```

The exact-package half of the same verification could not run:

```text
INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE
```

No packaged product artifact existed when the verifier ran, so `C4-III EXACT-PACKAGE VERIFICATION — NOT YET PASSED` and `C4-III LIFECYCLE CLOSURE — NOT COMPLETED`. That was an environment prerequisite, not a product failure and not a runner failure, and it is not counted as a PASS. D3 has since produced the artifact, outside C4-III; the exact-package verifier still has to run against it and pass. Full evidence is in [`docs/current-lifecycle.md`](docs/current-lifecycle.md).

C4-III does **not** authorize a new Restore engine, endpoint, browser filesystem authority, destructive command, packaging/update implementation or redesign, or hidden product-behavior change. Packaging was not built inside C4-III to unblock the missing artifact — it was built by D3 under its own authorization. If verification finds a product defect, fix it in a separate bounded defect PR and rerun the affected exact-head verification before C4-III can close.

Restore remains **NOT IMPLEMENTED** until C4-III itself completes and lifecycle closure is accepted. Product release readiness remains **NOT CLAIMED**.

## D3 macOS package MVP — implemented

```text
D3 — macOS package MVP — IMPLEMENTED — C4-III EXACT-PACKAGE VERIFICATION PENDING
```

`CR-012` is **ACCEPTED**. The normative decision is [`docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](docs/decisions/0019-c4-iii-packaged-artifact-prerequisite.md). It authorized exactly one bounded implementation task, run outside C4-III: package the existing architecture — launcher → local backend on `127.0.0.1` → built frontend → ordinary system browser → external user-data directory — as `CosmeticWorkshopOS-mac.zip` containing a simple `CosmeticWorkshopOS.app`, so that exact-package verification becomes runnable against a real packaged runtime.

Building the package on a Mac:

```bash
make package-macos
```

It produces `dist/CosmeticWorkshopOS-mac.zip`. The user unzips it and opens `CosmeticWorkshopOS.app`; the launcher starts, the local backend starts, the production frontend is served locally and the ordinary browser opens. No Git, Python, Node.js, npm, Docker, GitHub, Codex or terminal is needed to run it. Build products are never committed. See [`docs/packaging.md`](docs/packaging.md).

The packaging task changed no product topology and introduced no desktop application shell (Electron, Tauri, pywebview, PyObjC), no second product UI, no new Restore transport and no backend Restore endpoint. No protected closed Restore production file was modified. User data stays outside the package.

CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization. Signing, notarization, mandatory DMG, auto-update, App Store, sandbox migration, cloud deployment/sync, D4 update safety and D5 remote-install work remain **NOT AUTHORIZED** — matching the roadmap's own D3 non-goals. The package is a verification prerequisite — never product release readiness.

## Restore authority

- ADR 0016 — destructive Restore safety/state machine;
- ADR 0018 — launcher control/picker/exact-run browser-session architecture;
- ADR 0017 — C4 split and C4-III verification/lifecycle-closure purpose;
- `docs/current-lifecycle.md` — current lifecycle authority;
- `docs/c4-ii-b-implementation-slices.md` — closed B1→B3 contract;
- `docs/restore-interaction-and-validation-session.md` — active browser/control interaction profile.
