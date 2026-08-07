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
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
```

A1 added no packaging implementation or dependency.

A2 may implement only launcher runtime control/session behavior. It may start an
exact-run loopback control listener from launcher lifecycle, but must not add
packaging implementation, new runtime dependency, real picker, or browser
bootstrap-fragment handoff.

Production A2 source selection remains typed `picker_unavailable`. The real
`/usr/bin/osascript` picker remains A3. The first production browser handoff
remains A4.

C4-II-B destructive Restore remains not authorized.
