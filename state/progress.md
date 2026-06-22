# Progress

- PR23 adds `client_recipes` and `client_recipe_ingredients` migrations and table-guard policy updates.
- Backend domain/model/schema/repository/service/API layers now support creating a client recipe from an existing recipe version, reading details, listing all client recipes, listing recipes for one client, and soft deactivation/archive.
- Client recipe creation snapshots source recipe ingredient rows into independent `client_recipe_ingredients` rows; details read those snapshot rows, not live source recipe rows.
- Client recipe writes and `client_recipe.created` / `client_recipe.deactivated` audit events are transactional, with rollback coverage for audit and snapshot-line failures.
- No UI, orders, production behavior, stock reservation/write-off, import/export, or backup behavior changes were added.
