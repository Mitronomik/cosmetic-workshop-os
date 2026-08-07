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

The expected picker is macOS-provided `/usr/bin/osascript` + Standard Additions
`choose file`; no new application dependency is authorized. Mac App Store sandbox
compatibility is not claimed and remains a future packaging decision.

## C4-II-A status

```text
C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A2 — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
```

A1 adds no packaging implementation and no dependency. Its validation scratch is
runtime system-temp state only. It does not bundle or invoke `/usr/bin/osascript`,
does not add a control listener and does not change the production browser launch
URL.

A2/A3/A4 packaging consequences remain separately gated. C4-II-B destructive
Restore remains not authorized.
