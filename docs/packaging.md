# Packaging

Package must include launcher, backend runtime, frontend build, migrations, default config and help files. It must not include real user database, backups, exports, logs or secrets.

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

## Restore packaging consequence

```text
ordinary browser
→ launcher-owned 127.0.0.1:<ephemeral> control plane
→ launcher-owned /usr/bin/osascript picker
→ launcher-owned validation session
```

## C4-II-A status

```text
PR #178 — MERGED — C4-II-A3 EXACT-HEAD VERIFIED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A4 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-B — PLANNED — NOT AUTHORIZED
Restore — NOT IMPLEMENTED
Product release readiness — NOT CLAIMED
```

A3 remains dependency-free and uses macOS-provided `/usr/bin/osascript`. Mac App Store sandbox compatibility is **not claimed**.

A4 changes browser/session wiring only; it does not authorize packaging work. Bootstrap material may appear only in the initial URL fragment and must be removed immediately by SPA. Run-scoped session descriptors may live only in `sessionStorage`; secrets must not enter query params, logs, persistent storage or bundle resources.

C4-II-B destructive Restore remains not authorized.