# Packaging

Package must include launcher, backend runtime, frontend build, migrations,
default config and help files. It must not include real user database, backups,
exports, logs or secrets.

## Current status

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

## Restore packaging consequence

ADR 0018 topology remains:

```text
ordinary browser
→ launcher-owned 127.0.0.1:<ephemeral> control plane
→ launcher-owned /usr/bin/osascript picker
→ launcher-owned validation session
```

## C4-II-A status

```text
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
```

A3 uses only macOS-provided `/usr/bin/osascript` + Standard Additions `choose
file`. It adds no Python/application dependency and no bundle resource.

The picker is an owned short-lived child using fixed AppleScript, `shell=False`,
no `System Events`, typed cancellation, launcher-private POSIX path and owned
terminate/reap with kill fallback on cancel/expiry.

Mac App Store sandbox compatibility is **not claimed**. A later sandbox/packaging
decision may replace the picker adapter while preserving launcher ownership and
path privacy unless a later ADR explicitly changes them.

Production browser launch URL remains unchanged through A3. No `#cw-control`,
control port, bootstrap capability or session token is added to navigation; first
production handoff remains A4.

C4-II-B destructive Restore remains not authorized.
