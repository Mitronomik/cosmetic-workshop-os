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
C4-II-A1 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A2 — BLOCKED BY A1 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

A1 implements only launcher-owned non-destructive validation. Its scratch is
system-temp state, not durable application Restore state. The ordinary backend
remains running during A1 validation.

A1 may not implement the control plane, picker or frontend UI. In particular it
contains no loopback HTTP listener, browser bootstrap/session token, `command_seq`,
`/usr/bin/osascript` invocation or `/backups/restore` route.

A2 later owns exact `127.0.0.1` control binding and session/security protocol. A3
later owns the real `/usr/bin/osascript` + Standard Additions `choose file`
picker. A4 later owns production browser bootstrap handoff and UI.

No A1–A4 slice may add destructive Restore authority. C4-II-B remains separately
not authorized.
