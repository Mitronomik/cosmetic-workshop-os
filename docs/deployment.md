# Deployment

MVP is local-first. User mode must not require Git, terminal, Python, Node.js or Docker.

Current status:

- A launcher MVP foundation exists under `launcher/`.
- The launcher can explicitly initialize backend startup in user mode and start the local FastAPI backend on `127.0.0.1`.
- User data remains outside the repository/package directory and can be redirected with `COSMETIC_WORKSHOP_USER_DATA_DIR` for tests/developer smoke.
- Backup-before-migration remains part of the explicit user-mode startup path.

Developer-only runtime command:

```bash
python3 -m launcher.main --no-browser
```

This is not final deployment packaging. It does not provide a macOS `.app`, `.dmg`, installer, Electron shell, Docker runtime, service daemon, auto-update, cloud sync, or remote access.
