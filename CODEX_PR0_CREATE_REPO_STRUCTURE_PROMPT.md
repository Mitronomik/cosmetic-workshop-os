# Task: PR0 - Project documentation contract and repository structure

## Context

You are a senior full-stack product engineer working on `cosmetic-workshop-os`.

Treat this task as a scoped PR contract.

This repository is new. The goal is to create the initial project structure and place the documentation files in the correct locations.

## Goal

Create a documentation-first repository structure for a local-first web app for a cosmetic workshop. This PR must prepare the repo for future Codex tasks without implementing application code.

## Scope

Create or update only root project files, documentation files, state files, nested `AGENTS.md`, help article placeholders, empty starter directories and placeholder scripts.

## Non-goals

Do not implement backend code, frontend code, database models, migrations, tests, real launcher runtime, inventory, recipes, clients, orders, production, imports, cloud, mobile or OCR.

## Architecture constraints

- MVP is local-first.
- User data must stay outside app/repo.
- User mode must not require Git, Python, Node.js, Docker or terminal.
- Backend must be API-first even when local.
- Business logic must live in backend domain services.
- RecipeTemplate, RecipeVersion and ClientRecipe are separate concepts.
- Inventory changes must go through StockMovement.
- Production must be transactional.
- Imports must go through ImportDraft and user confirmation.
- UI must be human-readable and non-technical.

## Testing requirements

This is a docs/structure PR. Run docs-only smoke: verify file paths, verify no application code was implemented, verify no secrets are present.

## Acceptance criteria

- Required root files exist.
- Required docs exist.
- Required state files exist.
- Nested `AGENTS.md` files exist.
- ADR directory exists with starter ADRs.
- Help directory exists with starter help articles.
- Backend/frontend/launcher starter directories exist.
- No app code is implemented.
- The repository is ready for PR1 - App shell.

## PR summary format

Use:

## Summary
## Scope
## Docs changed
## Structure created
## Tests / checks
## Risks / limitations
## Follow-up
