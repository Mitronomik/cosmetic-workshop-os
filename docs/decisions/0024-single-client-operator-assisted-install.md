# ADR 0024 — Single-client operator-assisted install and update

Status: **ACCEPTED — CR-017 BOUNDED IMPLEMENTATION AUTHORIZED AFTER MERGE**

Decision base: `d2aef241f46be58a1f4c535718f93d15f8209ed8`
Date: `2026-08-16`
Change request: `CR-017 — Single-client operator-assisted install and update`

## Context

CR-016 attempted to preserve a double-click self-service bootstrap while avoiding Developer ID/notarization for one known client. Its implementation passed automated post-execution tests, but the mandatory clean-Mac Finder rehearsal failed before bootstrap execution because Gatekeeper blocked the downloaded `.command` itself. This is a trust-boundary deadlock, not a product-runtime defect.

The project has one known client. There is not yet sufficient business justification to pay for and operationalize Developer ID/notarization solely for this pilot. The product architecture, packaged `.app`, native lifecycle, D4 update safety, Restore and external user-data boundary must remain unchanged.

## Decision

For the current single-client pilot only, installation and later manual package updates use an **operator-assisted support flow**.

A qualified support operator may connect by screen sharing or work directly at the Mac, open Terminal, and run a repository-owned/operator-owned installation script. The client must not type shell commands or understand them. Normal product use after installation remains Finder/Dock/browser/product UI only.

This decision supersedes the failed CR-016 self-running downloaded `.command` mechanism. It does not revive or merge PR #210.

## Mandatory verification-before-quarantine-removal contract

Before quarantine metadata is removed or an installed application is replaced, the operator flow must:

1. identify the exact `CosmeticWorkshopOS-mac.zip` selected for installation;
2. calculate SHA-256 with a macOS system tool;
3. compare it with an immutable expected SHA-256 supplied by the version-specific operator script or explicit trusted invocation argument;
4. stop immediately on mismatch;
5. extract the verified ZIP into a runner-owned staging directory under the current user's filesystem;
6. verify the staged `CosmeticWorkshopOS.app` bundle identifier, product version, `CFBundleExecutable`, executable native main and expected architecture;
7. only after every verification passes, remove `com.apple.quarantine` recursively from that exact verified staged `.app`;
8. never remove quarantine from arbitrary paths or from an unverified downloaded bootstrap.

## Operator and user boundary

The support operator may use Terminal, `shasum`, `plutil`, `file`, `xattr`, `ditto`, `open`, `osascript` and ordinary filesystem commands needed by the bounded script.

The client must not be asked to type or paste Terminal commands. The operator may explain that Terminal is being used only for installation/support.

The operator flow must not use `sudo`, must not request an administrator password, and should install under `~/Applications/CosmeticWorkshopOS.app`.

## Gatekeeper boundary

Gatekeeper remains globally enabled. CR-017 permits only the narrow equivalent of:

```text
xattr -dr com.apple.quarantine <verified-staged-CosmeticWorkshopOS.app>
```

It does not authorize `spctl --master-disable`, SIP changes, Startup Security changes, global quarantine removal, security-policy weakening, MDM bypass or any other system-wide trust change.

## First installation

For first installation, after candidate verification the operator script may remove quarantine from the verified staged app, publish it to `~/Applications/CosmeticWorkshopOS.app`, and launch it with normal macOS application launch semantics.

After launch, the client must be able to use Finder/Dock/browser UI without Terminal. Ordinary macOS Quit and restart remain governed by the closed CR-015 lifecycle implementation.

## Update behavior

The same operator tool may install a later exact package.

Before replacement it must verify the candidate fully. If the application is running, it may request ordinary application Quit through macOS automation and wait for complete shutdown, or fail closed and require the operator to close it normally. It must never force-kill the application as a successful update path.

The previous `.app` package must be retained separately before candidate publication. The tool must not automatically launch that retained package as rollback after the new version starts.

D4 remains the sole authority for schema compatibility, before-migration backup, staged migration, UpdateLog, interruption handling and migration failure. The operator installer must never edit the product database or user-data directory.

## Trust model

The support operator receives the exact expected SHA-256 through a trusted support channel and verifies the selected package before quarantine removal. For the one-client pilot this is sufficient to protect against accidental wrong-package use and transfer corruption.

This is not public code-signing identity. If the application gains additional independent clients or self-service/public distribution becomes economically justified, a new decision must evaluate Developer ID signing/notarization and replace this assisted trust model.

## Implementation scope

CR-017 authorizes only:

- one operator-owned macOS install/update script;
- deterministic tests for its fail-closed ordering and forbidden commands;
- optional packaging/support documentation for the operator;
- exact-package automated rehearsal on isolated data;
- a clean-Mac human operator-assisted rehearsal.

It does not authorize backend/frontend/domain changes, database changes, migrations, Restore changes, D4 changes, a new desktop framework, auto-update/download, cloud infrastructure, signing/notarization, DMG/PKG, App Store, public release hosting, release channels, Phase 12 or product release readiness.

## Human rehearsal contract

A D5 pilot-assisted PASS requires the actual exact package to be installed on the clean test Mac through the operator procedure, followed by client-style product use without Terminal: launch, backup/client/component/recipe smoke, ordinary Quit, restart and persistence verification.

The operator may use Terminal during installation. After installation the client-facing path must not require Terminal.

Success proves only the single-client operator-assisted pilot deployment. It does not prove unsigned self-service distribution or public release readiness.

## Stop conditions

Stop and request another decision if the operator flow requires administrator privileges, global security weakening, database manipulation, remote-control infrastructure, public/multi-client distribution claims, Developer ID/notarization, or changes to the product runtime itself.

## Non-goals

- no self-running downloaded `.command` requirement;
- no global Gatekeeper disable;
- no Developer ID/notarization in this stage;
- no product redesign;
- no backend/frontend/domain/Restore/D4 changes;
- no automatic update downloads;
- no Phase 12;
- no product release readiness claim.
