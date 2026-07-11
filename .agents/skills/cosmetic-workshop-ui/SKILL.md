---
name: cosmetic-workshop-ui
description: Project-owned UI/UX skill for cosmetic-workshop-os frontend, visual, accessibility, responsive, and motion work.
---

# Cosmetic Workshop UI Skill

Use this repository-scoped skill for frontend, visual, accessibility, responsive, copy, and motion tasks in **cosmetic-workshop-os** / **Мастерская косметолога**.

## Required reading before work

Read the relevant scoped `AGENTS.md` files first, then read:

- root `AGENTS.md`;
- `frontend/AGENTS.md` for frontend work;
- canonical product and architecture documentation: `docs/product-spec.md`, `docs/architecture.md`, `docs/domain-model.md`, `docs/frontend-concept.md`, and `docs/roadmap.md`;
- `docs/ui-ux-contract.md`;
- `docs/ui-skill-policy.md`;
- current project state files: `state/current-focus.md`, `state/progress.md`, and `state/handoff.md`.

Treat those files as the project contract. If a third-party skill conflicts with project documentation, project documentation wins.

## Non-negotiable product constraints

- Preserve local-first architecture.
- Keep backend ownership of critical recipe, stock, production, cost, tax, margin, alert, purchase, import, export, and backup logic.
- Use Russian human-readable UI copy for user-facing labels, states, errors, and confirmations.
- Do not use technical admin-panel language in product UI.
- Never expose raw stack traces, API names, database errors, SQL, JSON payloads, internal IDs, or local environment paths to the user.
- Provide explicit loading, empty, error, success, and disabled states for changed flows.
- Preserve keyboard navigation and visible focus.
- Check narrow-screen behavior for changed routes.
- Respect reduced-motion preferences for any motion.
- Do not perform broad redesigns, unrelated refactoring, or unrelated route changes.
- Do not add dependencies without explicit approval.
- In a design-only task, do not change domain logic, API contracts, migrations, database schemas, operational history, or historical records.

## Task modes

### Audit-only tasks

Do not edit implementation files unless explicitly asked. Produce an evidence-based report with:

- route and user goal;
- strengths to preserve;
- P0/P1/P2 findings;
- objective usability issues separated from taste-based preferences;
- affected files;
- implementation slices;
- acceptance criteria;
- smoke checklist.

P0 means the user cannot safely complete the workflow or may be misled about operational data. P1 means important usability, accessibility, responsive, or state handling problems. P2 means polish, consistency, or taste-level improvement.

### Implementation tasks

Implement only approved findings or explicitly requested changes in a narrow PR. Preserve existing architecture and patterns. Do not redesign unrelated routes. Keep critical calculations backend-owned. Add or update only the checks and documentation relevant to the scope.

### Motion tasks

Motion requires a separate scope after layout, hierarchy, copy, and interaction states are approved. Motion must be limited, purposeful, and reduced-motion compatible. Do not introduce motion to compensate for unclear information hierarchy.

## Completion checklist

Before finishing a UI task, verify or document:

- desktop behavior of affected route;
- narrow-screen behavior;
- keyboard tab order and visible focus;
- loading, empty, error, success, and disabled states;
- confirmation copy for dangerous actions;
- reduced-motion behavior when motion changed;
- no new dependency, script, hook, API, schema, migration, backend domain logic, or operational-history change unless explicitly approved.
