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

ADR 0018 selects a separate launcher-owned local control boundary for future
Restore source selection/validation:

```text
browser presentation
  ├── ordinary business API → FastAPI backend
  └── Restore control → launcher-owned 127.0.0.1:<ephemeral>
                         → launcher-owned native picker
                         → non-destructive candidate validation
```

The Restore control plane is not an ordinary FastAPI route and may never bind to
LAN/remote interfaces.

Future C4-II-A, when separately authorized, must use:

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

C4-II-A remains `PLANNED — NOT AUTHORIZED` until a separate post-CR-011 task
explicitly authorizes runtime implementation.