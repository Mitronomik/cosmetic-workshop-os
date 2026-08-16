# ADR 0023 — Single-client assisted install and update bootstrap

Status: **ACCEPTED DECISION — IMPLEMENTATION REJECTED BY HUMAN FINDER REHEARSAL; SUPERSEDED FOR PILOT DEPLOYMENT BY ADR 0024**

Decision base: `93bdb1d51f6fe3e998051a7dda440c45ad17f30a`
Date: `2026-08-16`
Change request: `CR-016 — Single-client assisted install and update bootstrap`

## Context

D5 clean-Mac rehearsal exposed a second distribution blocker after the native application lifecycle defect was fixed: the exact unsigned/unnotarized package can still be rejected by Gatekeeper before product code runs. For the current project there is one known client and no present business justification for paid Apple Developer Program membership solely to obtain Developer ID/notarization.

The application architecture itself must not be rolled back or redesigned. The accepted local-first package, browser UI, external user-data boundary, D4 update safety, Restore contract and CR-015 AppKit lifecycle remain authoritative.

ADR 0021 intentionally prohibited Terminal/xattr from the ordinary D5 installation flow. It also required D5 to stop and seek a separate decision when normal unsigned distribution proved insufficient. This ADR is that separate bounded decision.

## Decision

For the **single known pilot/client only**, the product may use a version-specific assisted-install bootstrap distributed together with the exact product ZIP.

The deliverable is an outer ZIP containing at least:

```text
Установить или обновить Мастерскую.command
CosmeticWorkshopOS-mac.zip
```

The `.command` file is a support/bootstrap tool, not the product runtime. A user may double-click it in Finder; Terminal may become visible, but the user must not be required to type shell commands or understand them.

The same bootstrap must support both first installation and later manual updates of the one-client pilot package.

## Mandatory verification-before-quarantine-removal contract

The bootstrap must fail closed.

Before any quarantine metadata is removed and before an existing application is replaced, it must:

1. locate only the companion exact `CosmeticWorkshopOS-mac.zip` expected by that bootstrap;
2. calculate SHA-256 with a macOS system tool;
3. compare it with the immutable expected SHA-256 embedded into that generated bootstrap;
4. stop immediately on mismatch;
5. extract the verified ZIP into an isolated temporary staging directory;
6. verify that staging contains exactly the expected `CosmeticWorkshopOS.app` bundle shape needed by the installer;
7. verify at minimum bundle identifier `ru.cosmetic-workshop-os.app`, expected product version, expected `CFBundleExecutable`, executable native main and expected package architecture;
8. only after all checks pass, remove `com.apple.quarantine` recursively from the verified **staging application only**.

A checksum mismatch, wrong bundle ID/version/architecture, malformed archive or missing executable must never trigger quarantine removal, replacement of the installed app or launch of the candidate.

## Security boundary

CR-016 explicitly permits only the narrow command equivalent of:

```text
xattr -dr com.apple.quarantine <verified-staging-CosmeticWorkshopOS.app>
```

It does **not** authorize:

- `spctl --master-disable` or any global Gatekeeper disable;
- disabling SIP;
- lowering Startup Security / Security Policy;
- `sudo` or administrator-password requirements;
- modifying quarantine on arbitrary files/directories;
- suppressing MDM/enterprise policy;
- downloading executable code from an updater;
- Developer ID signing/notarization;
- App Store, DMG/PKG, public release hosting or release channels.

Gatekeeper remains enabled for the Mac. The exception is scoped to a candidate `.app` whose companion release ZIP has already passed the embedded exact SHA-256 and package-identity checks.

## Install location

The bootstrap should install the pilot product under the current macOS user's application space, preferably:

```text
~/Applications/CosmeticWorkshopOS.app
```

This avoids `sudo`, administrator credentials and system-wide changes while preserving normal Finder/Dock/Spotlight use for the single user.

## Existing-install/update behavior

The bootstrap must not manipulate the database, migrations, backups, Restore state or business data.

For an update:

- if the installed application is running, the bootstrap must stop before replacement and tell the user to close it normally through the macOS application lifecycle, then rerun the bootstrap;
- the candidate is fully verified and staged before the installed app is touched;
- the previous `.app` package is retained separately before replacement;
- the new `.app` is installed and launched;
- D4 remains the sole owner of version/schema compatibility, backup-before-migration, staged migration, UpdateLog and migration failure semantics;
- the bootstrap must never automatically launch the retained old `.app` as a rollback after the new app has been started, because D4 explicitly does not treat the prior package as a generic rollback after a schema commit.

The retained prior package is support evidence/recovery material, not an automatic database rollback mechanism.

## Release identity model

For the current one-client stage, every generated bootstrap is version-specific and contains the expected SHA-256 of its companion product ZIP. The bootstrap and companion ZIP are transferred together from the developer/support operator to the known client.

This protects against corruption, accidental wrong-package use and mismatch between the installer and candidate. It is **not** a substitute for public code-signing identity: replacement of both the bootstrap and its companion ZIP by an attacker is outside the trust guarantees of this single-client transfer model.

A future multi-client/public distribution decision should replace this trust model with Developer ID/notarization and/or an independently signed release-manifest design rather than silently extending CR-016.

## User/support boundary

For this pilot exception:

- the client may see a Terminal window opened by the `.command` file;
- the client must not type commands;
- the client must not manually run `xattr`, `shasum`, `chmod`, `spctl`, `sudo`, Python, Node.js or Git;
- all normal product use after installation remains Finder/Dock/browser/product UI only;
- screen-sharing assistance is allowed but the bootstrap should be understandable enough to run by double-click when possible.

This is a deliberate exception to ADR 0021's stricter no-Terminal human-rehearsal contract and applies only to the single-client assisted distribution mode decided here.

## Packaging/build requirements

The repository may add a dedicated bootstrap template and a packaging step that, only after the normal exact product ZIP has been produced and structurally verified:

1. computes the product ZIP SHA-256;
2. injects that digest plus canonical app version/architecture into a generated `.command`;
3. preserves the `.command` executable bit;
4. creates a separate outer single-client distribution ZIP;
5. leaves `CosmeticWorkshopOS-mac.zip` itself unchanged as the canonical product package artifact.

The ordinary D3/D4 package must remain independently buildable and verifiable.

## Tests

Implementation must include deterministic tests proving at least:

- expected digest/version/bundle identity are injected into the generated bootstrap;
- SHA mismatch fails before extraction/quarantine removal/replacement;
- malformed or wrong application bundle fails closed;
- quarantine removal appears only after all candidate verification gates;
- no global Gatekeeper/SIP/security-disable command exists;
- no `sudo` requirement exists;
- first-install path targets the per-user application directory;
- existing running app blocks replacement;
- update retains the previous app before candidate publication;
- bootstrap does not access the product database or user-data directory;
- outer archive preserves the `.command` executable bit;
- exact package regression and CR-015 lifecycle behavior remain intact.

A human clean-Mac rehearsal must then test the actual downloaded outer ZIP and double-click `.command` behavior. CI cannot substitute direct shell execution for that Finder/Terminal handoff.

## Result classification

- bootstrap/package product defect → `FAIL — PRODUCT`;
- verification-runner defect → `INCONCLUSIVE — RUNNER`;
- macOS/environment policy prevents the `.command` bootstrap itself from being invoked → `INCONCLUSIVE — ENVIRONMENT` unless evidence shows a deterministic distribution defect;
- success of the assisted bootstrap plus existing product smoke → evidence only for the bounded single-client assisted-install mode.

It must not be reported as signed/notarized/public/self-service release readiness.

## Stop conditions

Stop and request another decision if implementation requires:

- global Gatekeeper/security weakening;
- administrator privileges or `sudo`;
- database/migration/Restore changes;
- new cloud/update-download infrastructure;
- automatic remote-control infrastructure;
- multi-client/public-distribution claims;
- Developer ID/notarization work;
- a new desktop framework or replacement of the current product package.

## Non-goals

CR-016 does not authorize:

- rewriting or rolling back the application;
- Electron/Tauri/new desktop shell work;
- backend/frontend/domain changes;
- database schema or migration changes;
- Restore changes;
- D4 semantic changes;
- signing/notarization;
- App Store work;
- DMG/PKG;
- public release hosting;
- GitHub Releases integration;
- automatic update download/checking;
- release channels;
- Phase 12;
- product release readiness.

## Consequence for D5

D5's original self-service Finder/System Settings PASS remains unachieved. CR-016 introduces a narrower, explicitly documented **single-client assisted-install mode** so the one-client pilot can proceed without changing the product architecture or purchasing Developer ID at this stage.

The CR-016 implementation and its clean-Mac human rehearsal must be recorded separately. Success does not retroactively claim the original unsigned self-service D5 distribution path passed, and it does not claim public release readiness.


## Implementation outcome

CR-016 was implemented on head `0179be9fa1758a47662f86c5a14a7f24341815c5`. Automated macOS run `31959318870` proved only post-execution behavior. The mandatory clean-Mac Finder rehearsal then produced `FAIL — PRODUCT`: Gatekeeper quarantined and blocked the downloaded `.command` before it could execute, so it could not perform its embedded verification or reach its bounded quarantine-removal step. PR #210 was closed without merge.

The self-running downloaded bootstrap is therefore rejected as the pilot installation model. ADR 0024 supersedes only that deployment mechanism. The exact product package, CR-015 lifecycle fix, D4 safety and all application runtime semantics remain unchanged.
