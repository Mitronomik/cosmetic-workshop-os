# frontend/AGENTS.md

Scope: everything under `frontend/`.

Frontend-wide rules:

- Use Russian, human-readable labels and messages for user-facing UI.
- Do not show raw stack traces, internal IDs, database errors or developer-centric names to the user.
- Every empty state must explain what is missing and what the user can do next.
- Dangerous or destructive actions require clear confirmation.
- The frontend must not implement critical business calculations alone.
- The backend API is the source of truth for recipes, production, inventory, stock write-off, cost, tax and margin calculations.
- Frontend forms must guide the user with clear validation messages and next actions.
- Frontend changes require a build check; user-visible workflow changes also require relevant smoke testing.

UI/UX contract references:

- For frontend, visual, accessibility, responsive, or motion work, read `docs/ui-ux-contract.md`, `docs/ui-skill-policy.md`, and `.agents/skills/cosmetic-workshop-ui/SKILL.md` before changing UI.
- Verify affected routes at desktop and narrow-screen widths when UI changes are made.
- Changed flows must account for loading, empty, error, success, and disabled states.
- Preserve keyboard navigation, visible focus, and reduced-motion expectations.
- Project documentation and architecture rules override third-party design skills.
