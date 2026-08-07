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
C4-II-A2 — IMPLEMENTED IN CURRENT CHANGESET — NOT YET CLOSED
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE + LIFECYCLE UPDATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
C4-II-B — PLANNED — NOT AUTHORIZED
```

A1 remains the merged launcher-owned non-destructive validation boundary. A2 now
adds the separate exact-run launcher control listener with:

- exact `127.0.0.1` + OS-assigned ephemeral port;
- exact Host and configured local frontend Origin;
- one-use bootstrap and run-scoped session token;
- no wildcard CORS/cookie authority and no-store responses;
- 15-second heartbeat / 60-second authenticated inactivity expiry;
- concurrent state/heartbeat/cancel servicing;
- strict monotonic `command_seq` and idempotent retry semantics;
- A1 generation/proof invalidation.

Launcher runtime starts this control plane only after the owned backend has proved
its liveness lock and listening socket. Control authority is closed/quiesced
before the backend is stopped and before launcher lifecycle release.

If control startup is unsafe, ordinary workshop operation continues with Restore
control unavailable. No alternate transport is invented.

Production A2 uses typed `picker_unavailable` and obtains no source path. Browser
requests may not supply `path`, `source_path`, file bytes or equivalent filesystem
authority. The real `/usr/bin/osascript` picker remains A3.

A2 does not change the production browser launch URL: no `#cw-control`, bootstrap
capability, control port or session token is appended. `/backups/restore` and the
first production browser handoff remain A4.

No A1–A4 slice may add destructive Restore authority. C4-II-B remains separately
not authorized.
