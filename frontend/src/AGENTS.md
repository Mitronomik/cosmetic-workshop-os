# frontend/src/AGENTS.md

Scope: frontend source code under `frontend/src/`.

Source-structure rules:

- Keep route pages, features, entities, widgets and shared code separated.
- Route-level pages should compose features and widgets; they should not contain complex domain logic.
- Shared UI components must be reusable and not domain-specific unless intentionally placed in a domain area.
- API client code must be centralized instead of duplicated inside pages/components.
- Forms must show Russian, human-readable validation messages and suggested next actions.
- User-facing labels, statuses, empty states and errors should be Russian.
- Do not duplicate critical calculation logic from the backend; display backend-calculated results and warnings.
