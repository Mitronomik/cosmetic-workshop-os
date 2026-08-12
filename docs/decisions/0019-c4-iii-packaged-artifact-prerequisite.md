# ADR 0019 — D3 macOS package MVP as the C4-III exact-package prerequisite

## Status

`ACCEPTED` — 2026-08-12.

This ADR decides `CR-012 — D3 macOS package MVP authorization for C4-III exact-package verification`.

It authorizes the existing roadmap stage, unchanged, as the one bounded successor implementation task:

```text
D3 — macOS package MVP
— AUTHORIZED NEXT — NOT IMPLEMENTED

Current purpose:
produce the packaged product artifact required for
C4-III exact-package verification.
```

`D3 — macOS package MVP` is already defined in [`docs/roadmap.md`](../roadmap.md). This ADR does not invent a new packaging stage, does not redefine D3, and does not place a separate prerequisite phase before it. It gives the existing D3 stage its authorization and its current purpose, and it keeps D3's own roadmap scope, tests and non-goals authoritative.

It contains no packaging implementation. No packaged artifact exists on `main` as a result of this decision.

ADR 0016 remains authoritative for destructive Restore durable truth, the twelve phases, transition graph, startup recovery matrix, `replacement_intent`, immutable selected source, mandatory `before_restore` safety copy and the Restore AuditLog boundary. ADR 0018 remains authoritative for the launcher-owned loopback Restore control plane, launcher-owned macOS picker, exact-run browser-session security model and path privacy. ADR 0017 remains authoritative for the C4 slice split and for the purpose of C4-III. This ADR amends none of them.

## Context

C4-III — Restore end-to-end verification and lifecycle closure — is open and is **IN PROGRESS — EXACT-HEAD VERIFICATION PASSED**.

An independently executed external verifier (`c4-iii-restore-exact-head-v1`, SHA-256 `4c5c09081d2dc1db45ee556777039f4d9802f026d717a194c88c15d6894e5f3a`) ran against merged `main` `81e8193596709b0c16d0ecad598458b3ea95fd9c` and produced:

```text
C4III EXACT-HEAD OUTER GATE: PASS
C4III EXACT-PACKAGE OUTER GATE: INCONCLUSIVE — ENVIRONMENT
C4III LIFECYCLE CLOSURE: BLOCKED — PACKAGE PREREQUISITE
```

PR #190 recorded that result and merged as `1a5061b236cf7f69bca9ba533553e21401b94ab8`.

The exact-package half did not fail. It could not run, because **no packaged product artifact exists**. `scripts/package_macos.sh` is a placeholder that prints `TODO: implement in a future PR`. The launcher runs from the repository working tree via `python3 -m launcher.main`. There is no `.app`, no ZIP, no bundled backend runtime and no packaged production frontend.

Two separate facts must stay separate here.

The exact-package verifier correctly reported `INCONCLUSIVE — ENVIRONMENT` because the required packaged artifact was unavailable. Separately, no packaging implementation had yet been authorized to produce that artifact. CR-012 closes only that authorization gap. It does not reclassify or amend the previously recorded verification result.

That recorded result stands exactly as PR #190 captured it, and this ADR does not revisit it. What this ADR changes is governance: without an authorized packaging stage, C4-III had no route to the artifact, so it stayed unclosable by construction and Restore stayed frozen at `NOT IMPLEMENTED`.

This ADR closes that authorization gap and nothing else.

## Decision drivers

- C4-III lifecycle closure requires exact-package evidence that only a real packaged runtime can produce.
- Source-tree execution is not a substitute; an exact-package verifier must exercise the packaged runtime.
- The already-merged and audited Restore architecture must not be reopened, re-transported or re-owned in order to package it.
- The product is browser-first and local-first by accepted architecture; packaging must deliver that product, not a different one.
- The end user is non-technical and must not acquire developer tooling in order to run the product.
- The roadmap already has a stage for exactly this artifact; a parallel packaging stage would fragment the plan.
- D4, D5 and later release/distribution work are far larger than this stage and must not be smuggled in behind it.

## Considered alternatives

### Option A — leave C4-III blocked indefinitely

Advantage: changes nothing and risks nothing.

Rejected. Nothing about the recorded verification result needs revisiting; what is missing is an authorization to produce the artifact. Leaving that gap open makes C4-III unclosable by construction and freezes Restore at `NOT IMPLEMENTED` forever.

### Option B — authorize D3 together with D4, D5 and release readiness now

Advantage: one authorization would cover packaging, updates and release.

Rejected. D4 and D5 add update safety, remote-install automation and release-candidate certification, and the wider release programme adds signing, notarization and DMG/App Store distribution. None of that is required to run one exact-package verification, and bundling it here would turn a bounded stage into an unbounded release programme and would let "package exists" be misread as "product is releasable".

### Option B2 — invent a new pre-D3 packaging stage for the verification artifact

Advantage: a purpose-named stage would read as tightly scoped to C4-III.

Rejected. The roadmap's `D3 — macOS package MVP` already has precisely this scope — build frontend, build/package backend runtime, include migrations, include launcher, create `CosmeticWorkshopOS-mac.zip` or a simple `.app` if feasible — and precisely these non-goals: no signing, no auto-update, no App Store, no mandatory `.dmg`. A parallel stage would duplicate D3, leave two competing packaging plans and make the roadmap wrong. Authorize D3 itself instead.

### Option C — adopt a desktop application shell (Electron, Tauri, pywebview, PyObjC)

Advantage: a native shell is a conventional way to obtain a double-clickable macOS application.

Rejected. Every such shell replaces or duplicates the accepted browser-first presentation surface, introduces a second product UI or a WebView substitute for it, adds a persistent runtime framework and dependency class, and — most importantly — would put a new host process between the browser and the launcher-owned loopback Restore control plane decided in ADR 0018. That is an architecture redesign, not a packaging prerequisite. ADR 0018 already rejected adding PyObjC, Electron, Tauri, pywebview or a WebSocket framework by assumption; this ADR does not reverse that.

### Option D — authorize the existing roadmap D3 stage, packaging the architecture unchanged

Advantage: produces the artifact the verifier needs, uses the stage the roadmap already defines, and leaves product topology, Restore ownership, browser surface and user-data rules byte-for-byte as decided.

**Selected: Option D.**

## Decision

Authorize the existing roadmap stage `D3 — macOS package MVP` as the one bounded successor implementation task. Its current purpose is to produce the packaged product artifact required for C4-III exact-package verification. It produces a self-contained, user-openable macOS product artifact by packaging the **existing** local-first architecture. D3 packages the product; it does not redesign it.

D3's roadmap scope, user scenario, tests and non-goals remain authoritative. The sections below record the architectural constraints that packaging must respect; they do not widen D3 and do not restate it as a different stage.

### Preserved product topology

The packaged product must preserve exactly this topology:

```text
macOS packaged product
→ existing local launcher
→ local backend on 127.0.0.1
→ built frontend
→ ordinary system browser / SPA
→ external user-data directory
```

The browser remains the normal product presentation surface. The backend remains API-first and localhost-only. Business and domain logic remains backend-owned. The launcher remains the destructive Restore authority under ADR 0016, and the ADR 0018 launcher-owned loopback control plane and launcher-owned macOS picker remain the only Restore control path.

### Minimum artifact contract

The successor implementation must produce a distributable artifact with this intended delivery shape:

```text
CosmeticWorkshopOS-mac.zip
```

The archive must contain a self-contained, user-openable macOS product artifact. A simple:

```text
CosmeticWorkshopOS.app
```

inside that ZIP is the **preferred target** if it can be produced without changing the product topology. If it cannot, the successor implementation must still deliver a self-contained user-openable artifact inside the ZIP and must state plainly why the `.app` shape was not reached — it must not reach the `.app` shape by introducing an application shell.

The artifact must work for a non-technical user through the ordinary scenario:

```text
download/copy archive
→ unzip
→ open the packaged application
→ launcher starts
→ browser opens
→ user works
```

The end user must not need Git, Python, Node.js, npm, Docker, GitHub, Codex, a terminal or any manual shell command.

### Package contents

The successor implementation may package only what is necessary to run the existing product, conceptually:

- the launcher;
- a self-contained/bundled backend runtime;
- the production frontend build;
- migrations;
- required application configuration/resources;
- required offline help/static resources already part of the application contract.

### Excluded from the package

The package must **not** contain:

- a real user database;
- real backups;
- exports;
- attachments;
- logs;
- developer credentials;
- secrets;
- repository working data.

User data remains **outside** the application/package directory, in the existing configured user-data directory, and must survive application replacement and restart. The existing user-data-directory rules (ADR 0004) and the existing migration-safety rules — including backup before schema migration and never silently mutating historical data — remain unchanged.

### Packaging implementation mechanism

This ADR deliberately does **not** select a desktop framework and does **not** select a backend bundling tool. The repository contains no accepted normative decision requiring PyInstaller or any equivalent, so none is imposed here.

A future implementation PR may introduce a **build-only** packaging dependency or tool if it is necessary, provided all of the following hold:

1. it is not an end-user prerequisite;
2. it does not create a new application shell or a new product topology;
3. it does not move business logic out of the backend;
4. it does not change Restore ownership or security semantics;
5. it does not store user data inside the package;
6. its use is explicit in the implementation PR and in that PR's tests.

### Stop conditions

If the successor implementation discovers that satisfying the artifact contract requires a persistent new runtime framework, a desktop application shell, a sandbox model, a new Restore transport, a new backend Restore endpoint or any other architecture change, it must **STOP** and require a new decision. It must not implement such a change implicitly under this authorization.

## Explicit non-authorizations

This decision does **not** authorize:

- Electron;
- Tauri;
- pywebview;
- a PyObjC application shell;
- a second native product UI;
- a WebView-based replacement for the existing browser UI;
- a new Restore transport;
- a new backend Restore endpoint;
- any change to the ADR 0016 durable Restore state machine or safety semantics;
- any change to the ADR 0018 control-plane, picker, session or path-privacy contract;
- any production code change to backend, frontend or launcher runtime behavior as part of this decision PR.

CR-012 must not be read as authorizing the release programme. Explicitly outside this authorization:

- signing — NOT AUTHORIZED;
- notarization — NOT AUTHORIZED;
- mandatory DMG — NOT AUTHORIZED;
- installer redesign — NOT AUTHORIZED;
- auto-update — NOT AUTHORIZED;
- update download mechanism — NOT AUTHORIZED;
- GitHub Releases redesign — NOT AUTHORIZED;
- release-channel infrastructure — NOT AUTHORIZED;
- App Store — NOT AUTHORIZED;
- sandbox migration — NOT AUTHORIZED;
- cloud deployment — NOT AUTHORIZED;
- cloud sync — NOT AUTHORIZED;
- multi-user infrastructure — NOT AUTHORIZED;
- full release-candidate certification — NOT AUTHORIZED;
- general remote-install automation beyond what is required to test this artifact — NOT AUTHORIZED;
- D4 — Update safety — NOT AUTHORIZED BY CR-012;
- D5 — Remote install checklist — NOT AUTHORIZED BY CR-012.

None of the items above belong to D3. They are D4, D5 or later release/distribution work, and the roadmap's own D3 non-goals — no signing, no auto-update, no App Store, no mandatory `.dmg` — remain authoritative and are not widened here.

Stated as the one rule that replaces the earlier blanket prohibition on packaging implementation: **CR-012 authorizes the existing roadmap stage D3 — macOS package MVP and nothing beyond it; D4, D5 and later release/distribution work remain outside this authorization.** Producing the artifact is a verification prerequisite and is never product release readiness.

## Exact-package testability contract

The packaged artifact exists so that the later external C4-III exact-package verifier can run against the **actual packaged runtime**, never against a source-tree fallback.

The future package implementation must make it possible to prove:

- the packaged application starts;
- the backend is packaged and starts locally on `127.0.0.1`;
- the production frontend build is used, not the Vite development server;
- the user-data directory is external to the package;
- first start can create the required local data;
- restart preserves user data;
- current-schema Restore works through the already accepted product flow;
- supported older-schema Restore works through the existing migration/startup contract;
- invalid Restore candidates remain rejected before destructive mutation;
- rollback/recovery behavior remains the existing C4 contract;
- the selected Restore source remains immutable;
- mandatory `before_restore` safety-copy semantics remain intact.

The verifier itself is **not** implemented or authorized by this ADR. Writing it remains C4-III verification work under ADR 0017, and it may run only once a real packaged artifact exists.

## Consequences

Positive: C4-III gains a path to closure; the exact-package half becomes executable against a real artifact; the accepted Restore architecture, browser-first topology and user-data rules survive packaging untouched; the authorization stays small enough to review.

Negative and accepted: a build-only packaging tool may enter the repository in the successor PR; a self-contained backend runtime increases artifact size; the artifact will be unsigned and un-notarized and macOS will treat it accordingly, which is acceptable because this artifact is a verification prerequisite and not a release build.

Neutral: exact-package verification stays `INCONCLUSIVE — ENVIRONMENT` and C4-III lifecycle closure stays `NOT COMPLETED` until the artifact exists **and** the verifier runs and passes against it. Neither is advanced by this decision.

## Lifecycle consequence

When this ADR is present on `main`:

```text
PR #190 — MERGED — C4-III PARTIAL VERIFICATION CHECKPOINT
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
