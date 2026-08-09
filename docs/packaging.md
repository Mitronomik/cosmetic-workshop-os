# Packaging

Package must include launcher, backend runtime, frontend build, migrations, default config and help files. It must not include real user database, backups, exports, logs or secrets.

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

## Restore lifecycle

```text
PR #182 — MERGED — C4-II-B1 EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B3 — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed A4/B1 packaging consequences

A4 adds no runtime dependency. A packaged build must preserve `restore-control-entry.js` before `main.js` so the one-use fragment is captured/removed before shell routing.

The native picker remains macOS-provided `/usr/bin/osascript`. Mac App Store sandbox compatibility is **not claimed**; any later picker replacement must preserve launcher path authority unless a later ADR explicitly changes it.

Bootstrap capability is launch-memory only. Session token stays in `sessionStorage`, never `localStorage`, package files, logs or persistent config. Same-tab non-secret command replay metadata stays in `history.state`.

B1 is internal Python launcher/C4-I proof binding and adds no package resource or persistent state.

## B2 packaging consequence

B2 remains inside the existing launcher process and existing ephemeral loopback control plane. It may add Python launcher modules/tests only; it requires no new dependency, background service, port, helper executable, entitlement, persistent secret or package resource.

The same launcher process must survive the ordinary backend's intentional C4-I stop/restart. That is runtime coordination, not a packaging redesign.

Frontend assets remain byte-identical in B2. B3 later owns the browser confirmation/parser extension. macOS packaging work remains separately incomplete and not authorized by B2.
