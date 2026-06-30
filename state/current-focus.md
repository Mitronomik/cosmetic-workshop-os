# Current focus

PR58 is complete: client wishes and append-only feedback are available in the client-card UI, including follow-up fixes that preserve open wish/feedback drafts during background refreshes and client-card saves.

The repository is now past stock, recipe, catalog, client, client recipe, ClientRecipe composition, restore, and client wishes/feedback foundations. Future Codex tasks should not start from the older PR24/PR26 catalog focus.

## Next recommended implementation step

Orders backend foundation.

The next PR should be a narrow backend/domain/data-model slice for orders only, aligned with Phase 4 in the roadmap. It should preserve the existing local-first/API-first architecture, keep user data outside the repository, avoid mutating historical recipes/client recipes, and add migrations/tests only for the explicitly scoped order backend work.

## Still out of scope until explicitly requested

- Production readiness and production confirmation.
- Automatic stock write-off and production batches.
- Alerts and purchase suggestions.
- Import/export workflows.
- Backup/restore UI.
- Final user packaging/macOS distribution.
- Cloud sync, mobile app/view, OCR, auth, and roles.
