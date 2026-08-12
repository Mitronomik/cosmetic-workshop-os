# ADR 0019 — Minimal macOS packaged-artifact prerequisite for C4-III exact-package verification

## Status

`ACCEPTED` — 2026-08-12.

This ADR decides `CR-012 — Minimal macOS packaged-artifact prerequisite for C4-III exact-package verification`.

It authorizes exactly one bounded successor implementation task:

```text
Minimal macOS packaged-artifact prerequisite
— AUTHORIZED NEXT — NOT IMPLEMENTED
```

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

Until PR #190, no Change Request authorized producing one, so the blocker was correctly recorded as a prerequisite rather than cleared by hiding packaging work inside the C4-III verification slice. That remains the correct handling of the slice boundary, but it leaves C4-III permanently unclosable: the missing prerequisite is a decision gap, not a defect and not an environment accident that will resolve itself.

This ADR closes that decision gap and nothing else.

## Decision drivers

- C4-III lifecycle closure requires exact-package evidence that only a real packaged runtime can produce.
- Source-tree execution is not a substitute; an exact-package verifier must exercise the packaged runtime.
- The already-merged and audited Restore architecture must not be reopened, re-transported or re-owned in order to package it.
- The product is browser-first and local-first by accepted architecture; packaging must deliver that product, not a different one.
- The end user is non-technical and must not acquire developer tooling in order to run the product.
- Full D3/D4/D5 release work is far larger than this prerequisite and must not be smuggled in behind it.

## Considered alternatives

### Option A — leave C4-III blocked indefinitely

Advantage: changes nothing and risks nothing.

Rejected. The blocker is a missing decision, not a missing environment. Leaving it in place makes C4-III unclosable by construction and freezes Restore at `NOT IMPLEMENTED` forever.

### Option B — authorize full D3 macOS packaging and release readiness now

Advantage: one authorization would cover packaging, updates and release.

Rejected. D3/D4/D5 include signing, notarization, DMG, update safety, remote-install automation and release-candidate certification. None of that is required to run one exact-package verification, and bundling it here would turn a prerequisite into an unbounded release programme and would let "package exists" be misread as "product is releasable".

### Option C — adopt a desktop application shell (Electron, Tauri, pywebview, PyObjC)

Advantage: a native shell is a conventional way to obtain a double-clickable macOS application.

Rejected. Every such shell replaces or duplicates the accepted browser-first presentation surface, introduces a second product UI or a WebView substitute for it, adds a persistent runtime framework and dependency class, and — most importantly — would put a new host process between the browser and the launcher-owned loopback Restore control plane decided in ADR 0018. That is an architecture redesign, not a packaging prerequisite. ADR 0018 already rejected adding PyObjC, Electron, Tauri, pywebview or a WebSocket framework by assumption; this ADR does not reverse that.

### Option D — package the existing architecture, unchanged, as a minimal distributable artifact

Advantage: produces the artifact the verifier needs while leaving product topology, Restore ownership, browser surface and user-data rules byte-for-byte as decided.

**Selected: Option D.**

## Decision

Authorize one bounded successor implementation task that produces a minimal, self-contained, user-openable macOS product artifact by packaging the **existing** local-first architecture. The successor task packages the product; it does not redesign it.

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
- full D4 update-safety implementation — NOT AUTHORIZED;
- D5 remote-install work — NOT AUTHORIZED.

Full D3 remains outside this authorization. Stated as the one rule that replaces the earlier blanket prohibition: **only the bounded minimal packaged-artifact prerequisite is authorized; full D3 / release packaging remains outside this authorization.** Producing the artifact is a verification prerequisite and is never product release readiness.

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
CR-012 — ACCEPTED — MINIMAL MACOS PACKAGED-ARTIFACT PREREQUISITE
Minimal macOS packaged-artifact prerequisite — AUTHORIZED NEXT — NOT IMPLEMENTED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```
