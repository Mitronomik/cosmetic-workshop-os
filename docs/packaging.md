# Packaging

Package must include launcher, backend runtime, frontend build, migrations,
default config and help files. Package must not include real user database,
backups, exports, logs or secrets.

## Current status

macOS `.app` / `.dmg` packaging is **NOT COMPLETED**.

The current launcher/runtime foundation is not final user packaging.

## CR-011 Restore interaction consequence

ADR 0018 selects a browser-first Restore interaction architecture without adding
a general native shell:

```text
ordinary browser
→ launcher-owned loopback control plane
→ launcher-owned macOS picker
→ launcher-owned validation session
```

The accepted future runtime boundary requires the launcher to be able to:

- remain alive for the browser/product session;
- own an HTTP control listener bound only to `127.0.0.1` on an ephemeral port;
- open the browser with a one-use bootstrap capability in the URL fragment;
- own a short-lived `/usr/bin/osascript` child using macOS Standard Additions
  `choose file` for source selection;
- keep the absolute selected-source path launcher-private;
- clean run-scoped tokens and validation scratch on shutdown.

CR-011 authorizes **no new application dependency** for this boundary.

The current expected picker mechanism uses the macOS-provided
`/usr/bin/osascript`; it is not bundled into the package.

This decision does not implement packaging and does not claim Mac App Store
sandbox compatibility. A future App Store/sandbox decision may need a different
native picker adapter, for example an `NSOpenPanel`-based adapter with
security-scoped file access, but it must preserve launcher ownership and path
privacy unless a later ADR explicitly changes those semantics.

## C4-II-A authorization state

C4-II-A is authorized only through the bounded slice plan in
`docs/c4-ii-a-implementation-slices.md`.

```text
C4-II-A1 — AUTHORIZED NEXT — validation-session core only
C4-II-A2 — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
```

This authorization does **not** complete packaging and does not authorize hidden
packaging changes inside A1–A4. Any required packaging implementation remains a
separate bounded obligation.

C4-II-B destructive Restore remains not authorized.
