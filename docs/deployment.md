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
                         → launcher-owned picker adapter
                         → non-destructive A1 candidate validation
```

## C4-II-A status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — AUTHORIZED NEXT — NOT IMPLEMENTED
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

A2 is merged and exact-head verified. Its control plane remains exact loopback,
ephemeral, exact Host/configured Origin, one-use bootstrap, run-scoped token,
no-store/narrow CORS, 15s/60s liveness, strict `command_seq` and one long-work
owner with responsive state/heartbeat/cancel.

A3 may now add only the launcher-owned native macOS picker behind the existing A2
adapter seam:

- `/usr/bin/osascript`;
- Standard Additions `choose file`;
- fixed script, no user interpolation;
- no `shell=True`, no `System Events`;
- typed cancellation;
- absolute POSIX path only in launcher memory;
- owned child termination/quiescence on cancel/expiry;
- no new dependency.

The selected path remains launcher-private and flows only into merged A1
validation. Browser requests may not supply path/file authority.

A3 does not change production browser navigation. No `#cw-control`, bootstrap
capability, control port or session token is appended; `/backups/restore` and the
first production browser handoff remain A4.

No A1–A4 slice may add destructive Restore authority. C4-II-B remains separately
not authorized.
