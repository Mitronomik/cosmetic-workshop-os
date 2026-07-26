# Backend baseline failure triage — pre-release hardening gate

Document: `docs/backend-baseline-failure-triage.md`
Project: `cosmetic-workshop-os`
Gate: **Pre-release hardening — backend baseline correction gate**
Document state: **created** by the Block B closure / correction-gate task (no earlier active report existed)
Diagnostic outcome: **PATH A / COMPLETE**

This document is the only durable store for detailed backend baseline diagnostic evidence.
`state/` files carry the summary and the single active slice; they must not duplicate tracebacks or per-node tables.

---

## 1. Scope of this gate

This gate covers exactly these four node IDs and nothing else:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues
app/tests/test_purchase_suggestions.py::test_manual_api_smoke
```

This gate does not authorize any correction beyond the one active slice named in `state/current-focus.md`.
No correction is implemented by the pull request that created this document.

---

## 2. Evidence provenance

| Fact | Provenance |
|---|---|
| PR #141 merged; final reviewed head `d0cde127355b146f101ddf3769d76d0226c71ec0`; merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa`; merged `2026-07-26` | VERIFIED FROM REPOSITORY / GITHUB |
| Complete backend baseline `496 collected / 492 passed / 4 failed / 0 skipped` | EXECUTED IN THIS TASK |
| Per-node results, tracebacks, file/line, and surrounding-file results in this document | EXECUTED IN THIS TASK |
| Production/test source relationships quoted in this document | VERIFIED FROM REPOSITORY / GITHUB |
| Dashboard/Onboarding focused suite `42/42` for the final reviewed head | SUPPLIED TASK BASELINE |
| Frontend production build `PASS` | SUPPLIED TASK BASELINE |
| PR #141 backend branch-only failure delta `0` | SUPPLIED TASK BASELINE |
| Product-owner exact-head browser/keyboard/responsive/network smoke `PASS` | SUPPLIED TASK BASELINE — product-owner-verified exact-head smoke of PR #141 on 2026-07-26; not re-run in this documentation task |

The earlier dated record reports `33/33` for an intermediate branch state. The accepted PR #141 record reports `42/42` for the final reviewed head. Neither result was re-run in this documentation task, and no cause for the difference is claimed here.

---

## 3. Diagnostic environment

EXECUTED IN THIS TASK.

| Item | Value |
|---|---|
| Interpreter discovery | `/Users/volkilli/.local/bin/python3.12` → `Python 3.12.13`; `/Users/volkilli/.pyenv/shims/python3` → `Python 3.12.10` |
| Selected executable | `${TMPDIR:-/tmp}/cosmetic-workshop-os-diagnostic-venv/bin/python` (created from `python3.12`) |
| Python version in venv | `3.12.13` |
| Dependency install | `python -m pip install -e "backend[test]"` — succeeded |
| Working directory for the baseline | `/Users/volkilli/Projects/cosmetic-workshop-os/backend` |
| pytest version | `8.4.2` (plugins: `anyio-4.14.2`) |
| rootdir | `/Users/volkilli/Projects/cosmetic-workshop-os/backend` |
| configfile | `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths = ["app/tests"]`, `pythonpath = ["."]`) |
| Environment location | outside the repository; removed and verified absent after diagnostics |

The repository-root `pytest.ini` (`testpaths = backend/app/tests launcher/tests`) is a **different** configuration and was deliberately not used, because the accepted baseline corresponds to running from `backend/`. `make test`, `make test-backend`, and root-level pytest were not substituted for the baseline comparison.

---

## 4. Complete baseline result

Command, from `backend/`:

```text
${TMPDIR:-/tmp}/cosmetic-workshop-os-diagnostic-venv/bin/python -m pytest
```

Result: **496 collected, 492 passed, 4 failed, 0 skipped** in 23.96s.

Drift from the supplied `496 / 492 / 4 / 0`: **none**. The failing node IDs are exactly the four named nodes. No additional failures were observed, so no additional finding is carried into this gate.

Surrounding-file results:

| File | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| `app/tests/test_backups_api.py` | 9 | 8 | 1 | 0 |
| `app/tests/test_exports_api.py` | 11 | 10 | 1 | 0 |
| `app/tests/test_imports_api.py` | 7 | 6 | 1 | 0 |
| `app/tests/test_purchase_suggestions.py` | 11 | 10 | 1 | 0 |

In every file the only failure is the named node. Each named node was executed twice in isolation; both runs produced byte-identical failures. All four are **deterministic**.

---

## 5. Node 1 — backups reason sanitization

1. **Node ID** — `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
2. **Asserted expected behavior** — `POST /api/backups` with `reason="before/update ../unsafe"` must produce a backup filename containing the substring `before_update_unsafe`; a whitespace-only reason must default to `manual`; the file must land in `<tmp>/backups`.
3. **Observed behavior** — Both requests returned `201`. The whitespace-only default and the parent-directory assertions passed. The generated name was `20260726T204005961044Z-cosmetic_workshop-before_update____unsafe.sqlite` — four consecutive underscores where the test expects one.
4. **Exact failure** — `AssertionError: assert 'before_update_unsafe' in '20260726T204005961044Z-cosmetic_workshop-before_update____unsafe.sqlite'` at `backend/app/tests/test_backups_api.py:157`.
5. **Setup versus call** — **Call**, not setup. The API was reached, the backup file was created on disk, and the failure is a post-response assertion on the resulting filename.
6. **Deterministic / intermittent** — **Deterministic** across two isolated runs and the full-suite run.
7. **Surrounding test file** — `1 failed, 8 passed`.
8. **Classification** — **PRODUCT DEFECT**
9. **Evidence supporting classification**
   - `backend/app/services/backup.py:47` replaces every disallowed character with one `_` and never collapses runs, so `"/"`, `" "`, `"."`, `"."`, `"/"` become five separate underscores (four remain after `strip("_")` interacts with the surrounding text).
   - The same intended collapsed contract is asserted independently in two separate test files (this node and node 2), i.e. the contract was authored twice against two independent implementations.
   - The repository's own newer sanitizer `backend/app/services/report_documents.py:174 sanitize_reason` *does* normalize runs (`re.sub(r"[.]{2,}", ".", cleaned).strip(" ._-/\\")`), showing the project's established sanitization direction is toward normalization rather than 1:1 substitution.
   - The reason is user-visible: `backend/app/services/backup.py:144-149` parses the reason back out of the filename stem for `BackupFileMetadata`, which feeds the `/backups` listing. `AGENTS.md` §7.3/§7.5 require human-readable, non-technical user-facing text.
   - **Counter-evidence recorded for fairness:** no document explicitly mandates run-collapsing. `docs/backup-and-restore.md:24` only states that filenames include a timestamp, the database stem, and a reason such as `before_migration`, plus a non-overwriting suffix. The correction slice must confirm the intended normalization with the product owner before changing behavior.
10. **Relevant paths** — test `backend/app/tests/test_backups_api.py:157`; production `backend/app/services/backup.py:47` (`_safe_filename_part`), `:53` (`_backup_filename`), `:65` (`_unique_backup_path`), `:144` (metadata reason parsing); API `backend/app/api/backups.py`.
11. **Severity** — **LOW**
12. **User-visible or data-integrity impact** — User-visible only, and cosmetic: the reason shown in the `/backups` list renders with underscore runs. **No data-integrity impact.** Safety properties verified intact in this task: `..` and `/` are neutralized so no path traversal is possible; `_unique_backup_path` increments a numeric suffix until a free name is found so no backup is overwritten; the charset is restricted to alphanumerics, `-`, and `_`; the source database is never modified.
13. **Likely correction surface** — `backend/app/services/backup.py::_safe_filename_part` (shared with node 2 — see §9).
14. **Schema / migration requirement** — None.
15. **Shared root cause or duplicated contract** — **Duplicated implementation** shared with node 2. See §9.
16. **Smallest safe slice** — Slice `R1` in §10.
17. **Required tests** — The two existing baseline nodes must pass unmodified in intent; add coverage for reason strings that are entirely unsafe, empty after sanitization (fallback default), and containing a literal `-`.
18. **Required smoke** — Backend suite only. `/backups` and `/exports` list rendering check at desktop width to confirm the reason label reads correctly. No browser smoke beyond that is required for a backend-only filename change.

---

## 6. Node 2 — exports reason sanitization

1. **Node ID** — `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
2. **Asserted expected behavior** — `POST /api/exports` with `reason="before/import ../unsafe"` must produce an export filename containing `before_import_unsafe`; a whitespace-only reason must default to `manual` in both the filename and the manifest; the file must land in `<tmp>/exports`.
3. **Observed behavior** — Both requests returned `201`. The whitespace-only default, the manifest reason, and the parent-directory assertions passed. The generated name was `20260726T204020135395Z-cosmetic_workshop-export-before_import____unsafe.json`.
4. **Exact failure** — `AssertionError: assert 'before_import_unsafe' in '20260726T204020135395Z-cosmetic_workshop-export-before_import____unsafe.json'` at `backend/app/tests/test_exports_api.py:279`.
5. **Setup versus call** — **Call**, not setup. The API was reached and the export JSON was written and successfully re-read before the failing assertion.
6. **Deterministic / intermittent** — **Deterministic** across two isolated runs and the full-suite run.
7. **Surrounding test file** — `1 failed, 10 passed`.
8. **Classification** — **PRODUCT DEFECT**
9. **Evidence supporting classification** — Identical to node 1. `backend/app/services/export.py:84` is character-for-character the same implementation as `backend/app/services/backup.py:47`, differing only in the fallback default returned when the sanitized string is empty (`"manual"` versus `"backup"`). The same counter-evidence in node 1 §9 applies: `docs/export.md` documents the manifest `reason` field but not a filename run-collapsing rule.
10. **Relevant paths** — test `backend/app/tests/test_exports_api.py:279`; production `backend/app/services/export.py:78` (`normalize_export_reason`), `:84` (`_safe_filename_part`), `:116` (`_export_filename`), `:123` (`_unique_export_path`); API `backend/app/api/exports.py`.
11. **Severity** — **LOW**
12. **User-visible or data-integrity impact** — User-visible only, and cosmetic. **No data-integrity impact.** Traversal neutralization, non-overwriting unique naming, restricted charset, backend-owned generation, and human-readable JSON output were all verified intact in this task.
13. **Likely correction surface** — `backend/app/services/export.py::_safe_filename_part` (shared with node 1 — see §9).
14. **Schema / migration requirement** — None.
15. **Shared root cause or duplicated contract** — **Duplicated implementation** shared with node 1. See §9.
16. **Smallest safe slice** — Slice `R1` in §10.
17. **Required tests** — As node 1, field 17.
18. **Required smoke** — As node 1, field 18.

---

## 7. Node 3 — import draft issue count

1. **Node ID** — `app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues`
2. **Asserted expected behavior** — Uploading `quantity,unit,purchase_date` / `not-number,kg,05.07.2026` for target `ingredient_lots` must create a draft with `error_count >= 4`, global issue codes including `missing_required_column`, and row-0 issue codes including all of `invalid_decimal`, `invalid_unit`, `invalid_date`.
3. **Observed behavior** — The draft was created with `201`. `error_count` is `3`, `warning_count` is `1`. The actual issue set is: global `missing_required_column` (`ingredient_name`) — error; row 2 `invalid_decimal` (`quantity`) — error; row 2 `invalid_unit` (`unit`) — error; row 2 `date_format_normalized` (`purchase_date`, "«05.07.2026» будет прочитана как 2026-07-05") — **warning**. Draft readiness is `blocked`, `can_apply: false`, `valid_row_count: 0`.
4. **Exact failure** — `assert 3 >= 4` at `backend/app/tests/test_imports_api.py:107`.
5. **Setup versus call** — **Call**, not setup. The upload endpoint was reached and returned `201`; the failure is an assertion on the returned draft summary.
6. **Deterministic / intermittent** — **Deterministic** across two isolated runs and the full-suite run.
7. **Surrounding test file** — `1 failed, 6 passed`.
8. **Classification** — **TEST DEFECT**
9. **Evidence supporting classification**
   - `docs/import-format.md:152` documents the current contract explicitly: *"Dates should use ISO `YYYY-MM-DD`. Deterministic Russian `DD.MM.YYYY` dates are normalized to ISO with `date_format_normalized`; ambiguous slash dates are not accepted."* `05.07.2026` is exactly a deterministic Russian `DD.MM.YYYY` date, so a `date_format_normalized` **warning** is the documented correct outcome and `invalid_date` would be wrong.
   - The sibling test `backend/app/tests/test_import_parsing.py:144` asserts that `date_format_normalized` is emitted, and it **passes**. The sibling test `backend/app/tests/test_import_parsing.py:57-60` exercises `invalid_date` using the genuinely unparseable value `not-date`, and it also **passes**. The two behaviors are already correctly covered elsewhere.
   - The failing node therefore encodes a superseded pre-normalization contract in two places at once: the `>= 4` count at line 107 and the `invalid_date` membership assertion at line 110. Line 110 would also fail if line 107 were relaxed.
   - The absence of a row-level `missing_required_value` for `ingredient_name` is correct and not a defect: `backend/app/services/imports.py:385-387` raises that row issue only when the required column exists but the cell is blank. When the column is absent entirely, the global `missing_required_column` error already covers it, so the design avoids double-counting one fault.
   - The documented import flow is intact and was verified in this task: upload → draft → validation → preview → confirmation → apply. Missing required columns and row issues **do** coexist in one draft, the draft is `blocked`, `can_apply` is `false`, and nothing was written to production tables.
10. **Relevant paths** — test `backend/app/tests/test_imports_api.py:107` and `:110`; production `backend/app/services/imports.py:40` (`ingredient_lots` required columns), `:170-177` (`_normalize_date_value`, `date_format_normalized` / `invalid_date`), `:371-373` (`missing_required_column`), `:385-387` (`missing_required_value`), `:180-197` (`_readiness`), `:200` (`_issue_counts`); contract `docs/import-format.md:79`, `:115-119`, `:152-154`.
11. **Severity** — **MEDIUM**
12. **User-visible or data-integrity impact** — **None.** The import contract behaves exactly as documented, drafts remain blocked, and no production data is mutated. The impact is on the engineering baseline: the stale assertions keep the backend suite red and, if "corrected" in the wrong direction, would weaken the documented `DD.MM.YYYY` normalization and reintroduce a rejected-date regression for real Russian-formatted files.
13. **Likely correction surface** — `backend/app/tests/test_imports_api.py` lines 107 and 110 only. No production change is indicated.
14. **Schema / migration requirement** — None.
15. **Shared root cause or duplicated contract** — **None.** Direct shared cause with nodes 1, 2, and 4 is not proven; imports remain a separate slice.
16. **Smallest safe slice** — Slice `R2` in §10.
17. **Required tests** — Realign the two assertions to the documented contract (`error_count == 3`, `warning_count == 1`, row codes `{invalid_decimal, invalid_unit, date_format_normalized}`) and assert `apply_readiness.can_apply is false`. Do not skip, xfail, delete, rename, or weaken the test; the corrected test must be strictly more specific than `>= 4`.
18. **Required smoke** — Backend suite only. No browser smoke required for a test-only correction.

---

## 8. Node 4 — purchase suggestions manual API smoke

1. **Node ID** — `app/tests/test_purchase_suggestions.py::test_manual_api_smoke`
2. **Asserted expected behavior** — With an ingredient below its minimum stock, `POST /api/purchase-suggestions/regenerate` creates at least one suggestion; `GET /api/purchase-suggestions` lists it; `POST /api/purchase-suggestions/{id}/mark-purchased` moves it to `purchased`, removes it from the open list, keeps it visible under `status=all`, and creates **no** stock movements, packaging stock movements, or ingredient lots.
3. **Observed behavior** — None of the above was reached. The test aborted on its first statement, inside the shared seeding helper, before the FastAPI `TestClient` was constructed and before any API call.
4. **Exact failure** — `app.domain.errors.DomainValidationError: Количество движения должно быть больше нуля.` raised at `backend/app/domain/stock_movements.py:86`, via `backend/app/domain/stock_movements.py:179` ← `backend/app/tests/test_production_confirmation.py:58` (`seed_ready`) ← `backend/app/tests/test_purchase_suggestions.py:214`.
5. **Setup versus call** — **Setup / arrange.** In pytest phase terms the exception occurs during the `call` phase because the seeding runs in the test body rather than in a fixture, but functionally it is test arrangement: `seed_ready(c, lot_qty="0", ...)` fails before the API surface is exercised. **The API was never reached.**
6. **Deterministic / intermittent** — **Deterministic** across two isolated runs and the full-suite run.
7. **Surrounding test file** — `1 failed, 10 passed`.
8. **Classification** — **TEST DEFECT**
9. **Evidence supporting classification**
   - The domain rule is correct and intentional. `backend/app/domain/stock_movements.py:84-93` rejects a zero-quantity stock movement with the actionable Russian message "Количество движения должно быть больше нуля." A receipt movement of `0` carries no inventory meaning, and `AGENTS.md` §5.9 requires every inventory change to be a meaningful movement. **Domain validation is correctly rejecting the test's data.**
   - The test's seeding strategy is the outlier. Across all 45 `seed_ready(...)` call sites in `backend/app/tests/`, `backend/app/tests/test_purchase_suggestions.py:214` is the **only** one that passes `lot_qty="0"`. Every other low-stock scenario seeds a positive quantity and raises the minimum-stock threshold instead — for example `test_low_stock_and_order_shortages_generate_suggestions_and_quantities` at `:79` uses `lot_qty="10"` with `ingredient_min="100"`, and passes.
   - The correct in-repo idiom therefore already exists and is proven by passing sibling tests; only this node uses an invalid seed.
   - **The test is not genuinely manual.** Despite the `manual` in its name it carries no manual-only marker and no skip beyond the `TestClient is None` availability guard, so pytest collects and runs it automatically. Automatic collection is intended; the collection itself is not the defect.
   - **Equivalent automated coverage is partial, not complete.** `test_low_stock_and_order_shortages_generate_suggestions_and_quantities` (`:77`) covers suggestion generation and quantities, and `test_regeneration_and_mark_purchased_are_read_only_for_business_tables` (`:187`) covers regenerate plus `mark_purchased` read-only semantics — but both operate at the service/repository layer. This node is the only coverage of the `/api/purchase-suggestions` **HTTP** surface for regenerate, list, status filtering, and mark-purchased. While it fails at seeding, that API-layer coverage does not execute at all.
10. **Relevant paths** — test `backend/app/tests/test_purchase_suggestions.py:211-232`; shared helper `backend/app/tests/test_production_confirmation.py:50-62` (`seed_ready`); production `backend/app/domain/stock_movements.py:70-93` (`parse_stock_quantity`), `:179` (`StockMovementDraft.create`); API `backend/app/api/purchase_suggestions.py`; service `backend/app/services/purchase_suggestions.py`.
11. **Severity** — **MEDIUM**
12. **User-visible or data-integrity impact** — **None.** No product behavior is wrong; the domain correctly refuses an invalid movement. The impact is lost test coverage: the purchase-suggestions HTTP API has no executing end-to-end assertion, including the assertion that `mark-purchased` creates no stock movements, no packaging movements, and no lots. That read-only guarantee is a genuine data-safety property currently unverified at the API layer.
13. **Likely correction surface** — `backend/app/tests/test_purchase_suggestions.py:214` seeding only. No production change is indicated.
14. **Schema / migration requirement** — None.
15. **Shared root cause or duplicated contract** — **None.** No direct shared cause with nodes 1, 2, or 3 is proven; purchase suggestions remain a separate slice.
16. **Smallest safe slice** — Slice `R3` in §10.
17. **Required tests** — Re-seed with a valid positive `lot_qty` and a higher `minimum_stock` so the below-minimum condition still holds, matching the proven idiom at `:79`. All existing assertions — including the three no-mutation assertions — must be preserved and must execute. Do not delete, rename, skip, `xfail`, or weaken the test.
18. **Required smoke** — Backend suite only. No browser smoke required for a test-only correction.

---

## 9. Grouping evidence — why nodes 1 and 2 may be corrected together

The combined-slice condition satisfied is **duplicated implementation**, not shared root cause:

- **Two modules independently implement the same contract.** `backend/app/services/backup.py:47` and `backend/app/services/export.py:84` each define a private `_safe_filename_part`. Neither imports the other; a repository-wide search for `_safe_filename_part` returns only these two definitions and their local call sites. The two bodies are identical except for the empty-result fallback (`"backup"` versus `"manual"`).
- **Both exhibit the same proven defect.** Both replace each disallowed character with one underscore and never collapse runs, and both failing assertions differ only in the literal reason string.
- **Extracting one shared helper removes the duplication safely.** The only behavioral difference is the fallback default, which a single parameter preserves exactly.
- **Changes remain limited to those modules and their direct tests.** `backend/app/api/backups.py` and `backend/app/api/exports.py` call the services, not the helper, so no API or schema surface moves.

Nodes 3 and 4 are **excluded** from this grouping. They share no helper, no contract, and no cause with nodes 1 and 2 or with each other, and each is a test-only correction in a different subsystem. They remain separate slices.

A third sanitizer, `backend/app/services/report_documents.py:174 sanitize_reason`, implements a **different** contract — it permits spaces and dots, collapses only repeated dots, strips a wider separator set, and truncates to 80 characters. It is **not** part of this grouping and must not be unified into the shared helper.

---

## 10. Proposed bounded correction slices

### Slice R1 — Backups and Exports filename reason normalization

- **Title** — `R1 — Shared safe filename part for backup and export reasons`
- **Scope** — Extract one shared filename-part sanitizer used by `backend/app/services/backup.py` and `backend/app/services/export.py`, with a caller-supplied fallback default; collapse consecutive replaced characters into a single underscore; keep the two existing baseline test intents unmodified.
- **Non-goals** — No change to `report_documents.sanitize_reason`; no change to timestamp format, directory resolution, uniqueness/suffix logic, manifest content, export payload schema, or the backup copy mechanism; no change to nodes 3 and 4; no API, schema, or migration change; no dependency change.
- **Architecture constraints** — User data stays outside code and package. Filenames stay restricted to alphanumerics, `-`, and `_`. Path traversal stays impossible. Existing backups and exports are never overwritten and never rewritten. Artifact generation stays backend-owned. Artifacts stay human-readable. The backup filename→metadata round trip at `backend/app/services/backup.py:144-149` must not regress; note that `-` is currently a permitted character in the reason part while the parser splits on `-`, so the slice must confirm the parser still resolves the reason correctly for every reason it can now produce.
- **Backend requirements** — One shared helper; both services call it; the two fallback defaults are preserved through a parameter.
- **Frontend requirements** — None.
- **Data model / migrations** — None.
- **Tests** — The two baseline nodes pass without weakening their assertions; new cases for a fully unsafe reason, a reason that sanitizes to empty (fallback), a reason containing a literal `-`, and a filename→metadata round trip.
- **Smoke** — Backend suite; visual check that `/backups` and `/exports` render the reason label correctly at desktop width.
- **Acceptance criteria** — Backend baseline improves from `4 failed` to `2 failed` with no new failure; no production behavior other than the reason segment of generated filenames changes; all safety properties in §5 field 12 and §6 field 12 remain verified.

### Slice R2 — Import draft issue-count contract alignment (test-only)

- **Title** — `R2 — Align import draft baseline test with the documented date-normalization contract`
- **Scope** — `backend/app/tests/test_imports_api.py` lines 107 and 110 only.
- **Non-goals** — No production change; no change to `docs/import-format.md`; no change to nodes 1, 2, and 4.
- **Architecture constraints** — Direct Apply stays prohibited; row issues are never discarded; validation is never weakened; no production data is mutated.
- **Backend requirements** — None.
- **Frontend requirements** — None.
- **Data model / migrations** — None.
- **Tests** — As §7 field 17.
- **Smoke** — Backend suite only.
- **Acceptance criteria** — The node passes with assertions strictly more specific than `>= 4`, and the documented `DD.MM.YYYY` → `date_format_normalized` behavior is asserted rather than removed.

### Slice R3 — Purchase suggestions API smoke seeding repair (test-only)

- **Title** — `R3 — Repair purchase-suggestions API smoke seeding`
- **Scope** — The seeding call at `backend/app/tests/test_purchase_suggestions.py:214` only.
- **Non-goals** — No production change; no change to `seed_ready`'s signature or to any other caller; no change to the zero-quantity domain rule; no change to nodes 1, 2, and 3.
- **Architecture constraints** — The zero-quantity rejection rule stays intact. Stock changes stay routed through `StockMovement`. The test's no-mutation assertions stay intact.
- **Backend requirements** — None.
- **Frontend requirements** — None.
- **Data model / migrations** — None.
- **Tests** — As §8 field 17.
- **Smoke** — Backend suite only.
- **Acceptance criteria** — The node reaches and exercises the `/api/purchase-suggestions` HTTP surface, and all three no-mutation assertions execute and pass.

---

## 11. Selection

**Primary selection priority applied** (from most to least important: data loss or unsafe mutation → backup/recovery reliability → import integrity → broken user-visible API → test defect hiding coverage → manual-smoke collection hygiene):

- No node reaches priority 1. No data loss or unsafe mutation was found; all four subsystems were verified to leave production data untouched.
- No node reaches priority 2. Backup and recovery **reliability** is not impaired: backups are created, never overwritten, never traversable, and the source database is never modified. Severity was deliberately not inflated to place R1 here.
- No node reaches priority 3. Import **integrity** is intact and documented behavior is correct; R2 is a stale test, not an integrity failure.
- **R1 reaches priority 4** — broken user-visible API output. The generated filename, and the reason parsed back out of it for the `/backups` listing, is user-visible and does not match the intended readable contract.
- **R2 and R3 reach priority 5** — test defects. R2 blocks a clean baseline; R3 additionally leaves the purchase-suggestions HTTP surface with no executing coverage.
- No node is priority 6. Node 4 is automatically collected and intended to be; its name is misleading but collection hygiene is not the defect.

**Tie-breaker** — R1 stands alone at priority 4, so no tie-breaker was needed to select it. For the deferred follow-up ordering, R2 and R3 tie at priority 5 and were separated on the second criterion, greater direct user/data impact: R3 leaves a real data-safety guarantee (mark-purchased creates no movements or lots) unverified at the API layer, whereas R2 only blocks the baseline. Follow-up order is therefore **R3 before R2**.

**Active slice: R1.** R2 and R3 are proposed and evidenced but **not activated**. Exactly one slice is active.

---

## 12. Adjacent finding recorded but not part of this gate

**Potential backup consistency finding — not classified or activated.**

The current backup helper copies the SQLite database file through `shutil.copy2`, and the startup before-migration path uses the same helper. This raises a transaction-consistency question when the database may be live or use auxiliary SQLite files. Some existing tests pass ordinary bytes rather than a real SQLite database to the helper, so a future diagnostic must inspect those fixtures.

This task records only the need for a separate evidence-based diagnostic.

Do not classify the behavior as unsafe and do not prescribe a correction design here.

This finding is **not** one of the four current failures, is **not** diagnosed, scoped, or activated here, and is tracked as a `needs evidence` row in `state/change-requests.md`.
