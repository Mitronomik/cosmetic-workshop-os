# cosmetic-workshop-os - Codex Web Prompting Rules

Document: `docs/codex-prompting-rules.md`  
Project: `cosmetic-workshop-os`  
Human-facing name: `Мастерская косметолога`  
Purpose: define the rules for writing effective Codex Web prompts for this project.

---

## 1. Purpose of this document

This document defines how prompts for Codex Web must be written for `cosmetic-workshop-os`.

The goal is to make every Codex task:

- clear;
- scoped;
- testable;
- safe for architecture;
- aligned with project documents;
- understandable for Codex Web;
- suitable for PR-based development;
- resistant to scope creep;
- explicit about non-goals;
- explicit about testing;
- explicit about acceptance criteria.

Every implementation prompt for Codex Web must be written in English.

User-facing product texts may be Russian, but Codex task prompts must be English unless there is a specific reason to do otherwise.

---

## 2. Core principle

A Codex prompt is not a casual request.

For this project, every Codex prompt must be treated as a **small PR contract**.

Good prompt:

```text
Implement only PR5: Ingredients and IngredientLots backend.
Read the project contracts.
Follow the local-first architecture.
Add migrations.
Add tests.
Do not implement frontend, alerts, orders or production.
```

Bad prompt:

```text
Build the inventory system.
```

The second version is too broad and allows Codex to invent architecture, skip tests, add future features, or violate project boundaries.

---

## 3. Required project context for every Codex prompt

Every Codex prompt must tell the agent to read the relevant project memory files.

Minimum required files:

```text
AGENTS.md
docs/architecture.md
docs/roadmap.md
state/current-focus.md
state/progress.md
```

If the task touches a specific area, also require relevant documents:

Backend:

```text
backend/AGENTS.md
docs/domain-model.md
docs/api.md
docs/testing.md
```

Frontend:

```text
frontend/AGENTS.md
docs/ui-ux-contract.md
docs/frontend-concept.md if present
```

Launcher / packaging / local deployment:

```text
launcher/AGENTS.md
docs/deployment.md
docs/packaging.md
docs/user-install.md
docs/update-guide.md
docs/backup-and-restore.md
```

Docs:

```text
docs/AGENTS.md
docs/codex-project-structure.md
```

Import:

```text
docs/import-format.md
docs/domain-model.md
docs/testing.md
```

UI/onboarding:

```text
docs/ui-ux-contract.md
docs/user-guide.md
help/
```

---

## 4. Mandatory prompt sections

Every Codex Web implementation prompt must include these sections.

```markdown
# Task: <PR number and title>

## Context

## Goal

## Scope

## Non-goals

## Architecture constraints

## Backend requirements

## Frontend requirements

## Data model / migrations

## Testing requirements

## Documentation requirements

## Acceptance criteria

## Required checks

## PR summary format
```

If a section does not apply, keep it and write:

```text
Not applicable for this PR.
```

Do not remove the section. Consistent structure helps Codex follow the task.

---

## 5. Prompt language

Implementation prompts must be written in English.

Reasons:

- Codex usually follows technical English prompts more consistently;
- code, APIs, tests and errors are usually in English;
- PR summaries and technical contracts are easier to keep standardized;
- user-facing Russian labels can still be explicitly required.

Rule:

```text
Prompt language: English.
User-facing UI labels: Russian unless otherwise specified.
Code comments: English unless domain-specific Russian wording is required.
Documentation for user: Russian.
Technical docs: English or Russian, but be consistent inside each document.
```

---

## 6. Scope rules

Each prompt must define exactly what Codex is allowed to change.

Good scope:

```markdown
## Scope

Implement only:

- `Ingredient` model;
- `IngredientLot` model;
- Alembic migration;
- CRUD endpoints for ingredients and lots;
- backend validation;
- backend tests;
- minimal documentation update.
```

Bad scope:

```markdown
## Scope

Implement inventory.
```

The scope must be concrete enough to review.

---

## 7. Non-goals are mandatory

Every prompt must include explicit non-goals.

For this project, non-goals prevent Codex from adding future features too early.

Common non-goals:

```markdown
## Non-goals

Do not implement:

- frontend UI unless explicitly scoped;
- cloud sync;
- mobile app;
- OCR;
- AI recommendations;
- advanced analytics;
- production write-off unless this PR is about production;
- alerts unless this PR is about alerts;
- PDF export unless this PR is about PDF;
- Docker-only user deployment;
- any feature not listed in Scope.
```

A good prompt must tell Codex what not to do.

---

## 8. Architecture constraints that should appear often

For most implementation prompts, include this block.

```markdown
## Architecture constraints

- Keep the MVP local-first.
- Do not introduce mandatory cloud dependencies.
- Keep user data outside the app/repository directory.
- Keep business logic in backend domain services, not only in frontend.
- All database schema changes require migrations.
- Use Decimal for recipe, weight, density and money calculations.
- Do not silently mutate historical recipe versions.
- `RecipeTemplate`, `RecipeVersion` and `ClientRecipe` are separate concepts.
- Inventory changes must go through `StockMovement`.
- Production must be transactional.
- Imports must go through `ImportDraft` and user confirmation.
- UI must be human-readable and non-technical.
- Do not expose raw stack traces or internal IDs to the user.
- Do not add cloud, mobile, OCR or AI recommendations unless explicitly scoped.
```

Not every prompt needs every rule, but risky domain PRs should include the full block.

---

## 9. Project-specific hard rules

These rules must be preserved in all prompts where relevant.

### 9.1. Local-first

MVP must work locally on MacBook without internet.

Do not require the end user to:

- clone GitHub repository;
- install Python;
- install Node.js;
- install Docker;
- use terminal commands.

### 9.2. User data directory

User data must live outside app/repo.

Recommended location:

```text
~/Documents/Мастерская косметолога/
  data/
  backups/
  exports/
  attachments/
  logs/
```

### 9.3. Recipes

Do not flatten recipe concepts.

Use:

```text
RecipeTemplate
RecipeVersion
ClientRecipe
```

### 9.4. Inventory

Do not update stock silently.

Use:

```text
Ingredient
IngredientLot
StockMovement
```

### 9.5. Production

Production must be explicit and transactional.

```text
Readiness check
→ user confirmation
→ transaction
→ ProductionBatch
→ StockMovements
→ Order status update
→ AuditLog
```

### 9.6. Import

Imports must never write directly into production tables without preview and confirmation.

Use:

```text
ImportSource
→ ImportDraft
→ validation
→ preview
→ confirmation
→ apply
```

### 9.7. OCR

OCR is future scope. OCR output must always be a draft.

Never trust OCR automatically.

### 9.8. UI

User-facing UI must be simple and human-readable.

Every empty state must explain the next action.

Every dangerous action must require confirmation.

### 9.9. Updates

Before schema migration in user mode, create a backup.

---

## 10. Testing requirements

Every prompt must include testing expectations.

Use this pattern:

```markdown
## Testing requirements

Add or update tests for:

- <domain behavior>;
- <validation>;
- <error case>;
- <migration if applicable>;
- <transaction behavior if applicable>;
- <API endpoint if applicable>;
- <frontend build or UI smoke if applicable>.

Run available checks and report results.

If a check cannot be run, explain why.
```

### 10.1. Backend testing expectations

For backend PRs, require:

```text
pytest
migration test
API endpoint tests
domain service tests
validation tests
```

For calculation PRs:

```text
Decimal calculations
rounding
missing density warning
total percent validation
cost/tax/margin calculation
```

For inventory PRs:

```text
no negative stock
lot remaining quantity
StockMovement creation
audit logging
```

For production PRs:

```text
readiness check
FEFO lot selection
transaction rollback
cannot produce same order twice
StockMovement creation
ProductionBatch snapshot
```

For import PRs:

```text
parse valid file
reject invalid rows
show row/column/value errors
do not apply before confirmation
AuditLog on apply
```

### 10.2. Frontend testing expectations

For frontend PRs, require at minimum:

```text
frontend build
route smoke
form validation smoke
human-readable empty states
human-readable error messages
```

If frontend test tooling exists, add component tests for critical flows.

### 10.3. Packaging testing expectations

For deployment PRs, require:

```text
package starts
data directory created
database created
migrations applied
browser opens
data persists after restart
backup works
port conflict handled
```

### 10.4. Documentation testing

For docs-only PRs, require:

```text
links checked manually if possible
filenames match repository structure
instructions are consistent with roadmap and architecture
```

---

## 11. Required checks block

Every prompt must include a `Required checks` section.

Example:

```markdown
## Required checks

Run the available checks:

- backend tests;
- frontend build;
- lint/format checks if configured;
- migration check if schema changes;
- relevant smoke scenario.

Report:

- commands run;
- results;
- failures;
- checks not run and why.
```

Codex must not claim success without saying what it actually ran.

---

## 12. Acceptance criteria

Acceptance criteria must be concrete and verifiable.

Good:

```markdown
## Acceptance criteria

- `Ingredient` can be created through API.
- `IngredientLot` can be created for an ingredient.
- Negative lot quantity is rejected.
- `remaining_quantity` cannot exceed `initial_quantity`.
- Schema migration applies on an empty database.
- AuditLog entry is created for create/update/archive actions.
- Tests cover success and failure cases.
```

Bad:

```markdown
## Acceptance criteria

- Inventory works.
```

---

## 13. Documentation requirements

Every prompt should say whether docs need updates.

Use:

```markdown
## Documentation requirements

Update docs if the implementation changes:

- architecture;
- data model;
- API contract;
- roadmap status;
- user workflow;
- installation/update behavior.

Always update `state/progress.md` and `state/handoff.md` after meaningful work.
```

For docs-only prompts:

```markdown
## Documentation requirements

This is a docs-only PR. Do not change application code.
```

---

## 14. PR summary format

Every prompt must require this summary format.

```markdown
## Summary
- ...

## Scope
- ...

## Data model / migrations
- ...

## User-visible changes
- ...

## Tests
- ...

## Risks / limitations
- ...

## Follow-up
- ...
```

This makes Codex output easier to review.

---

## 15. Modern prompting techniques to use

Use these techniques in every important prompt.

### 15.1. Role and operating mode

Tell Codex what role to take.

```markdown
You are a senior full-stack product engineer working in a PR-sized task.
Treat this task as a scoped implementation contract.
```

### 15.2. Context anchoring

Tell Codex which files define the truth.

```markdown
The source of truth is:
- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/domain-model.md`
- `state/current-focus.md`
```

### 15.3. Scope boxing

Define exactly what is inside and outside scope.

```markdown
Implement only the items listed in Scope.
Do not implement any item listed in Non-goals.
If you discover related future work, document it under Follow-up instead of implementing it.
```

### 15.4. Constraint hierarchy

Give Codex a priority order.

```markdown
Priority order:
1. Preserve architecture.
2. Preserve data safety.
3. Keep scope small.
4. Add tests.
5. Keep UI human-readable.
6. Update docs/state.
```

### 15.5. Verification-first wording

Require tests and checks before claiming completion.

```markdown
Do not claim the task is complete unless the relevant checks were run or you clearly explain why they could not be run.
```

### 15.6. No hidden work

Tell Codex not to silently add extra features.

```markdown
Do not implement future roadmap items opportunistically.
Add follow-up notes instead.
```

### 15.7. Safety gates

Use explicit stop conditions.

```markdown
Stop and report instead of implementing if:
- required project files are missing;
- the current branch already has unrelated changes;
- migrations cannot be generated safely;
- the task requires cloud/OCR/mobile features not listed in Scope;
- tests cannot be run due to missing setup.
```

### 15.8. Output contract

Tell Codex what final answer must include.

```markdown
Final response must include:
- summary of changes;
- tests run;
- files changed;
- migrations added;
- risks;
- follow-up items.
```

---

## 16. Standard Codex Web prompt template

Use this template for most implementation PRs.

```markdown
# Task: <PR number> - <PR title>

## Context

You are a senior full-stack product engineer working on `cosmetic-workshop-os`.

Treat this task as a scoped PR contract.

Before making changes, read and follow:

- `AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/domain-model.md`
- `docs/ui-ux-contract.md`
- `docs/testing.md`
- `state/current-focus.md`
- `state/progress.md`
- relevant nested `AGENTS.md`

This PR implements only:

`<PR number and title from docs/roadmap.md>`

## Goal

<Describe the user value and engineering goal in 2-4 sentences.>

## Scope

Implement only:

- ...
- ...
- ...

## Non-goals

Do not implement:

- ...
- ...
- ...

If you discover related future work, document it in Follow-up instead of implementing it.

## Architecture constraints

- Keep the MVP local-first.
- Do not introduce mandatory cloud dependencies.
- Keep user data outside the app/repository directory.
- Keep business logic in backend domain services, not only in frontend.
- Add migrations for all database schema changes.
- Use Decimal for recipe, weight, density and money calculations where relevant.
- Do not silently mutate historical recipe versions.
- `RecipeTemplate`, `RecipeVersion` and `ClientRecipe` are separate concepts.
- Inventory changes must go through `StockMovement`.
- Production must be transactional.
- Imports must go through `ImportDraft` and user confirmation.
- UI must be human-readable and non-technical.
- Do not expose raw stack traces or internal IDs to the user.
- Do not add cloud, mobile, OCR, AI recommendations or advanced analytics unless explicitly scoped.

## Backend requirements

- ...

## Frontend requirements

- ...

## Data model / migrations

- ...

If no schema changes are needed, explicitly state that no migration is required.

## Testing requirements

Add or update tests for:

- ...
- ...

Run available checks and report results.

If a check cannot be run, explain why.

## Documentation requirements

Update documentation if this PR changes:

- architecture;
- roadmap;
- domain model;
- API contract;
- testing strategy;
- user workflow;
- deployment/update behavior.

Always update after meaningful work:

- `state/progress.md`
- `state/handoff.md`

## Acceptance criteria

- ...
- ...
- ...

## Stop conditions

Stop and report instead of implementing if:

- required project files are missing;
- current branch has unrelated changes that make the task unsafe;
- schema migration cannot be created safely;
- the requested implementation conflicts with `docs/architecture.md`;
- the task requires cloud/mobile/OCR/AI features not listed in Scope.

## Required checks

Run relevant checks:

- backend tests;
- frontend build;
- lint/format if configured;
- migration check if schema changes;
- relevant smoke scenario.

Report commands and results.

## PR summary format

Use this format in the final response:

## Summary
- ...

## Scope
- ...

## Data model / migrations
- ...

## User-visible changes
- ...

## Tests
- ...

## Risks / limitations
- ...

## Follow-up
- ...
```

---

## 17. Prompt template for docs-only PR

```markdown
# Task: Docs - <title>

## Context

You are updating documentation for `cosmetic-workshop-os`.

Read and follow:

- `AGENTS.md`
- `docs/AGENTS.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `state/progress.md`

## Goal

<Explain what documentation problem this PR solves.>

## Scope

Update only:

- ...

## Non-goals

Do not change:

- application code;
- tests;
- migrations;
- package files;
- unrelated docs.

## Documentation requirements

- Keep docs concise.
- Do not duplicate large sections from other docs.
- Link to the source document when possible.
- Keep instructions actionable.
- Do not include secrets.
- Keep user-facing docs simple and non-technical.

## Acceptance criteria

- ...
- ...

## Required checks

- Review links/filenames manually if possible.
- Ensure docs do not conflict with architecture and roadmap.
- Update `state/progress.md` and `state/handoff.md` if this changes project state.

## PR summary format

Use:

## Summary
## Scope
## Docs changed
## Tests / checks
## Risks / limitations
## Follow-up
```

---

## 18. Prompt template for code review

```markdown
# Task: Review PR - <PR title or number>

## Context

You are reviewing a PR for `cosmetic-workshop-os`.

Read and follow:

- `AGENTS.md`
- `code_review.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- relevant nested `AGENTS.md`

## Review focus

Check:

- roadmap fit;
- scope control;
- local-first constraints;
- user data directory safety;
- migrations;
- Decimal calculations;
- domain model correctness;
- transaction safety;
- import draft safety;
- audit logging;
- UI/UX human-readability;
- tests;
- docs/state updates;
- no cloud/mobile/OCR/AI leakage unless scoped.

## Output format

Return:

## Verdict
APPROVE / REQUEST_CHANGES / COMMENT_ONLY

## Blockers
- ...

## Important issues
- ...

## Minor issues
- ...

## Tests reviewed
- ...

## Architecture risks
- ...

## Recommended next action
- ...
```

---

## 19. Prompt anti-patterns

Avoid these prompt patterns.

### 19.1. Too broad

Bad:

```text
Build the whole MVP.
```

Better:

```text
Implement PR5 only: Ingredients and IngredientLots backend.
```

### 19.2. No non-goals

Bad:

```text
Add inventory.
```

Better:

```text
Add ingredient and lot backend only. Do not add frontend, alerts, purchases or production.
```

### 19.3. No tests

Bad:

```text
Implement and tell me when done.
```

Better:

```text
Add tests for success, validation errors, migration and audit logging. Run available checks and report results.
```

### 19.4. No architecture anchor

Bad:

```text
Make it work however you think is best.
```

Better:

```text
Follow docs/architecture.md. Preserve local-first architecture. Keep user data outside the app/repo.
```

### 19.5. Mixed scope

Bad:

```text
Add recipes, UI, production, PDF and import.
```

Better:

```text
Implement PR8 only: Recipe backend models.
```

---

## 20. Prompt quality checklist

Before sending any Codex prompt, check:

```text
[ ] Is the prompt in English?
[ ] Is there a clear PR title?
[ ] Does it reference required project files?
[ ] Is the Scope explicit?
[ ] Are Non-goals explicit?
[ ] Are architecture constraints included?
[ ] Are testing requirements included?
[ ] Are acceptance criteria verifiable?
[ ] Is documentation/state update required?
[ ] Is there a stop condition?
[ ] Is final PR summary format specified?
[ ] Does it avoid future scope leakage?
```

---

## 21. Project-specific prompt checklist

For `cosmetic-workshop-os`, also check:

```text
[ ] Does the prompt preserve local-first?
[ ] Does it keep user data outside repo/app?
[ ] Does it avoid cloud/mobile/OCR unless scoped?
[ ] Does it keep UI human-readable?
[ ] Does it require migrations for DB changes?
[ ] Does it require Decimal where calculations are involved?
[ ] Does it preserve RecipeTemplate/RecipeVersion/ClientRecipe separation?
[ ] Does it require StockMovement for inventory changes?
[ ] Does it require transaction safety for production?
[ ] Does it require ImportDraft for imports?
[ ] Does it require AuditLog for important actions?
[ ] Does it update state/progress.md and state/handoff.md?
```

---

## 22. Recommended first prompt for Codex Web

Use this as the first real implementation prompt after project documents are committed.

```markdown
# Task: PR0 - Project documentation contract

## Context

You are a senior full-stack product engineer working on `cosmetic-workshop-os`.

Treat this task as a scoped PR contract.

This is the first project setup PR. The goal is to create the documentation and project memory structure that future Codex tasks will follow.

Read the current repository state first. If files already exist, update them instead of duplicating them.

## Goal

Create the initial project documentation contract for a local-first web app for a cosmetic workshop. The documentation must help Codex implement the project safely through small PRs.

## Scope

Create or update only documentation and project-state files:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/product-spec.md`
- `docs/domain-model.md`
- `docs/ui-ux-contract.md`
- `docs/codex-prompting-rules.md`
- `state/progress.md`
- `state/handoff.md`
- `state/current-focus.md`
- `code_review.md`

## Non-goals

Do not implement:

- backend code;
- frontend code;
- database models;
- migrations;
- tests;
- package scripts;
- inventory;
- recipes;
- orders;
- production;
- cloud;
- mobile;
- OCR.

## Architecture constraints

Document these constraints clearly:

- MVP is local-first.
- User data must stay outside app/repo.
- The app must be usable by a non-technical user.
- RecipeTemplate, RecipeVersion and ClientRecipe are separate concepts.
- Inventory changes must go through StockMovement.
- Production must be transactional.
- Imports must go through ImportDraft and user confirmation.
- UI must be human-readable.
- Future cloud/mobile/OCR must not be implemented in MVP unless explicitly scoped.

## Documentation requirements

Keep `AGENTS.md` short. Put detailed product and architecture content into `docs/`.

Use `state/` for current progress and handoff.

## Acceptance criteria

- Required docs exist.
- `AGENTS.md` is short and points to the correct docs.
- `docs/architecture.md` describes local-first architecture.
- `docs/roadmap.md` describes PR-based implementation.
- `state/progress.md`, `state/handoff.md` and `state/current-focus.md` exist.
- No application code is changed.

## Required checks

- Verify file paths.
- Verify docs do not contradict each other.
- Report changed files.

## PR summary format

Use:

## Summary
## Scope
## Docs changed
## Tests / checks
## Risks / limitations
## Follow-up
```

---

## 23. Final rule

A good Codex prompt for this project must do three things:

```text
1. Tell Codex exactly what to build.
2. Tell Codex exactly what not to build.
3. Tell Codex how to prove it did the work safely.
```

If any of these three are missing, the prompt is not ready.
