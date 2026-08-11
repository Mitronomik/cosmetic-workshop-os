# Packaging

Package must include launcher, backend runtime, frontend build, migrations, default config and help files. It must not include real user database, backups, exports, logs or secrets.

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

## Restore lifecycle

```text
PR #185 — MERGED — B3 AUTHORIZED
PR #184 — MERGED — C4-II-B2 EXACT-HEAD VERIFIED
PR #183 — MERGED — B2 AUTHORIZATION BASELINE
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed A4/B1 packaging consequences

A4 adds no runtime dependency. A packaged build must preserve `restore-control-entry.js` before `main.js` so the one-use fragment is captured/removed before shell routing.

The native picker remains macOS-provided `/usr/bin/osascript`. Mac App Store sandbox compatibility is **not claimed**; any later picker replacement must preserve launcher path authority unless a later ADR explicitly changes it.

Bootstrap capability is launch-memory only. Session token stays in `sessionStorage`, never `localStorage`, package files, logs or persistent config. Same-tab non-secret command replay metadata stays in `history.state`.

B1 is internal Python launcher/C4-I proof binding and adds no package resource or persistent state.

## Closed B2 packaging consequence

B2 remains inside the same launcher process and same ephemeral loopback control plane. It adds only launcher coordination/tests and no new dependency, background service, port, helper executable, entitlement, persistent secret or package resource.

The same launcher process owns the ordinary backend across an intentional C4-I stop/restart using one bounded runtime owner loop. That is runtime coordination, not a packaging redesign.

## B3 packaging consequence

The current B3 changeset changes only existing frontend Restore assets/tests plus lifecycle documentation/checker state. It adds no dependency, entitlement, background service, helper executable, persistent filesystem authority or packaging topology.

Pending execute replay may retain only action, request ID, command sequence and accepted control generation. No source path, source proof, digest, operation identity or internal database/backup/lock path may be packaged or persisted.

`restore-control-entry.js` remains the early browser entry before `main.js`; B3 extends its focused Restore confirmation wiring without moving Restore lifecycle into the giant application shell.

macOS packaging work remains separately incomplete and is not authorized by B3.