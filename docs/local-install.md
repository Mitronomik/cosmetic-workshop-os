# Local Install for Developers

Status: launcher MVP foundation exists; final user packaging is still planned.

Planned/available commands:

- `make setup` - install backend and frontend developer dependencies.
- `make dev` - print separate backend/frontend development commands.
- `make run-local` - run the launcher MVP without opening the browser.
- `python3 -m launcher.main --no-browser` - start the minimal local backend runtime directly.
- `make test` - run backend and launcher tests from the repository root.

Development persistence defaults:

- Default development SQLite path: `.local/cosmetic_workshop.sqlite` at the repository root.
- Override the development database file with `COSMETIC_WORKSHOP_DB_PATH=/path/to/cosmetic_workshop.sqlite`.
- User-mode startup uses the user data resolver and creates data directories only through explicit startup initialization.
- Override the user-mode data directory with `COSMETIC_WORKSHOP_USER_DATA_DIR=/path/to/user-data`.

Launcher MVP behavior:

- Safe defaults: host `127.0.0.1`, backend port `8000`, frontend URL placeholder `http://127.0.0.1:5173`.
- Default mode is `user`, so startup uses the user data directory and the existing backup-before-migration path.
- The launcher starts only a local backend process in this PR. Static frontend serving/final desktop packaging are follow-up work.
- The launcher is developer-facing for now; the final product must not require the user to run terminal commands.
