# Deployment

MVP is local-first. User mode must not require Git, terminal, Python, Node.js or
Docker.

## Current status

- launcher MVP foundation exists under `launcher/`;
- launcher initializes user-mode backend startup and starts local FastAPI on
  `127.0.0.1`;
- user data remains outside repository/package and can be redirected with
  `COSMETIC_WORKSHOP_USER_DATA_DIR` for isolated tests/developer smoke;
- backup-before-migration remains part of explicit user-mode startup;
- launcher opens the ordinary system browser for the product UI;
- final macOS `.app`/`.dmg` packaging is not implemented.

Developer-only runtime command:

```bash
python3 -m launcher.main --no-browser
```

This command is not the final user workflow.

## CR-011 selected Restore control topology

ADR 0018 selects a separate launcher-owned local control boundary for Restore
source selection/validation:

```text
browser presentation
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → launcher-owned native picker
                         → non-destructive candidate validation
```

The Restore control plane is not an ordinary FastAPI route and may never bind to
LAN/remote interfaces.

The accepted C4-II-A architecture requires:

- exact `127.0.0.1` loopback binding;
- OS-assigned ephemeral port;
- exact configured local frontend Origin;
- one-use browser bootstrap capability in URL fragment;
- run-scoped session token only;
- no wildcard CORS;
- no durable/reusable control token;
- launcher-owned `/usr/bin/osascript` + Standard Additions `choose file` picker;
- no absolute selected-source path in browser or ordinary backend state.

The ordinary backend remains running during non-destructive source selection and
validation. Destructive backend exclusion/stop remains part of future C4-II-B /
existing C4-I execution semantics.

CR-011 does not implement the control plane, picker, validation session,
packaging, updater, service daemon, Electron/Tauri shell, cloud sync or remote
access.

## C4-II-A authorization state

Implementation is authorized only through
`docs/c4-ii-a-implementation-slices.md`:

```text
C4-II-A — AUTHORIZED AS SLICED — NOT IMPLEMENTED
C4-II-A1 — AUTHORIZED NEXT — validation-session core only
C4-II-A2 — BLOCKED BY A1 MERGE + EXACT-HEAD GATE
C4-II-A3 — BLOCKED BY A2 MERGE + EXACT-HEAD GATE
C4-II-A4 — BLOCKED BY A3 MERGE + EXACT-HEAD GATE
```

A1 may not implement the control plane, picker or frontend UI. Those remain
separately gated A2/A3/A4 slices.

No A1–A4 slice may add destructive Restore authority. C4-II-B remains separately
not authorized.
