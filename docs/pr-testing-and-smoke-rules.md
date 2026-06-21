# cosmetic-workshop-os - PR Testing and Smoke Rules

Document: `docs/pr-testing-and-smoke-rules.md`  
Project: `cosmetic-workshop-os`  
Human-facing name: `Мастерская косметолога`  
Purpose: define mandatory testing, validation and smoke-check rules after every PR.

---

## 1. Purpose

This document defines how every PR in `cosmetic-workshop-os` must be tested before it can be considered complete.

The goal is to make every PR:

- safe;
- small;
- verifiable;
- aligned with architecture;
- protected against regressions;
- clear for review;
- ready for Codex Web PR workflow.

Every Codex prompt must reference this document when implementation or review work is requested.

---

## 2. Core rule

Every PR must answer three questions:

```text
1. What changed?
2. How was it tested?
3. What user-critical flow could break, and was it smoke-checked?
```

A PR is not complete if it only says:

```text
Implemented feature.
```

A PR must say:

```text
Implemented feature.
Added/updated tests.
Ran checks.
Performed relevant smoke scenario or explained why smoke is not applicable.
Documented risks and follow-up.
```

---

## 3. Testing hierarchy

Testing is layered.

Not every PR needs every test type, but every PR must explicitly state which layers were run and which were not applicable.

```text
Static checks
→ Unit tests
→ Integration/API tests
→ Migration tests
→ Frontend build/UI smoke
→ Domain smoke
→ End-to-end/manual smoke
→ Packaging/local deployment smoke
→ Documentation/state checks
```

---

## 4. Mandatory checks for every PR

Every PR must include at least these checks.

### 4.1. Repository status check

Before making changes:

```bash
git status --short
git branch --show-current
```

Codex must avoid mixing unrelated work.

If unrelated changes exist, Codex must report them and avoid overwriting them.

---

### 4.2. Scope check

Before coding, Codex must confirm:

```text
This PR implements only the roadmap step listed in the prompt.
```

If Codex discovers related future work, it must add it to `Follow-up` instead of implementing it.

---

### 4.3. Build/test command discovery

Codex must inspect existing project files before assuming commands.

Look for:

```text
README.md
AGENTS.md
Makefile
package.json
pyproject.toml
pytest.ini
vite.config.ts
```

Use existing commands if present.

Do not invent commands without checking.

---

### 4.4. Documentation/state check

After meaningful work, update if applicable:

```text
state/progress.md
state/handoff.md
docs/roadmap.md if roadmap status changed
docs/api.md if API changed
docs/domain-model.md if data model changed
docs/architecture.md if architecture changed
docs/ui-ux-contract.md if UI contract changed
docs/testing.md or this file if testing strategy changed
```

If docs are not updated, the PR summary must say why.

---

## 5. Required PR summary testing block

Every Codex final response must contain a `Tests` section.

Required format:

```markdown
## Tests

Commands run:

- `<command>` - passed/failed
- `<command>` - passed/failed

Smoke checks:

- `<scenario>` - passed/failed/not applicable

Not run:

- `<check>` - reason
```

Codex must not claim that tests passed unless it actually ran them.

If tests cannot be run, Codex must clearly say why.

---

## 6. Standard check commands

The exact commands may change as the project evolves. Codex must prefer project-defined commands.

Recommended command aliases:

```bash
make test
make test-backend
make test-frontend
make build
make lint
make format-check
make smoke
make package-smoke
```

If `Makefile` does not exist yet, use direct commands discovered from backend/frontend configs.

Typical backend:

```bash
cd backend && pytest
```

Typical frontend:

```bash
cd frontend && npm run build
```

Typical migration check:

```bash
cd backend && alembic upgrade head
```

---

## 7. When smoke testing is required

Smoke testing is required when a PR changes a user-visible or workflow-critical path.

Smoke is mandatory for PRs that touch:

- app startup;
- local launcher;
- user data directory;
- database migrations;
- backup/restore;
- onboarding;
- dashboard;
- frontend routes;
- recipe calculation;
- inventory stock changes;
- orders;
- production readiness;
- production confirmation;
- import/export;
- packaging;
- update safety;
- PDF/report generation;
- error handling;
- anything that changes how a user completes a core task.

Smoke may be not applicable for:

- docs-only PRs;
- refactor with no runtime behavior change;
- test-only PRs;
- internal cleanup with no user/API change.

If smoke is not applicable, say so explicitly.

---

## 8. Smoke testing principles

Smoke tests are not full QA.

Smoke tests answer:

```text
Can the most important path still start and complete without obvious failure?
```

A smoke test should be:

- short;
- focused;
- repeatable;
- documented;
- matched to the PR scope;
- safe for local data;
- ideally run on demo/test data.

Smoke must not rely on real client data.

---

## 9. Smoke test levels

### 9.1. Level 0 - Docs smoke

For docs-only PRs.

Check:

```text
Docs exist.
Links/filenames are correct.
Docs do not contradict AGENTS.md, architecture or roadmap.
No secrets included.
No code changed.
```

Required PR summary:

```text
Smoke: Docs-only smoke passed.
```

---

### 9.2. Level 1 - Build smoke

For shell/frontend/backend setup PRs.

Check:

```text
Backend starts.
Health endpoint responds.
Frontend builds.
Frontend can reach backend health endpoint if app shell exists.
```

Example:

```bash
cd backend && pytest
cd frontend && npm run build
```

If manual startup is possible:

```text
Open app shell.
Dashboard placeholder renders.
Navigation renders.
No console-breaking error observed.
```

---

### 9.3. Level 2 - API/domain smoke

For backend feature PRs.

Check:

```text
Migration applies.
Core API endpoint works.
Domain service handles success case.
Domain service handles at least one failure case.
AuditLog created when required.
```

Example for ingredients:

```text
Create ingredient.
Create ingredient lot.
Reject negative quantity.
Reject remaining_quantity > initial_quantity.
Archive ingredient.
```

---

### 9.4. Level 3 - UI workflow smoke

For frontend feature PRs.

Check:

```text
Route opens.
Empty state is human-readable.
Form can be filled.
Validation appears for bad input.
Success state appears.
No raw stack trace or technical error appears to user.
```

Example for recipes UI:

```text
Open Recipes.
See empty state.
Create recipe.
Open recipe card.
Add ingredient row if supported.
Run calculation if supported.
See warning if density missing.
```

---

### 9.5. Level 4 - Cross-domain business smoke

For workflow PRs that connect multiple domains.

Check the full flow related to the PR.

Example for production:

```text
Create ingredient.
Create lot.
Create packaging.
Create recipe.
Create client.
Create order.
Check production readiness.
Confirm production.
Verify StockMovement created.
Verify lot/package stock reduced.
Verify Order status updated.
Verify ProductionBatch created.
```

This level is mandatory for production and import apply PRs.

---

### 9.6. Level 5 - Deployment/package smoke

For local runtime, launcher, packaging and update PRs.

Check:

```text
Package or launcher starts.
User data directory is created.
Database is created outside app/repo.
Migrations apply.
Browser opens.
Data persists after restart.
Backup works.
Port conflict is handled.
No terminal commands required for user mode if package scope includes user mode.
```

Mandatory for:

```text
D1 User data directory
D2 Local launcher
D3 macOS package MVP
D4 Update safety
D5 Remote install checklist
```

---

## 10. PR-specific testing rules

---

# 10.1. Documentation PRs

Applies to:

```text
PR0
docs-only tasks
roadmap/architecture updates
prompting rules
testing rules
```

Required checks:

```text
Docs added/updated.
No application code changed unless scoped.
No secrets.
Docs do not conflict with architecture/roadmap.
state/progress.md and state/handoff.md updated if project state changed.
```

Smoke:

```text
Docs smoke.
```

---

# 10.2. Backend foundation PRs

Applies to:

```text
PR1 backend shell
PR2 DB/settings/audit
PR3 Decimal helpers/enums
```

Required checks:

```text
Backend tests.
Health endpoint test.
Migration applies if schema changes.
Settings/audit tests if relevant.
```

Smoke:

```text
Backend starts.
Health endpoint responds.
```

---

# 10.3. User data directory and launcher PRs

Applies to:

```text
D1
D2
```

Required checks:

```text
Data directory creation.
Database path outside repo/app.
Permission error handling.
Launcher startup.
Port conflict handling.
Backend localhost only.
```

Smoke:

```text
Start app from launcher.
Verify user data directory created.
Verify database created in user data directory.
Verify browser opens.
Restart and verify data persists.
```

---

# 10.4. Backup/update PRs

Applies to:

```text
PR4
D4
PR23 if restore is implemented
```

Required checks:

```text
Backup file created.
Backup metadata recorded.
AuditLog written.
Backup stored in user data directory.
Migration creates backup before applying.
Failed migration does not destroy DB.
```

Smoke:

```text
Create backup from UI/API.
Verify file exists.
Restart app.
Verify data remains accessible.
```

For D4:

```text
Simulate migration from previous schema if possible.
Verify auto-backup before migration.
Verify UpdateLog written.
```

---

# 10.5. Inventory PRs

Applies to:

```text
PR5
PR6
PR7
```

Required checks:

```text
Create ingredient.
Create IngredientLot.
Reject invalid quantities.
Create packaging.
Create StockMovement.
Reject negative stock.
AuditLog for important changes.
Frontend build if UI changed.
```

Smoke for backend:

```text
Create ingredient.
Create lot.
Add inbound movement.
Try invalid outbound.
Verify remaining quantity.
```

Smoke for UI:

```text
Open stock page.
Create ingredient.
Add lot.
See stock summary.
Create packaging.
See movement history.
```

---

# 10.6. Recipe PRs

Applies to:

```text
PR8
PR9
PR10
```

Required checks:

```text
RecipeTemplate creation.
RecipeVersion creation.
RecipeIngredient creation.
Decimal percent storage.
Total percent validation.
Percent to grams calculation.
ml to grams with density.
Missing density warning.
Estimated cost if included.
Frontend build if UI changed.
```

Smoke:

```text
Create recipe.
Create version.
Add ingredients.
Calculate 100g.
Calculate 153g.
Verify warnings.
Open recipe UI if applicable.
```

---

# 10.7. Client and ClientRecipe PRs

Applies to:

```text
PR11
PR12
PR12b
```

Required checks:

```text
Create client.
Update client.
Archive client.
Sensitive notes not fully logged.
Create ClientRecipe from RecipeVersion.
Base RecipeVersion remains unchanged.
Create ClientWish.
Create ClientFeedback.
Link wish/feedback to client recipe/order if scoped.
```

Smoke:

```text
Create client.
Open client card.
Create individual recipe from base recipe.
Add wish.
Add feedback.
Verify client card tabs show data.
```

---

# 10.8. Order PRs

Applies to:

```text
PR13
PR14
```

Required checks:

```text
Create order with RecipeVersion.
Create order with ClientRecipe.
Reject order without recipe.
Status transition.
AuditLog for status change.
Frontend build if UI changed.
```

Smoke:

```text
Create client.
Create recipe/client recipe.
Create order.
Open order card.
Change status if scoped.
Verify order appears in client card.
```

---

# 10.9. Production PRs

Applies to:

```text
PR15
PR16
PR17
```

Required checks:

```text
Production readiness success.
Production readiness blocking issue.
FEFO lot selection.
Missing density warning.
Cost/tax/margin calculation.
Production transaction.
StockMovement creation.
ProductionBatch snapshot.
Order status update.
Cannot produce same order twice.
Rollback on failure.
Frontend build if UI changed.
```

Smoke:

```text
Create ingredient and lot.
Create packaging.
Create recipe.
Create client.
Create order.
Run readiness check.
Confirm production.
Verify lot remaining quantity decreased.
Verify packaging stock decreased.
Verify ProductionBatch exists.
Verify Order status is produced.
Verify AuditLog entries.
```

Production smoke is mandatory.

---

# 10.10. Alerts, purchases and dashboard PRs

Applies to:

```text
PR18
PR19
PR20
```

Required checks:

```text
Low stock alert.
Expiration alert.
Missing density alert.
Recipe total invalid alert.
PurchaseSuggestion from low stock.
PurchaseSuggestion from insufficient order materials.
Dashboard data aggregation.
Resolve/dismiss alerts.
```

Smoke:

```text
Create low stock condition.
Regenerate alerts.
See alert on dashboard.
Generate purchase suggestion.
Mark suggestion as purchased/dismissed if scoped.
```

---

# 10.11. Onboarding/help PRs

Applies to:

```text
O1
O2
UX1
O3
O4
O5
```

Required checks:

```text
First-run wizard state.
OnboardingState persistence.
Empty states render.
Contextual help visible.
Checklist step completion.
Demo data creation/removal.
Help pages load.
```

Smoke:

```text
Start with empty database.
See first-run wizard.
Complete wizard.
See dashboard checklist.
Open empty Recipes/Clients/Stock pages.
Verify next actions.
Create demo data if scoped.
Remove demo data if scoped.
Open help page.
```

---

# 10.12. Import/export PRs

Applies to:

```text
PR21
PR22
PR23
```

Required checks:

```text
Parse valid CSV.
Parse valid XLSX.
Create ImportSource.
Create ImportDraft.
Column mapping.
Validation error includes row/column/value/message.
No apply before confirmation.
Apply in transaction.
AuditLog on apply.
Export creates file.
CSV export valid.
Restore safe if implemented.
```

Smoke:

```text
Upload sample CSV.
Map columns.
Preview rows.
See validation error for bad row.
Apply valid import.
Verify created records.
Export records.
```

Import apply smoke is mandatory.

---

# 10.13. Reports/PDF PRs

Applies to:

```text
PR24
PR25
```

Required checks:

```text
Report endpoint returns expected data.
Date filters work if included.
PDF endpoint returns file.
PDF includes key text.
No broken response for empty data.
Frontend build if UI changed.
```

Smoke:

```text
Create sample data.
Open reports page.
Generate report.
Export PDF for recipe/order/production/purchase list if scoped.
Open/download PDF.
```

---

# 10.14. Packaging PRs

Applies to:

```text
D3
D5
```

Required checks:

```text
Package artifact created.
Package does not include user database.
Launcher works from package.
User data directory created.
Browser opens.
Restart persists data.
Remote install docs exist.
```

Smoke:

```text
Use clean test directory/profile.
Run packaged app.
Complete first run.
Create test client.
Close app.
Reopen app.
Verify test client still exists.
Create backup.
```

Packaging smoke is mandatory.

---

## 11. MVP smoke scenario

Before MVP release, run the full smoke scenario.

```text
1. Start app from clean local state.
2. Complete first-run wizard.
3. Create backup.
4. Create ingredient.
5. Create ingredient lot with expiration date.
6. Create packaging.
7. Create stock movement if needed.
8. Create base recipe.
9. Create recipe version.
10. Add recipe ingredients.
11. Calculate 100g.
12. Calculate 153g.
13. Verify density warning if density missing.
14. Create client.
15. Create individual client recipe.
16. Add client wish.
17. Add client feedback.
18. Create order.
19. Check production readiness.
20. Confirm production.
21. Verify ingredient lot stock decreased.
22. Verify packaging stock decreased.
23. Verify ProductionBatch created.
24. Verify Order status is produced.
25. Regenerate alerts.
26. Verify dashboard shows relevant state.
27. Generate purchase suggestion if applicable.
28. Import sample CSV through preview.
29. Export data.
30. Create PDF if PDF is implemented.
31. View AuditLog.
32. Close app.
33. Reopen app.
34. Verify data persists.
35. Create final backup.
```

This scenario must be documented in:

```text
docs/mvp-smoke-checklist.md
```

---

## 12. Smoke test reporting format

Every PR that includes smoke must report it like this:

```markdown
## Smoke

Scenario: <name>

Steps performed:
1. ...
2. ...
3. ...

Result:
- Passed / Failed / Partially passed

Evidence:
- endpoint response;
- UI observed;
- test output;
- created record;
- generated file;
- log entry.

Notes:
- ...
```

For Codex final response, a shorter version is acceptable:

```markdown
## Smoke
- Scenario: Create ingredient and lot
- Result: Passed
- Notes: Verified lot remaining quantity and AuditLog entry.
```

---

## 13. Handling failed tests or failed smoke

A PR with failed tests can still be useful, but it must not be presented as complete.

If tests fail, Codex must report:

```text
What failed
Why it failed if known
Whether the failure is related to this PR
What files/areas are affected
Recommended next step
```

Do not hide failures.

Do not say “all good” if checks failed.

---

## 14. When to stop instead of continuing

Codex must stop and report if:

```text
Required project files are missing.
The current branch has unrelated uncommitted changes.
The prompt conflicts with docs/architecture.md.
Migration cannot be created safely.
Tests cannot run due to missing dependencies.
The task requires cloud/mobile/OCR outside scope.
A smoke test would require real user data.
Packaging cannot be tested in the current environment.
```

Stopping and reporting is better than making unsafe changes.

---

## 15. Test data rules

Use fake/demo data only.

Do not use real client data in tests.

Recommended demo entities:

```text
Client: Demo Client
Ingredient: Demo Shea Butter
Ingredient: Demo Water
Packaging: Demo Jar 50 ml
Recipe: Demo Face Cream
Order: Demo Order
```

Demo/test data must be clearly marked as demo/test.

---

## 16. Data safety rules during tests

Tests must not write to real user data directories.

For tests use:

```text
temporary database
temporary user data directory
test fixtures
demo seed data
```

Never run destructive tests against a real user database.

---

## 17. Manual smoke vs automated smoke

Manual smoke is acceptable in early MVP.

But if a smoke scenario is repeated often, convert it into an automated test or script.

Priority for automation:

```text
1. backend domain tests;
2. API integration tests;
3. migration tests;
4. production flow smoke;
5. import apply smoke;
6. packaging smoke where feasible.
```

---

## 18. What must be added to Codex prompts

Every implementation prompt must include:

```markdown
## Testing requirements

Follow `docs/pr-testing-and-smoke-rules.md`.

Add or update tests for the PR scope.

Run relevant checks and report commands/results.

If this PR touches a user-visible or workflow-critical path, perform the relevant smoke scenario from `docs/pr-testing-and-smoke-rules.md`.

If smoke is not applicable, state why.
```

And:

```markdown
## Required checks

- backend tests if backend changed;
- frontend build if frontend changed;
- migration check if schema changed;
- smoke scenario if user workflow changed;
- docs/state consistency check.
```

---

## 19. Definition of done for every PR

A PR is done only when:

```text
[ ] Scope is respected.
[ ] Non-goals are not implemented.
[ ] Tests are added/updated where needed.
[ ] Relevant checks are run.
[ ] Smoke is performed or explicitly marked not applicable.
[ ] Migration exists if schema changed.
[ ] AuditLog is handled for important actions.
[ ] UI is human-readable if UI changed.
[ ] Docs/state are updated if needed.
[ ] Risks and follow-up are documented.
```

---

## 20. Final rule

For this project, “works on my machine” is not enough.

A PR must be:

```text
implemented
tested
smoke-checked when relevant
documented
safe for local user data
reviewable
```

If Codex cannot prove these points, the PR is not complete.
