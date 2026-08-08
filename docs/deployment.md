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
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → A3 native macOS picker
                         → non-destructive A1 candidate validation
```

## C4-II-A status

```text
C4-II-A — IN PROGRESS — SLICED
C4-II-A1 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A2 — DONE — MERGED AND EXACT-HEAD VERIFIED
C4-II-A3 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

A2 remains the exact-run control/session authority. A3 now injects only the
launcher-owned native picker into its existing source-selection seam:

- exact `/usr/bin/osascript`;
- Standard Additions `choose file`;
- fixed script, no user interpolation;
- `shell=False`, no `System Events`;
- typed user cancel;
- absolute POSIX path only in launcher memory;
- owned child terminate/reap with kill fallback on cancel/expiry;
- no new dependency.

The selected path flows only into merged A1 validation. Browser requests remain
pathless. A1/C4-I remains acceptance authority.

Production browser navigation remains unchanged through A3: no `#cw-control`,
bootstrap capability, control port or session token is appended. `/backups/restore`
and first production browser handoff remain A4.

No A1–A4 slice may add destructive Restore authority. C4-II-B remains separately
not authorized.
