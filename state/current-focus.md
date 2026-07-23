# Current focus — PR #137 B3.4+B3.5 ownership correction

- PR #136 is merged; B3.3 is complete at merge commit `e7c2d97473070f361052325fd6476208629af1cc`.
- PR #137 remains open and under review on `codex/b3.4-b3.5-core-workspace-feedback`.
- Active combined slice: B3.4+B3.5 — Formula/Client Workspace plus Inventory/Catalog Workspace.
- Starting `main` SHA: `e7c2d97473070f361052325fd6476208629af1cc`.
- Published PR head before this correction: `8c58e5e1466f05aa27950e2157f597e3fa4414b3`.
- B3.4+B3.5 is not DONE. B3.6 remains the next slice after review and merge.

## Correction under review

- Read ownership is now route-, operation-, entity-context-, generation-, and request-owned.
- A same-operation context switch explicitly supersedes the previous owner; late obsolete completion cannot apply data, feedback, announcement, or focus, and cannot leave an active owner behind.
- Mutation completion includes exact entity context and rejected/obsolete paths release their UI and lifecycle ownership.
- Reconciliation is an exact structured obligation containing the originating mutation, mutation context, required authoritative read operation/context, epoch, detached-settlement state, and one-shot automatic queue state.
- Domain adapters map every migrated mutation to an existing authoritative GET surface.
- Formula/Client manual refresh can target an exact Recipe Version, Client Wish, Client Feedback, or ClientRecipe composition obligation.
- StockMovement obligations remain attached to the original lot. Only validated history plus balance GETs for that lot may clear the lock; reference/list/overview/wrong-lot reads cannot.
- StockMovement still sends exactly one POST. At most one post-settlement automatic authoritative GET is consumed; failure does not loop and manual retry remains available.

## Scope boundaries

No backend production code, backend APIs, migrations, dependencies, lockfiles, Orders, Production, unsupported RecipeTemplate/RecipeVersion updates, persisted RecipeIngredient CRUD, ClientRecipe calculation, Feedback update, Packaging StockMovement, or StockMovement update/delete are included.

External smoke-authoring contract not stored in the repository; not required for this smoke-deferred runtime slice.

Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.
