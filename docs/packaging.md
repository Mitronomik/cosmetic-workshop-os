# Packaging

Package must include launcher, backend runtime, frontend build, migrations,
default config and help files. It must not include real user database, backups,
exports, logs or secrets.

## Current status

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

## Restore packaging consequence

ADR 0018 eventually requires:

```text
ordinary browser
→ launcher-owned 127.0.0.1:<ephemeral> control plane
→ launcher-owned /usr/bin/osascript picker
→ launcher-owned validation session
```

The expected future picker is macOS-provided `/usr/bin/osascript` + Standard
Additions `choose file`; no new application dependency is authorized. Mac App
Store sandbox compatibility is not claimed and remains a future packaging
decision.

## C4-II-A status

```text
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
```

A1 added no packaging implementation or dependency.

A2 adds only launcher runtime control/session code using Python standard-library
HTTP/threading/secrets primitives. It starts a loopback control listener during
launcher lifetime but adds no packaging implementation, dependency or bundle
resource.

Production A2 source selection remains typed `picker_unavailable` through
`UnavailableSourceSelectionAdapter`; it does not invoke `/usr/bin/osascript`.
The real picker remains A3.

Production browser launch URL remains unchanged in A2. No `#cw-control`, control
port, bootstrap capability or session token is added to the browser URL; first
production handoff remains A4.

C4-II-B destructive Restore remains not authorized.
