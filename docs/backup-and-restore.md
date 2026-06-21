# Backup and Restore

Default user data directory: `~/Documents/Мастерская косметолога/`.

Expected local user-data layout:

```text
~/Documents/Мастерская косметолога/
  data/
    cosmetic_workshop.sqlite
  backups/
  exports/
  attachments/
  logs/
```

Current foundation behavior:

- Development mode still uses repository-root `.local/cosmetic_workshop.sqlite` unless `COSMETIC_WORKSHOP_DB_PATH` is set.
- User-mode path resolution targets the default user data directory above, or `COSMETIC_WORKSHOP_USER_DATA_DIR` when explicitly overridden.
- Directory creation and database migration are explicit startup actions, not side effects of ordinary status/read endpoints.
- Before schema migration in packaged user mode, a future launcher/startup step must create an automatic backup. The backup and restore flow will be finalized during backup/restore PRs.
