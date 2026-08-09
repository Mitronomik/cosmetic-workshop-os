# Packaging

Package must include launcher, backend runtime, frontend build, migrations, default config and help files. It must not include real user database, backups, exports, logs or secrets.

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

## Restore lifecycle

```text
PR #180 — MERGED — C4-II-A4 EXACT-HEAD VERIFIED
C4-II-A — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-B — IN PROGRESS — SLICED
C4-II-B1 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B2 — PLANNED — NOT AUTHORIZED
C4-II-B3 — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## Closed A4 packaging consequences

A4 adds no runtime dependency. A packaged build must preserve `restore-control-entry.js` before `main.js` so the one-use fragment is captured/removed before shell routing.

The native picker remains macOS-provided `/usr/bin/osascript`. Mac App Store sandbox compatibility is **not claimed**; any later picker replacement must preserve launcher path authority unless a later ADR explicitly changes it.

Bootstrap capability is launch-memory only. Session token stays in `sessionStorage`, never `localStorage`, package files, logs or persistent config. Same-tab non-secret command replay metadata stays in `history.state`.

## B1 packaging consequence

B1 is internal Python launcher/C4-I proof binding. It authorizes no dependency, helper executable, new package resource, background service or persistent secret. Packaging behavior remains unchanged.

B2/B3 destructive execution/confirmation remain separately not authorized.
