# Current focus — PR #137 detached settlement and recipe snapshot correction

- PR #136 is merged; B3.3 is complete at merge commit `e7c2d97473070f361052325fd6476208629af1cc`.
- PR #137 remains open, non-draft, and under review on `codex/b3.4-b3.5-core-workspace-feedback`.
- Active combined slice: B3.4+B3.5 — Formula/Client Workspace plus Inventory/Catalog Workspace.
- Starting `main` SHA: `e7c2d97473070f361052325fd6476208629af1cc`.
- Published PR head before this correction: `b95b0b293f6f381495fa9e08d36b1ad27a214252`.
- B3.4+B3.5 is not DONE. B3.6 remains the next slice after review and merge.

## Correction under review

- Both production workspace runtimes now finalize every accepted mutation request exactly once, including known success, definite failure, ambiguous failure, invalid DTO, detached completion, obsolete context, and stale ownership. Rejected mutation starts do not run a finalizer.
- Finalization is limited to route-local busy-state/control recovery and route-loader resumption. It does not apply DTOs, clear drafts/forms, announce, move focus, clear reconciliation, or retry a write.
- Direct RecipeTemplate, RecipeVersion, Client, Ingredient, Ingredient Lot, and Packaging mutations use the same route-local finalization primitive, so leaving and returning cannot strand saving flags.
- ClientRecipe create, composition, archive, and restore recover after detached settlement while retaining their exact reconciliation obligation.
- RecipeTemplate detail and its RecipeVersion list now load as one context-owned atomic snapshot. Neither half is committed until both validate for the same template; a partial failure commits neither half.
- RecipeVersion reconciliation remains a separate exact `recipe-version-list` / `template:<id>` read and updates visible versions only when that template is still selected.
- Structured reconciliation and original-lot StockMovement safety from the prior correction remain unchanged: exactly one POST, one post-settlement automatic GET opportunity, no automatic retry loop, and manual original-lot recovery.

## Scope boundaries

No backend production code, backend APIs, migrations, dependencies, lockfiles, Orders, Production, unsupported RecipeTemplate/RecipeVersion updates, persisted RecipeIngredient CRUD, ClientRecipe calculation, Feedback update, Packaging StockMovement, or StockMovement update/delete are included.

External smoke-authoring contract not stored in the repository; not required for this smoke-deferred runtime slice.

Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
