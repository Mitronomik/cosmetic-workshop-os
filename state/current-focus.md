# Current focus

PR23 is implemented: backend client recipe foundation for individual client formulas. Client recipes are first-class persisted entities linked to clients and source recipe versions, with their own `client_recipe_ingredients` snapshot lines so later base recipe changes do not silently mutate the client formula.

Scope intentionally excludes frontend client recipe UI, orders, production, stock reservation/write-off, cost/tax/margin, imports, cloud, mobile, OCR, auth, and roles.
