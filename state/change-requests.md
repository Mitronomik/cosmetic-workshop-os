# Change Requests

| ID | Date | Request | Status | Target PR | Notes |
|---|---|---|---|---|---|
| CR-001 | 2026-06-21 | Add Codex project memory structure | accepted | PR0 | Required for safe Codex workflow |
| CR-002 | 2026-07-26 | Close B4 with the Dashboard safe-GET pilot only and defer remaining read-route timeout coverage | accepted | | Alerts, Purchases, Orders, Reports, Backups, Exports and Report Documents were not delivered; expansion needs a separately authorized slice |
| CR-003 | 2026-07-26 | Open the backend baseline correction gate | accepted | | Covers exactly the four accepted backend baseline failures; evidence in `docs/backend-baseline-failure-triage.md`; one active slice at a time |
| CR-004 | 2026-07-26 | Investigate potential SQLite backup transaction consistency | needs evidence | | Separate evidence-based diagnostic; not classified, scoped or activated; not one of the four gate failures |
| CR-005 | 2026-07-26 | Decide the backup/export filename normalization and hyphen round-trip contract | needs product decision | | Blocks the two `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED` gate nodes. Must cover: whether consecutive unsafe characters collapse to one underscore; whether literal hyphens remain allowed; how backup filename-to-metadata reason round-trip works; whether displayed reason is filename-derived or stored independently; the required focused smoke after implementation. No slice may open until decided |
