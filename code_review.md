# Code Review Checklist

## Scope
- [ ] PR matches one roadmap step.
- [ ] Non-goals were not implemented.

## Architecture
- [ ] Local-first preserved.
- [ ] User data stays outside app/repo.
- [ ] Business logic is not only in frontend.
- [ ] DB changes have migrations.

## Domain
- [ ] RecipeTemplate, RecipeVersion and ClientRecipe remain separate.
- [ ] Inventory changes go through StockMovement.
- [ ] Production is transactional.
- [ ] Import uses ImportDraft and confirmation.
- [ ] Important actions are audited.

## UI/UX
- [ ] UI is human-readable.
- [ ] Empty states explain next action.
- [ ] Dangerous actions require confirmation.

## Testing
- [ ] Tests were added/updated.
- [ ] Relevant checks were run.
- [ ] Smoke was run if applicable.

## Docs/state
- [ ] Relevant docs/state were updated.
