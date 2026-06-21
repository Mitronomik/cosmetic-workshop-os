# Local runtime launcher MVP

This directory contains the first minimal local runtime foundation for **Мастерская косметолога**.

Current scope:

- resolve repository/backend/frontend runtime paths;
- build safe localhost runtime configuration;
- explicitly run backend startup initialization in `user` mode by default;
- start the FastAPI backend on `127.0.0.1:8000`;
- optionally open the browser at the current frontend development URL placeholder.

This is **not** final packaging. It is not a macOS `.app`, `.dmg`, installer, Electron shell, Docker runtime, service daemon, or auto-updater.

Developer command:

```bash
python3 -m launcher.main --no-browser
```

The launcher respects `COSMETIC_WORKSHOP_USER_DATA_DIR` through the existing backend user-data resolver. User data must stay outside the repository/package directory.
