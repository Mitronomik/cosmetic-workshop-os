# Deployment

MVP is local-first. User mode must not require Git, terminal, Python, Node.js or
Docker.

## Current status

- launcher local runtime foundation exists;
- local FastAPI remains bound to `127.0.0.1`;
- user data remains outside repository/package;
- backup-before-migration remains part of startup;
- ordinary browser remains the product UI;
- final macOS `.app`/`.dmg` packaging is not implemented.

## Restore topology

ADR 0018 remains:

```text
browser presentation
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned local control boundary
                         127.0.0.1:<ephemeral>
                         → launcher-owned /usr/bin/osascript picker
                         → non-destructive candidate validation
```

## C4-II-A status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

A1 is merged and provides only launcher-owned non-destructive validation. Its
scratch is system-temp state, not durable application Restore state. The ordinary
backend remains running during validation.

After this lifecycle closure merges, A2 may add a separate launcher-owned local
control listener with exact `127.0.0.1`, OS-assigned ephemeral port, exact
Host/Origin checks, one-use bootstrap/session tokens, no-store state, heartbeat /
inactivity expiry, request sequencing and A1 cancel/invalidation integration.

Production A2 must keep the source-selection adapter at typed
`picker_unavailable`; it obtains no source path. Browser/control requests may not
supply a path or file payload.

A2 does not change the production browser launch URL. The first real browser
bootstrap-fragment handoff remains A4 scope.

A3 later owns the real `/usr/bin/osascript` + Standard Additions `choose file`
picker. A4 later owns `/backups/restore` and production browser session UX.

No A1–A4 slice may add destructive Restore authority. C4-II-B remains separately
not authorized.
