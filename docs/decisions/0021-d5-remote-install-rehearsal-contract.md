# ADR 0021 — D5 Remote Install Rehearsal contract

Status: **PROPOSED BY CR-014 — DECISION ONLY; D5 MAY BE AUTHORIZED ONLY WHEN THIS CHANGESET MERGES**

Decision base: `a8a28672a6fd807cd59342a02a102b8e09128fff`
Change request: `CR-014 — D5 Remote Install Rehearsal contract`

This ADR decides what the roadmap stage `D5 — Remote install checklist` means for the current packaged local product. It contains **no runtime implementation**. It does not sign, notarize, redesign, publish or update the application.

ADR 0019 remains authoritative for the D3 packaged-product topology. ADR 0020 remains authoritative for D4 Update Safety. ADR 0016 and ADR 0018 remain authoritative for Restore. This decision does not reopen any of them.

## Context

D3 is implemented: the product is packaged as `CosmeticWorkshopOS.app` inside `CosmeticWorkshopOS-mac.zip`, with a bundled backend runtime and production frontend, while user data stays outside the application package. D4 is complete, exact-package verified and lifecycle-closed.

The strategic roadmap defines D5 narrowly:

- make remote installation repeatable;
- maintain `docs/user-install.md`, `docs/remote-install-checklist.md`, `docs/update-guide.md` and `docs/backup-and-restore.md`;
- exercise download/unzip/open, first-run, user-data check, backup, a test client, test component, test recipe and restart;
- follow the checklist on a clean Mac or clean user profile if possible;
- document limitations;
- do not integrate paid remote-management tools;
- do not implement auto-update.

The product specification adds one user-level requirement: remote installation must be possible through screen sharing. The architecture also requires that user mode never require Git, Python, Node.js, Docker, GitHub or terminal commands.

The current install documents are only skeletons. `docs/remote-install-checklist.md` has eight unchecked lines and does not yet carry the full roadmap scenario. `docs/user-install.md` still contains branch-era wording that the final user package is not yet available, even though D3 and D4 are now closed. Those files therefore must not be mistaken for a verified release procedure before D5 runs.

The current D3 package is intentionally unsigned and un-notarized. Its build records the architecture of the machine that produced it, and `Info.plist` contains `LSMinimumSystemVersion=12.0`; neither fact by itself proves a broad support matrix. D5 must not silently convert package existence into a claim that every supported-looking macOS/CPU combination has been tested.

## Problem

Without a bounded D5 decision, several different programmes can be confused under the phrase “remote install”:

1. a human-assisted first installation of the existing ZIP/.app;
2. signing/notarization and Gatekeeper distribution engineering;
3. DMG/PKG installer design;
4. public release hosting and GitHub Releases;
5. auto-update/download or release channels;
6. MDM/remote-management integration;
7. full release-candidate certification.

Only the first item belongs to roadmap D5.

There are also concrete verification gaps:

- the exact artifact and tested environment are not recorded by the current checklist;
- Finder/Gatekeeper behavior of the unsigned package is not yet rehearsed as a user flow;
- the current checklist does not prove the full roadmap sequence client → component → recipe → restart persistence;
- the current guides do not distinguish user steps from technician/evidence steps;
- a CI package smoke cannot by itself prove that a non-technical person can follow Finder/System Settings instructions;
- a clean-profile rehearsal can be blocked by environment policy, and that must not be mislabeled as a product failure or as a PASS.

## Decision

D5 is a **documentation + exact-package assisted-install rehearsal stage** over the already implemented D3/D4 product. It does not add a new product runtime feature.

D5 may update the install/checklist documentation and run exact-package verification. It may not modify backend, frontend, launcher, migrations, package runtime behavior or Restore semantics as part of the D5 implementation changeset. If the rehearsal finds a real product defect, D5 stops and the defect requires its own bounded fix/authorization before D5 can close.

D5 certifies only this statement:

> An exact packaged artifact can be transferred to a non-technical user and installed/opened through ordinary macOS user interfaces, optionally with human screen-sharing assistance, then complete the roadmap first-install smoke and preserve data across restart on the explicitly recorded tested environment.

D5 does **not** certify commercial/public release readiness.

## User and support model

The ordinary user flow remains:

```text
receive/download the exact ZIP from a trusted transfer location
→ unzip with Finder
→ open CosmeticWorkshopOS.app
→ if macOS requires confirmation, use ordinary Finder/System Settings UI only
→ complete first-run
→ verify the product's user-data location
→ create a backup through the product UI
→ create a synthetic test client
→ create a synthetic test component
→ create a synthetic test recipe
→ close the application normally
→ reopen the same application
→ verify the test data persisted
```

Human screen sharing is allowed as assistance because `docs/product-spec.md` explicitly requires remote installation to be possible through screen sharing. D5 does not select, bundle or integrate a screen-sharing vendor. The assistance channel is outside the product and may be absent when the user can follow the guide independently.

The end user must not need to:

- browse or clone the GitHub repository;
- install Git, Python, Node.js, npm, Docker, Codex or developer dependencies;
- open Terminal;
- run shell commands;
- inspect SQLite directly;
- understand ports, migrations or package internals.

Internet connectivity may be used to transfer the archive or provide screen sharing. After the package is present, the ordinary local product must retain the accepted local-first/offline-capable topology.

## Gatekeeper and macOS security boundary

At D5 entry the package is unsigned and un-notarized. D5 may document the **standard user-facing macOS UI path actually observed during the rehearsal** for opening a trusted exact artifact, such as Finder `Open` and/or the corresponding `System Settings → Privacy & Security` approval path when macOS presents one.

D5 must never instruct the user to:

- run `xattr` or `spctl` commands;
- use `sudo` or Terminal to bypass security;
- disable Gatekeeper globally;
- lower macOS security settings globally;
- remove quarantine metadata by command line;
- suppress or bypass enterprise/MDM security policy.

If the tested environment prevents the unsigned application from being opened through normal permitted macOS UI, D5 does not invent a bypass. The result must be reported truthfully as either an environment limitation or a product/distribution limitation, and D5 cannot claim a full PASS for that environment.

If practical remote installation for the intended audience is found to require signing/notarization, D5 must STOP and request a separate release/distribution decision. Signing and notarization are not silently authorized by this ADR.

## Artifact identity and support-boundary contract

Every D5 rehearsal must record, in engineering evidence rather than in burdensome user instructions:

- exact Git commit SHA used to build the package;
- effective application version;
- archive filename;
- archive SHA-256 digest;
- package architecture from the packaged runtime manifest;
- tested Mac hardware architecture;
- exact macOS version;
- whether Gatekeeper/quarantine UI appeared and what user-facing path was used;
- whether the run used a clean Mac or a clean macOS user profile.

A D5 PASS is bounded to the exact tested artifact and environment evidence. It must not imply Intel, Apple Silicon, Universal 2 or additional macOS-version support that was not actually exercised.

`LSMinimumSystemVersion` is package metadata, not sufficient evidence of a supported OS matrix. Host-specific package architecture is likewise not a universal-support claim.

No checksum command is an end-user requirement. Artifact digest verification belongs to the build/support evidence layer.

## Clean-environment contract

A trustworthy D5 rehearsal requires either:

1. a clean Mac, preferred when available; or
2. a clean macOS user profile with no existing CosmeticWorkshopOS user data, acceptable under the roadmap’s explicit fallback.

The rehearsal must begin with:

- no running product process;
- no existing working database for the rehearsal profile;
- no dependency on a developer checkout;
- no real client/customer data;
- a disposable or clearly isolated test-data context.

The verifier/support operator may collect technical evidence outside the user flow, but must not turn those evidence steps into user prerequisites.

## Required D5 checklist semantics

The D5 implementation must preserve the roadmap’s user-facing checklist, at minimum:

```text
1. Скачать/получить архив приложения
2. Распаковать архив
3. Запустить приложение
4. Разрешить запуск через обычный интерфейс macOS, если это требуется
5. Пройти first-run wizard
6. Проверить папку данных через понятный продуктовый сценарий
7. Создать backup через приложение
8. Создать тестового клиента
9. Создать тестовый компонент
10. Создать тестовый рецепт
11. Закрыть и снова открыть приложение
12. Убедиться, что тестовые данные сохранились
```

The extra persistence assertion is an explicit verification of the roadmap restart requirement; it does not add product scope.

The checklist must distinguish:

- **user steps** — Finder/System Settings/browser/product UI only;
- **support/evidence steps** — artifact SHA, environment metadata and diagnostic evidence, never required from the ordinary user.

The user must never be told to inspect the database file, execute a developer command or use the repository as the product.

## Documentation contract

The D5 implementation is allowed to revise only the documentation necessary to make the accepted flow truthful and repeatable, principally:

- `docs/user-install.md` — concise Russian first-install guide for a non-technical user;
- `docs/remote-install-checklist.md` — operator/user checklist plus pass/fail evidence fields;
- `docs/update-guide.md` — cross-link only where needed to distinguish first install from the already closed D4 manual-update flow;
- `docs/backup-and-restore.md` — cross-link only where needed to point to the already accepted backup/Restore behavior without changing it.

`docs/local-install.md` remains developer-only and must not become the user install path.

The D5 implementation may also update lifecycle/state/testing documentation required to record its progress and evidence. It may not use documentation changes to redefine application behavior.

## Verification contract

D5 has two complementary evidence layers.

### Automated exact-package layer

An external verifier must run against the exact D5 implementation head and use a real package built from that exact head. It must reuse the accepted package/runtime test seams rather than substitute source-tree startup.

It must prove at least:

- exact-head identity before testing;
- package structure/version projection passes;
- packaged application starts in isolated user-data;
- first-run creates/uses external user data rather than data inside the package/repository;
- a backup can be created through the product flow;
- synthetic client/component/recipe data can be created through product APIs/UI as appropriate to the existing product;
- restart preserves that data;
- repository and runner postflight are clean.

### Human UI rehearsal layer

A complete D5 PASS also requires a documented human rehearsal on a clean Mac or clean macOS user profile. This layer exists specifically to validate the non-technical Finder/System Settings/first-run flow that CI cannot honestly infer from package internals.

It must record:

- the environment/artifact identity fields above;
- whether each checklist step was completed without Terminal/developer tooling;
- any Gatekeeper wording/path actually encountered;
- any limitation or confusing step;
- whether an independent person can follow the written guide with no repository knowledge;
- whether screen sharing was needed, optional or not used.

Screenshots are optional and must not contain real client data, secrets, private paths unnecessarily or sensitive backup contents.

## Result classification

D5 follows the repository smoke contract:

- real application/package defect → `FAIL — PRODUCT`;
- verifier/script defect → `INCONCLUSIVE — RUNNER`;
- unavailable/incompatible/managed test environment → `INCONCLUSIVE — ENVIRONMENT`;
- all required automated and human layers pass → `PASS — D5 REMOTE INSTALL REHEARSAL PASSED`.

A runner/environment issue must never be reported as a product failure. Conversely, D5 may not close on an `INCONCLUSIVE` result.

If the human clean-environment rehearsal has not happened, automated package smoke alone is not enough to claim D5 complete.

## Completion criteria

D5 may be lifecycle-closed only when all of the following are true:

- the user-install guide is current, Russian, short and non-technical;
- the remote-install checklist covers the complete roadmap scenario;
- the exact artifact and tested environment are recorded in evidence;
- the automated exact-package layer passes;
- the human clean-Mac/clean-profile rehearsal passes;
- backup creation is proven through the product flow;
- synthetic client/component/recipe data survive restart;
- no end-user Terminal/Git/Python/Node/Docker step is required;
- limitations and the tested support boundary are documented;
- D5 closure is recorded in a separate lifecycle-only changeset.

D5 completion still does **not** equal product release readiness.

## Explicit non-authorizations

CR-014 / D5 does **not** authorize:

- signing or Developer ID certificate work;
- notarization;
- entitlements or sandbox migration;
- DMG or PKG installer redesign;
- App Store work;
- public release hosting or website distribution;
- GitHub Releases integration;
- release-channel infrastructure;
- auto-update, internet update checking or update download;
- telemetry or remote diagnostics;
- MDM integration;
- paid or bundled remote-management tools;
- automated remote control of the user’s Mac;
- cloud deployment or cloud sync;
- multi-user infrastructure;
- a new desktop shell;
- changes to the D3 package topology;
- changes to D4 migration/update semantics;
- changes to Restore ownership, state machine, picker, control plane or destructive semantics;
- `PHASE 12 — MVP release preparation`, `PR28`, `PR29` or product release readiness.

The fact that an older D3-era comment informally grouped some future distribution work with “D4/D5” is not authorization. For D5 scope, this newer ADR and the strategic roadmap are authoritative.

## Stop conditions

D5 must stop and require a separate bounded decision/fix when:

- the package needs runtime code changes to complete the checklist;
- signing/notarization is required for the intended installation audience;
- a requested hardware/OS target is outside the actually proven package architecture/environment;
- installation requires Terminal, administrator shell commands or global security weakening;
- enterprise/MDM policy blocks the package and cannot be resolved through ordinary permitted user UI;
- the product stores or mutates rehearsal data inside the package/repository;
- first-run, backup or restart persistence exposes a product defect;
- the only path to “remote install” would introduce remote-management infrastructure or a new distribution system.

The D5 implementation task must not silently fix around any of these boundaries.

## Considered alternatives

### Option A — treat D5 as signing/notarization/release engineering

Rejected. The roadmap defines D5 as a repeatable remote-install checklist and explicitly keeps auto-update out. Signing/notarization/DMG/App Store/public distribution form a separate release programme.

### Option B — declare D5 complete from existing D3/D4 CI package smoke

Rejected. Existing exact-package evidence proves the packaged runtime and update safety, but it does not prove that an independent non-technical person can complete the Finder/System Settings first-install flow on a clean Mac/profile.

### Option C — make remote installation a remote-management integration

Rejected. The product specification asks for screen-sharing-assisted installation, not a control agent. The roadmap explicitly excludes paid remote-management integration.

### Option D — accept documentation + exact-package + human clean-environment rehearsal

**Selected.** It is the smallest interpretation that satisfies the roadmap and product specification without smuggling release/distribution infrastructure into MVP.

## Consequences

Positive:

- “remote install” gets a precise user-centered meaning;
- the current unsigned package can be tested honestly without pretending it is a public release;
- the user guide remains simple while engineering evidence remains precise;
- hardware/OS support claims become evidence-bounded;
- Gatekeeper handling cannot drift into unsafe terminal bypass instructions;
- D3, D4 and Restore stay closed and unchanged.

Negative and accepted:

- a real human clean-profile rehearsal is required before D5 can close;
- an unsigned package may expose a practical distribution limitation that D5 is not authorized to solve;
- a PASS on one architecture/macOS version does not automatically prove other combinations.

Neutral:

- D5 may reveal that signing/notarization should be the next separately decided release step; that discovery is useful, but it is not itself authorization.

## Test contract

The D5 implementation PR must be docs/lifecycle/testing-only unless a separately authorized defect fix exists. Before merge it requires:

- `git diff --check`;
- documentation lifecycle checker PASS;
- exact D5 scope check;
- external exact-head verification;
- exact-package automated rehearsal evidence;
- human clean-Mac/clean-profile rehearsal evidence;
- product/runner/environment failure classification;
- clean postflight.

D5 closure must be a separate lifecycle-only changeset after the accepted D5 implementation head is merged and the required evidence is trustworthy.

## Lifecycle consequence

When this decision changeset is merged to `main`:

```text
CR-013 — ACCEPTED — D4 UPDATE SAFETY CONTRACT
D4 — Update safety — DONE — EXACT-PACKAGE VERIFIED AND LIFECYCLE-CLOSED
CR-014 — ACCEPTED — D5 REMOTE INSTALL REHEARSAL CONTRACT
D5 — Remote install checklist — AUTHORIZED NEXT — NOT IMPLEMENTED
D5 verification — NOT STARTED
PHASE 12 — MVP release preparation — NOT AUTHORIZED BY CR-014
Product release readiness — NOT CLAIMED
```

Only D5 is authorized next. No runtime, release/distribution or Phase 12 work is authorized by this decision.
