# Packaging

Updated: `2026-08-12`

## Lifecycle

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

## C4-II-C closure / C4-III boundary

PR #188 / C4-II-C made no packaging, updater, helper-executable, dependency, port or installation-topology change. Its closure changes documentation/state/checker only. PR #189 and the C4-III partial-verification checkpoint likewise change no packaging surface.

C4-III is authorized for Restore end-to-end verification and lifecycle closure. ADR 0017 includes exact-package verification in that evidence, but this authorization does not authorize packaging implementation or redesign.

If a required packaged verification artifact is not yet available, C4-III must remain incomplete or report an environment/prerequisite gap. It must not hide packaging work inside the Restore verification slice.

## Active packaged-artifact prerequisite gap

That condition is now the live state, not a hypothetical:

```text
C4-III EXACT-PACKAGE VERIFICATION — BLOCKED BY PACKAGED ARTIFACT PREREQUISITE
```

The external C4-III verifier reported `PASS — C4-III EXACT-HEAD VERIFICATION PASSED` on merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c`, and `INCONCLUSIVE — ENVIRONMENT — EXACT-PACKAGE VERIFICATION PREREQUISITE UNAVAILABLE` for the packaged half, leaving `C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE`.

C4-III itself stays open and stays out of packaging. Inside the C4-III verification slice, do **not**:

- implement macOS packaging under C4-III;
- create a `.app`, `.dmg`, ZIP or packaged runtime to satisfy the gate;
- redesign packaging or updater architecture;
- relabel the exact-package result as PASS, FAIL PRODUCT or INCONCLUSIVE RUNNER;
- treat the passing exact-head half as sufficient for lifecycle closure.

## CR-012 — D3 macOS package MVP authorization

`CR-012` is **ACCEPTED**. The normative decision is [`decisions/0019-c4-iii-packaged-artifact-prerequisite.md`](decisions/0019-c4-iii-packaged-artifact-prerequisite.md).

The exact-package verifier correctly reported `INCONCLUSIVE — ENVIRONMENT` because the required packaged artifact was unavailable. Separately, no packaging implementation had yet been authorized to produce that artifact. CR-012 closes only that authorization gap. It does not reclassify or amend the previously recorded verification result.

It authorizes the existing roadmap stage as the one bounded successor implementation task, outside C4-III:

```text
D3 — macOS package MVP — AUTHORIZED NEXT — NOT IMPLEMENTED

Current purpose:
produce the packaged product artifact required for
C4-III exact-package verification.
```

`D3 — macOS package MVP` is the roadmap's own stage. CR-012 authorizes it rather than introducing a parallel packaging phase, and D3's roadmap scope, tests and non-goals stay authoritative.

That task packages the existing architecture and changes no product topology:

```text
macOS packaged product
→ existing local launcher
→ local backend on 127.0.0.1
→ built frontend
→ ordinary system browser / SPA
→ external user-data directory
```

Intended delivery shape is `CosmeticWorkshopOS-mac.zip` containing a self-contained, user-openable macOS product artifact — preferably a simple `CosmeticWorkshopOS.app` if that shape is reachable without changing the topology. The packaged user must not need Git, Python, Node.js, npm, Docker, GitHub, Codex, a terminal or manual shell commands. The package carries the launcher, a bundled backend runtime, the production frontend build, migrations, required configuration/resources and required offline help — and never a real user database, real backups, exports, attachments, logs, credentials, secrets or repository working data. User data stays outside the package and survives replacement and restart.

**No new desktop application shell is authorized.** Electron, Tauri, pywebview, a PyObjC shell, a second native product UI, a WebView replacement for the browser UI, a new Restore transport and a new backend Restore endpoint all remain unauthorized. ADR 0016 and ADR 0018 Restore ownership and security semantics are unchanged.

The bounded rule replaces the older blanket statement: **CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization.** Still NOT AUTHORIZED by CR-012: signing, notarization, mandatory DMG, installer redesign, auto-update, update download mechanism, GitHub Releases redesign, release-channel infrastructure, App Store, sandbox migration, cloud deployment, cloud sync, multi-user infrastructure, full release-candidate certification, general remote-install automation beyond testing this artifact, D4 update safety and D5 remote-install work. None of these belong to D3.

A future implementation PR may add a build-only packaging dependency or tool only under the six ADR 0019 conditions, and must STOP for a new decision if the artifact contract turns out to require a persistent runtime framework, desktop shell, sandbox model or Restore architecture change.

Producing the artifact is a verification prerequisite and is never product release readiness. Safe packaged update flow, installation verification and full release-candidate smoke remain separate future work needing separate authorization. Restore remains NOT IMPLEMENTED until C4-III closes. Product release readiness remains NOT CLAIMED.
