# Packaging

Package must include launcher, backend runtime, frontend build, migrations, default config and help files. It must not include real user database, backups, exports, logs or secrets.

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

## C4-II-A status

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
PR #179 — MERGED — A3 CLOSED / A4 AUTHORIZED
C4-I — DONE — MERGED AND EXACT-HEAD VERIFIED
CR-011 — ACCEPTED — ADR 0018 NORMATIVE ON MAIN
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-B — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

## A4 packaging consequences

A4 adds no runtime dependency and no package resource beyond frontend source/build output and launcher Python already included by the application.

The native picker remains the macOS-provided `/usr/bin/osascript` adapter from A3. Mac App Store sandbox compatibility is **not claimed**; a later packaging decision may replace the picker adapter without moving path authority into the browser.

The one-use bootstrap token is launch-time memory only and travels in the browser URL fragment. It is removed immediately by the SPA. The run-scoped session token is stored only in `sessionStorage`, never `localStorage`, package files, logs or persistent config. Same-tab non-secret command replay metadata lives only in `history.state`.

A packaged build must preserve script ordering so `restore-control-entry.js` loads before `main.js`, allowing fragment capture/removal before ordinary shell route resolution.

C4-II-B destructive Restore remains not authorized.
