# Local Install for Developers

Status: skeleton. Planned commands: `make setup`, `make dev`, `make test`.

Development persistence defaults:

- Default development SQLite path: `.local/cosmetic_workshop.sqlite` at the repository root.
- Override the database file with `COSMETIC_WORKSHOP_DB_PATH=/path/to/cosmetic_workshop.sqlite`.
- User-mode data directory resolution exists for launcher/startup preparation, but developer commands do not silently switch to the user Documents folder.
