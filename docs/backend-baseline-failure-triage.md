# Backend baseline failure triage — pre-release hardening gate

Document: `docs/backend-baseline-failure-triage.md`
Project: `cosmetic-workshop-os`
Gate: **Pre-release hardening — backend baseline correction gate**
Document state: **created**, then **fully replaced** in place after review of the same active gate. No duplicate heading or duplicate node record was appended.
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
The pull request that originally carried this document implemented no correction. Corrections are implemented by their own focused slice pull requests, and their lifecycle is tracked in §10 and §13.

---

## 2. Evidence provenance

| Fact | Provenance |
|---|---|
| PR #141 merged; final reviewed head `d0cde127355b146f101ddf3769d76d0226c71ec0`; merge commit `70cb6f01bf23a3d09dd2e5caa320424d3b1a2ffa`; merged `2026-07-26` | VERIFIED FROM REPOSITORY / GITHUB |
| Complete backend baseline `496 collected / 492 passed / 4 failed / 0 skipped` | EXECUTED IN THIS TASK |
| Per-node results, tracebacks, file/line, and surrounding-file results in this document | EXECUTED IN THIS TASK |
| Production/test source relationships quoted in this document | VERIFIED FROM REPOSITORY / GITHUB |
| Absence of a documented filename normalization rule for runs of unsafe characters | VERIFIED FROM REPOSITORY / GITHUB |
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

The diagnostic environment itself was fully available and every required diagnostic command completed. Where a node below is marked `INCONCLUSIVE`, the missing input is a **product-contract decision**, not missing diagnostic evidence, and no further test execution would resolve it.

---

## 5. Node 1 — backups reason sanitization

1. **Node ID** — `app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters`
2. **Asserted expected behavior** — `POST /api/backups` with `reason="before/update ../unsafe"` must produce a backup filename containing the substring `before_update_unsafe`; a whitespace-only reason must default to `manual`; the file must land in `<tmp>/backups`.
3. **Observed behavior** — Both requests returned `201`. The whitespace-only default and the parent-directory assertions passed. The generated name was `20260726T204005961044Z-cosmetic_workshop-before_update____unsafe.sqlite`, which contains four consecutive underscores where the test's substring has one.
4. **Exact failure** — `AssertionError: assert 'before_update_unsafe' in '20260726T204005961044Z-cosmetic_workshop-before_update____unsafe.sqlite'` at `backend/app/tests/test_backups_api.py:157`.
5. **Setup versus call** — **Call**, not setup. The API was reached, the backup file was created on disk, and the failure is a post-response assertion on the resulting filename.
6. **Deterministic / intermittent** — **Deterministic** across two isolated runs and the full-suite run.
7. **Surrounding test file** — `1 failed, 8 passed`.
8. **Classification** — **INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED**
9. **Evidence supporting classification**
   - The mismatch is factual and reproducible. `backend/app/services/backup.py:47` maps each character that is not alphanumeric, `-`, or `_` to a single `_`, one output character per input character. For the input `"before/update ../unsafe"` the five characters `/`, ` `, `.`, `.`, `/` therefore produce five underscores, of which four appear between `update` and `unsafe`. The test's substring `before_update_unsafe` requires a run of replaced characters to collapse to one underscore.
   - **No product documentation defines which behavior is required.** `docs/backup-and-restore.md:24` states only that backup filenames include a UTC timestamp, the database filename stem, and a reason such as `before_migration`, plus a non-overwriting suffix when a name already exists. It does not specify collapsing, and it does not specify 1:1 substitution. `docs/export.md` likewise documents the manifest `reason` field but no filename normalization rule. `docs/product-spec.md`, `docs/architecture.md`, and `docs/api.md` contain no filename normalization contract either.
   - Evidence exists on both sides and neither is decisive. Two independently written tests assert the collapsed form, which indicates an intent that was written twice. The repository also contains a third, deliberately different sanitizer, `backend/app/services/report_documents.py:174 sanitize_reason`, which permits spaces and dots, collapses only repeated dots, strips a wider separator set, and truncates to 80 characters — so the repository does not have one settled normalization style to generalize from.
   - **This document does not state that the production behavior is wrong.** Determining which of the two behaviors is correct requires a product decision, recorded as a `needs product decision` change request. Until that decision exists, no root cause, no severity, and no correction surface can be asserted for this node.
   - Recorded as observed facts, independent of the undecided contract: `..` and `/` are mapped to `_` so the generated name contains no path separator and no parent-directory reference; `_unique_backup_path` (`backend/app/services/backup.py:65`) increments a numeric suffix until a free name is found, so an existing backup is not overwritten; the produced charset is restricted to alphanumerics, `-`, and `_`; the source database is not modified by the copy.
   - A related undecided point sits in the same contract. `backend/app/services/backup.py:144-149` recovers the reason for `BackupFileMetadata` by splitting the filename stem on `-` and taking the last segment (or the second-to-last when the last is a numeric uniqueness suffix), while `-` is itself a permitted character inside the sanitized reason. A reason containing a literal hyphen therefore round-trips differently from one that does not. Whether hyphens should remain permitted, and whether the displayed reason should be derived from the filename at all rather than stored independently, is part of the same undecided contract.
10. **Relevant paths** — test `backend/app/tests/test_backups_api.py:157`; production `backend/app/services/backup.py:47` (`_safe_filename_part`), `:53` (`_backup_filename`), `:65` (`_unique_backup_path`), `:144-149` (metadata reason parsing); API `backend/app/api/backups.py`; documentation `docs/backup-and-restore.md:24`.
11. **Severity** — `NOT DETERMINED FROM CURRENT EVIDENCE`
12. **User-visible or data-integrity impact** — `NOT DETERMINED FROM CURRENT EVIDENCE`
13. **Likely correction surface** — `NOT DETERMINED FROM CURRENT EVIDENCE`
14. **Schema / migration requirement** — `NOT DETERMINED FROM CURRENT EVIDENCE`
15. **Shared root cause or duplicated contract** — `NOT DETERMINED FROM CURRENT EVIDENCE`. The structural duplication between this node and node 2 is recorded as a fact in §9, but no shared *defect* can be asserted while the contract is undecided.
16. **Smallest safe slice** — `NOT DETERMINED FROM CURRENT EVIDENCE`
17. **Required tests** — `NOT DETERMINED FROM CURRENT EVIDENCE`
18. **Required smoke** — `NOT DETERMINED FROM CURRENT EVIDENCE`

---

## 6. Node 2 — exports reason sanitization

1. **Node ID** — `app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters`
2. **Asserted expected behavior** — `POST /api/exports` with `reason="before/import ../unsafe"` must produce an export filename containing `before_import_unsafe`; a whitespace-only reason must default to `manual` in both the filename and the manifest; the file must land in `<tmp>/exports`.
3. **Observed behavior** — Both requests returned `201`. The whitespace-only default, the manifest reason, and the parent-directory assertions passed. The generated name was `20260726T204020135395Z-cosmetic_workshop-export-before_import____unsafe.json`.
4. **Exact failure** — `AssertionError: assert 'before_import_unsafe' in '20260726T204020135395Z-cosmetic_workshop-export-before_import____unsafe.json'` at `backend/app/tests/test_exports_api.py:279`.
5. **Setup versus call** — **Call**, not setup. The API was reached and the export JSON was written and successfully re-read before the failing assertion.
6. **Deterministic / intermittent** — **Deterministic** across two isolated runs and the full-suite run.
7. **Surrounding test file** — `1 failed, 10 passed`.
8. **Classification** — **INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED**
9. **Evidence supporting classification**
   - The same undecided contract applies. `backend/app/services/export.py:84` is character-for-character the same implementation as `backend/app/services/backup.py:47`, differing only in the fallback value returned when the sanitized string is empty (`"manual"` versus `"backup"`). Neither module imports the other; a repository-wide search for `_safe_filename_part` returns only these two definitions and their local call sites.
   - **No product documentation defines the required behavior**, exactly as in §5. `docs/export.md` documents the manifest `reason` field and the export payload shape but states no filename normalization rule.
   - **This document does not state that the production behavior is wrong.** No root cause, no severity, and no correction surface is asserted for this node.
   - Recorded as observed facts, independent of the undecided contract: traversal characters are neutralized; `_unique_export_path` (`backend/app/services/export.py:123`) avoids overwriting an existing export; the charset is restricted; artifact generation is backend-owned and the artifact is human-readable JSON.
   - The structural duplication with node 1 is a fact about the code. It is **not** treated here as proof of a shared defect, because whether either module is defective is undecided.
10. **Relevant paths** — test `backend/app/tests/test_exports_api.py:279`; production `backend/app/services/export.py:78` (`normalize_export_reason`), `:84` (`_safe_filename_part`), `:116` (`_export_filename`), `:123` (`_unique_export_path`); API `backend/app/api/exports.py`; documentation `docs/export.md`.
11. **Severity** — `NOT DETERMINED FROM CURRENT EVIDENCE`
12. **User-visible or data-integrity impact** — `NOT DETERMINED FROM CURRENT EVIDENCE`
13. **Likely correction surface** — `NOT DETERMINED FROM CURRENT EVIDENCE`
14. **Schema / migration requirement** — `NOT DETERMINED FROM CURRENT EVIDENCE`
15. **Shared root cause or duplicated contract** — `NOT DETERMINED FROM CURRENT EVIDENCE`. See §5 field 15.
16. **Smallest safe slice** — `NOT DETERMINED FROM CURRENT EVIDENCE`
17. **Required tests** — `NOT DETERMINED FROM CURRENT EVIDENCE`
18. **Required smoke** — `NOT DETERMINED FROM CURRENT EVIDENCE`

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
   - Unlike nodes 1 and 2, this contract **is** documented. `docs/import-format.md:152` states: *"Dates should use ISO `YYYY-MM-DD`. Deterministic Russian `DD.MM.YYYY` dates are normalized to ISO with `date_format_normalized`; ambiguous slash dates are not accepted."* `05.07.2026` is exactly a deterministic Russian `DD.MM.YYYY` date, so a `date_format_normalized` **warning** is the documented correct outcome and `invalid_date` would contradict the documented contract.
   - The sibling test `backend/app/tests/test_import_parsing.py:144` asserts that `date_format_normalized` is emitted, and it **passes**. The sibling test `backend/app/tests/test_import_parsing.py:57-60` exercises `invalid_date` using the genuinely unparseable value `not-date`, and it also **passes**. Both behaviors are already correctly covered elsewhere, against the documented contract.
   - The failing node therefore encodes a superseded pre-normalization contract in two places at once: the `>= 4` count at line 107 and the `invalid_date` membership assertion at line 110. Line 110 would also fail if line 107 were relaxed.
   - The absence of a row-level `missing_required_value` for `ingredient_name` is correct and not a defect: `backend/app/services/imports.py:385-387` raises that row issue only when the required column exists but the cell is blank. When the column is absent entirely, the global `missing_required_column` error already covers it, so the design avoids double-counting one fault.
   - The documented import flow is intact and was verified in this task: upload → draft → validation → preview → confirmation → apply. Missing required columns and row issues **do** coexist in one draft, the draft is `blocked`, `can_apply` is `false`, and nothing was written to production tables.
10. **Relevant paths** — test `backend/app/tests/test_imports_api.py:107` and `:110`; production `backend/app/services/imports.py:40` (`ingredient_lots` required columns), `:170-177` (`_normalize_date_value`, `date_format_normalized` / `invalid_date`), `:371-373` (`missing_required_column`), `:385-387` (`missing_required_value`), `:180-197` (`_readiness`), `:200` (`_issue_counts`); contract `docs/import-format.md:79`, `:115-119`, `:152-154`.
11. **Severity** — **MEDIUM**
12. **User-visible or data-integrity impact** — **None.** The import contract behaves exactly as documented, drafts remain blocked, and no production data is mutated. The impact is on the engineering baseline: the stale assertions keep the backend suite red and, if "corrected" in the wrong direction, would weaken the documented `DD.MM.YYYY` normalization and reintroduce a rejected-date regression for real Russian-formatted files.
13. **Likely correction surface** — `backend/app/tests/test_imports_api.py` lines 107 and 110 only. No production change is indicated.
14. **Schema / migration requirement** — None.
15. **Shared root cause or duplicated contract** — **None.** No direct shared cause with nodes 1, 2, and 4 is proven; imports remain a separate slice.
16. **Smallest safe slice** — Slice `R2` in §10.
17. **Required tests** — Realign the two assertions to the documented contract (`error_count == 3`, `warning_count == 1`, row codes `{invalid_decimal, invalid_unit, date_format_normalized}`) and assert `apply_readiness.can_apply is false`. Do not skip, xfail, delete, rename, or weaken the test; the corrected test must be strictly more specific than `>= 4`.
18. **Required smoke** — Backend suite only. This is a test-only correction with no runtime surface, so no browser, visual, or route-rendering check applies.

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
   - The correct in-repo idiom therefore already exists and is proven by passing sibling tests; only this node uses an invalid seed. No product documentation is required to settle this: the domain rule, the failing call, and the proven alternative idiom are all in the repository.
   - This node already performs its own threshold setup on a separate line: `backend/app/tests/test_purchase_suggestions.py:215-216` sets `minimum_stock='10'` directly via SQL after seeding. It therefore does **not** need the threshold raised the way `:79` does through `set_thresholds`. A lot quantity of `1` is already below the existing threshold of `10`, so changing only the `lot_qty` value satisfies the below-minimum condition and no second edit is required.
   - **The test is not genuinely manual.** Despite the `manual` in its name it carries no manual-only marker and no skip beyond the `TestClient is None` availability guard, so pytest collects and runs it automatically. Automatic collection is intended; the collection itself is not the defect.
   - **Equivalent automated coverage is partial, not complete.** `test_low_stock_and_order_shortages_generate_suggestions_and_quantities` (`:77`) covers suggestion generation and quantities, and `test_regeneration_and_mark_purchased_are_read_only_for_business_tables` (`:187`) covers regenerate plus `mark_purchased` read-only semantics — but both operate at the service/repository layer. This node is the only coverage of the `/api/purchase-suggestions` **HTTP** surface for regenerate, list, status filtering, and mark-purchased. While it fails at seeding, that API-layer coverage does not execute at all.
10. **Relevant paths** — test `backend/app/tests/test_purchase_suggestions.py:211-232`; shared helper `backend/app/tests/test_production_confirmation.py:50-62` (`seed_ready`); production `backend/app/domain/stock_movements.py:70-93` (`parse_stock_quantity`), `:179` (`StockMovementDraft.create`); API `backend/app/api/purchase_suggestions.py`; service `backend/app/services/purchase_suggestions.py`.
11. **Severity** — **MEDIUM**
12. **User-visible or data-integrity impact** — **None.** No product behavior is wrong; the domain correctly refuses an invalid movement. The impact is lost test coverage: the purchase-suggestions HTTP API has no executing end-to-end assertion, including the assertion that `mark-purchased` creates no stock movements, no packaging movements, and no lots. That read-only guarantee is a genuine data-safety property currently unverified at the API layer.
13. **Likely correction surface** — `backend/app/tests/test_purchase_suggestions.py:214` seeding only. No production change is indicated.
14. **Schema / migration requirement** — None.
15. **Shared root cause or duplicated contract** — **None.** No direct shared cause with nodes 1, 2, or 3 is proven; purchase suggestions remain a separate slice.
16. **Smallest safe slice** — Slice `R3` in §10 — **the active slice**.
17. **Required tests** — Change exactly one value: `lot_qty="0"` → `lot_qty="1"` in the `seed_ready(...)` call at `backend/app/tests/test_purchase_suggestions.py:214`. Leave `packaging_qty="2"` on that same line unchanged, and leave the existing `minimum_stock='10'` setup at `:215-216` unchanged — the existing threshold of `10` is already higher than the new lot quantity of `1`, so the below-minimum condition remains true without touching the threshold. No other line in the test may change. All existing assertions — including the three no-mutation assertions — must be preserved and must execute. Do not delete, rename, skip, `xfail`, or weaken the test.
18. **Required smoke** — Backend suite only. This is a test-only correction with no runtime surface, so no browser, visual, or route-rendering check applies.

---

## 9. Grouping evidence

**Nodes 1 and 2 are not grouped into a correction slice.** They are structurally duplicated implementations of one filename contract, and that duplication is recorded as a fact in §5 and §6. It is deliberately **not** used to justify a combined correction slice here, because the combined-slice rule requires that both modules exhibit the same *proven defect*. No defect is proven for either node while the product contract is undecided. Grouping is therefore deferred until the product decision exists; if that decision concludes that runs must collapse, the duplicated-implementation grouping evidence in §5 and §6 already supports a single bounded slice at that time.

**Nodes 3 and 4 are not grouped with each other or with nodes 1 and 2.** They share no helper, no contract, and no cause. Each is a test-only correction in a different subsystem, and each remains a separate slice.

A third sanitizer, `backend/app/services/report_documents.py:174 sanitize_reason`, implements a **different** contract — it permits spaces and dots, collapses only repeated dots, strips a wider separator set, and truncates to 80 characters. It is not part of any grouping here and must not be unified into a shared helper without an explicit decision.

---

## 10. Slices

### Slice R3 — Repair purchase-suggestions API smoke seeding — **DONE**

- **Title** — `R3 — Repair purchase-suggestions API smoke seeding`
- **Scope** — Exactly one changed value. In the `seed_ready(...)` call at `backend/app/tests/test_purchase_suggestions.py:214`, change `lot_qty="0"` to `lot_qty="1"`. Leave `packaging_qty="2"` on that same line unchanged. Leave the existing `minimum_stock='10'` setup at `backend/app/tests/test_purchase_suggestions.py:215-216` unchanged. **The existing threshold of `10` is already higher than the new lot quantity of `1`, so the below-minimum condition the test needs remains true without touching the threshold.** No other line in the test may change.
- **Non-goals** — No production-code change of any kind; no change to `seed_ready`'s signature, body, or any other caller; no change to the zero-quantity domain rule; no change to the existing `minimum_stock='10'` setup or to any line of the test other than the `lot_qty` value on line 214; no change to nodes 1, 2, and 3; no schema, migration, dependency, lockfile, or pytest-configuration change; no frontend change.
- **Architecture constraints** — The zero-quantity rejection rule at `backend/app/domain/stock_movements.py:84-93` stays intact and unmodified. Stock changes stay routed through `StockMovement`. The test's three no-mutation assertions stay intact and must execute. The existing `minimum_stock='10'` threshold stays unchanged; the below-minimum condition is preserved by the threshold already exceeding the new lot quantity of `1`, not by editing the threshold. The diff for this slice is exactly one changed value on one line.
- **Backend requirements** — None. This slice is **test-only**.
- **Frontend requirements** — None.
- **Data model / migrations** — None.
- **Tests** — The node reaches and exercises the `/api/purchase-suggestions` HTTP surface: regenerate creates at least one suggestion, list returns it, mark-purchased returns `purchased`, the suggestion leaves the open list, it remains visible under `status=all`, and the stock-movement, packaging-stock-movement, and ingredient-lot counts are unchanged. Every existing assertion is preserved. No skip, `xfail`, deletion, rename, or weakened assertion. The **complete backend suite** must be run from `backend/`.
- **Smoke** — **Backend suite only.** The slice changes no runtime surface, so no browser, visual, or route-rendering check applies or is claimed.
- **Acceptance criteria** — The backend baseline improves from `4 failed` to `3 failed` with no new failure. The remaining three failures are exactly the two undecided filename nodes and the deferred `R2` node. The node's three no-mutation assertions execute and pass. No production file is modified. The test diff is exactly one changed value, `lot_qty="0"` → `lot_qty="1"`, on line 214.
- **Implementation result** — `IMPLEMENTED — REVIEW AND MERGE REQUIRED` (EXECUTED IN THIS TASK, on the `R3` PR branch; **not merged**). The authorized one-value change was applied and nothing else in the runtime/test tree changed:
  - runtime/test diff is exactly one changed value on one line — `lot_qty="0"` → `lot_qty="1"` at `backend/app/tests/test_purchase_suggestions.py:214`; `packaging_qty="2"` and the `minimum_stock='10'` setup at `:215-216` are unchanged, and no other line of the test changed;
  - no production file changed; the zero-quantity rule at `backend/app/domain/stock_movements.py:84-93`, `seed_ready(...)`, and all other `seed_ready(...)` call sites are untouched;
  - the target node now **passes twice** in isolation and reaches the `/api/purchase-suggestions` HTTP surface: `POST /api/purchase-suggestions/regenerate`, `GET /api/purchase-suggestions`, `POST /api/purchase-suggestions/{id}/mark-purchased`, the default open-list filter, and `status=all` all execute;
  - the three no-mutation assertions execute and pass: stock-movement count, packaging-stock-movement count, and ingredient-lot count are unchanged across `mark-purchased`;
  - the surrounding file `app/tests/test_purchase_suggestions.py` passes `11/11`;
  - the complete backend suite, run from `backend/`, is `496 collected / 493 passed / 3 failed / 0 skipped`;
  - the remaining three failures are exactly the two undecided filename nodes (§5, §6) and the deferred `R2` node (§7); no new failure and no skip appeared.
  - Environment: Python `3.12.13`, pytest `8.4.2`, rootdir `backend/`, configfile `pyproject.toml`, temporary venv outside the repository, removed and verified absent after the run.
  - The classification of nodes 1–3 is unchanged by this implementation, and `CR-005` remains undecided.
- **Merge closure** — `R3` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB). PR #143 `R3 — Repair purchase-suggestions API smoke seeding`, state `MERGED`, final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`, merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`, merged at `2026-07-27T04:01:23Z`. Accepted `R3` backend result: `496 collected, 493 passed, 3 failed, 0 skipped`. No production code changed in `R3`. Node 4 now passes on `origin/main` and is closed. The pre-merge `R3` record above is preserved unchanged as historical evidence and is superseded by this closure line.

### Slice R2 — Import draft issue-count contract alignment — **DONE**

- **Title** — `R2 — Align import draft baseline test with the documented date-normalization contract`
- **Scope** — The assertion block of `backend/app/tests/test_imports_api.py::test_missing_required_columns_and_row_errors_create_draft_with_issues` only.
- **Non-goals** — No production change; no change to `docs/import-format.md`; no change to nodes 1, 2, and 4; no change to `_normalize_date_value`, readiness calculation, issue counting, required-column behavior, `missing_required_value`, import Apply, or the import preview/confirmation flow; no change to the test date `05.07.2026`; no skip, `xfail`, deletion, rename, or weakened assertion.
- **Architecture constraints** — Direct Apply stays prohibited; row issues are never discarded; validation is never weakened; no production data is mutated; deterministic `DD.MM.YYYY` normalization stays supported; `date_format_normalized` stays a warning; `invalid_date` stays reserved for genuinely invalid dates; missing required columns keep blocking Apply.
- **Backend requirements** — None. Test-only.
- **Frontend requirements** — None.
- **Data model / migrations** — None.
- **Tests** — As §7 field 17.
- **Smoke** — Backend suite only.
- **Acceptance criteria** — The node passes with assertions strictly more specific than `>= 4`, and the documented `DD.MM.YYYY` → `date_format_normalized` behavior is asserted rather than removed.
- **Implementation result** — `IMPLEMENTED — REVIEW AND MERGE REQUIRED` (EXECUTED IN THIS TASK, on the `R2` PR branch from starting `origin/main` `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`; **not merged**). The authorized assertion-block change was applied and nothing else in the runtime/test tree changed:
  - the runtime/test diff is exactly the assertion block of the target test — `error_count >= 4` → `error_count == 3`, added `warning_count == 1`, added `apply_readiness.can_apply is False`, and the row-code subset assertion `{"invalid_decimal", "invalid_unit", "invalid_date"} <= row_codes` → the exact-set assertion `row_codes == {"invalid_decimal", "invalid_unit", "date_format_normalized"}`; the response status assertion, request payload, CSV data, date `05.07.2026`, target type, and the global `missing_required_column` assertion are unchanged, and no other line of the file changed;
  - no production file changed; `_normalize_date_value`, `_readiness`, `_issue_counts`, the required-column and `missing_required_value` behavior, and import Apply are untouched, and `docs/import-format.md` was not modified;
  - observed contract confirmed before editing: `201`, `error_count` `3`, `warning_count` `1`, readiness `blocked`, `can_apply` `false`, global codes `{missing_required_column}`, row-0 codes `{invalid_decimal, invalid_unit, date_format_normalized}` with `date_format_normalized` carrying severity `warning` and the message "В строке 2 дата «05.07.2026» будет прочитана как 2026-07-05";
  - the target node now **passes twice** in isolation;
  - the surrounding file `app/tests/test_imports_api.py` passes `7/7`;
  - the sibling file `app/tests/test_import_parsing.py` passes `16/16` with zero skips, so `date_format_normalized` still works and genuinely invalid dates still emit `invalid_date`;
  - the complete backend suite, run from `backend/`, is `496 collected / 494 passed / 2 failed / 0 skipped`;
  - the remaining two failures are exactly nodes 1 and 2 (§5, §6); `app/tests/test_purchase_suggestions.py::test_manual_api_smoke` passes; no new failure and no skip appeared.
  - Environment: Python `3.12.13`, pytest `8.4.2`, rootdir `backend/`, configfile `pyproject.toml`, temporary venv outside the repository, removed and verified absent after the run.
  - The classification of nodes 1 and 2 is unchanged by this implementation, and `CR-005` remains undecided. No correction slice for the filename nodes is created or authorized here.
- **Merge closure** — `R2` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB). PR #144 `R2 — Align import draft baseline test with date normalization`, state `MERGED`, final reviewed head `52e2c64fc601b458cfd60e8b86a778efabd65671`, merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c`, merged at `2026-07-27T04:21:16Z`. Accepted `R2` backend result: `496 collected, 494 passed, 2 failed, 0 skipped`. No production code changed in `R2`. Node 3 now passes on `origin/main` and is closed. The pre-merge `R2` record above is preserved unchanged as historical evidence and is superseded by this closure line. See §14.1.

### Nodes 1 and 2 — no slice at diagnosis time — superseded by §14

No correction slice exists for the backups and exports filename nodes. They are blocked on the change request *"Decide the backup/export filename normalization and hyphen round-trip contract"* (`needs product decision`), recorded in `state/change-requests.md`. That decision must cover:

- whether consecutive unsafe characters collapse to one underscore;
- whether literal hyphens remain allowed;
- how backup filename-to-metadata reason round-trip works;
- whether the displayed reason is filename-derived or stored independently;
- the required focused smoke after implementation.

Any focused visual or route-rendering check for `/backups` and `/exports` belongs to that product decision and its future implementation slice, **not** to the current active slice.

**Superseded.** `CR-005` has since been decided and accepted. All five listed questions are answered in §14.2, both nodes are reclassified in §14.3 and §14.4, and one bounded slice `R4` is authorized in §14.6. The paragraph above is preserved as the record of the pre-decision state.

---

## 11. Selection

**Primary selection priority applied** (from most to least important: data loss or unsafe mutation → backup/recovery reliability → import integrity → broken user-visible API → test defect hiding coverage → manual-smoke collection hygiene):

- **No node reaches priorities 1, 2, or 3.** No data loss or unsafe mutation was found. Backup and recovery behavior was not shown to be impaired: backups are created, are not overwritten, contain no path separator, and do not modify the source database. Import integrity is intact and matches the documented contract.
- **No node reaches priority 4.** A "broken user-visible API" finding cannot be asserted for nodes 1 and 2, because whether the current filename output is wrong is exactly the undecided question. Severity was deliberately not inflated to create a priority-4 candidate.
- **Nodes 3 and 4 reach priority 5** — test defects. Node 4 additionally leaves the purchase-suggestions HTTP surface with no executing coverage; node 3 blocks a clean baseline.
- **No node is priority 6.** Node 4 is automatically collected and intended to be; its name is misleading but collection hygiene is not the defect.

**Tie-breaker.** `R3` and `R2` tie at priority 5, so the documented tie-breaker was applied in order. Both rest on equally strong in-repository evidence, so criterion 1 does not separate them. Criterion 2, greater direct user/data impact, does: `R3` restores execution of a real data-safety guarantee — that mark-purchased creates no stock movements, no packaging movements, and no lots — which is currently unverified at the API layer, whereas `R2` only unblocks the baseline. `R3` is therefore selected ahead of `R2`.

Both candidates are fully evidenced from repository sources alone and need no product decision, which is why one of them can be activated while nodes 1 and 2 cannot.

**Selection at diagnosis time: `R3` first, then `R2`.** `R3` is now merged and DONE, so the **active slice is `R2`**, implemented and pending review and merge. Nodes 1 and 2 have no slice and are blocked on a product decision. Exactly one slice is active.

---

## 12. Adjacent finding recorded but not part of this gate

**Potential backup consistency finding — not classified or activated.**

The current backup helper copies the SQLite database file through `shutil.copy2`, and the startup before-migration path uses the same helper. This raises a transaction-consistency question when the database may be live or use auxiliary SQLite files. Some existing tests pass ordinary bytes rather than a real SQLite database to the helper, so a future diagnostic must inspect those fixtures.

This task records only the need for a separate evidence-based diagnostic.

Do not classify the behavior as unsafe and do not prescribe a correction design here.

This finding is **not** one of the four current failures, is **not** diagnosed, scoped, or activated here, and is tracked as a `needs evidence` row in `state/change-requests.md`. It is distinct from the `needs product decision` filename-contract row in §10.

---

## 13. Slice lifecycle

The original diagnostic evidence in §2–§9 and §11 is preserved unchanged. This section records only how the gate's slices have progressed since diagnosis.

| Slice | Node | Status | Evidence |
|---|---|---|---|
| `R3` | Node 4 — purchase suggestions manual API smoke | **DONE** | PR #143 `MERGED`; final reviewed head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`; merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`; merged `2026-07-27T04:01:23Z`; accepted result `496 / 493 / 3 / 0` (VERIFIED FROM REPOSITORY / GITHUB) |
| `R2` | Node 3 — import draft issue count | **DONE** | PR #144 `MERGED`; final reviewed head `52e2c64fc601b458cfd60e8b86a778efabd65671`; merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c`; merged `2026-07-27T04:21:16Z`; accepted result `496 / 494 / 2 / 0` (VERIFIED FROM REPOSITORY / GITHUB) |
| `R4` | Nodes 1 and 2 — backups and exports filename reason | **IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE** | `CR-005` decision PR #145 `MERGED` (head `7d68b45bee1f223b67f105c30e3acbb89dc8d41d`, merge commit `bef36822e50c245b72f813dad0afbffc7f772588`); implemented on branch `claude/r4-canonical-artifact-reason-normalization`; branch result `562 / 562 / 0 / 0`; not reviewed and not merged — see §15 |

After `R2`, the complete backend suite run from `backend/` is `496 collected, 494 passed, 2 failed, 0 skipped`, and the remaining failures are exactly nodes 1 and 2:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

No production file changed in `R3` or in `R2`; both slices are test-only. The `INCONCLUSIVE — PRODUCT CONTRACT NOT YET DECIDED` classification recorded for nodes 1 and 2 in §5 and §6 was **correct at diagnosis time** and is preserved unchanged as historical evidence. It has since been superseded by the accepted `CR-005` product decision; the resulting post-decision classification is recorded in §14 below and does not edit §5, §6, or §9.

**Superseded.** The lifecycle table above records the state **before** `R4` merged, when `R4` was still `IMPLEMENTED — EXACT-HEAD SMOKE REQUIRED BEFORE MERGE` and the merged baseline was not yet green. It is preserved unchanged as the record of that state. `R4` has since merged as PR #146 and the gate is closed; the current lifecycle table is §16.3 and the closure evidence is §16.

---

## 14. R2 merge closure and post-decision classification of nodes 1 and 2

This section was added after `CR-005` was decided. It supersedes nothing in §2–§9 and §11; the original diagnostic evidence and its classification **at diagnosis time** stand unchanged. Nothing here is a test or runtime result: no implementation was performed and no backend suite was executed for the decision that produced this section.

### 14.1 `R2` merge closure

`R2` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB).

- PR #144 `R2 — Align import draft baseline test with date normalization`, state `MERGED`.
- Final reviewed head: `52e2c64fc601b458cfd60e8b86a778efabd65671`.
- Merge commit: `8efbdc5c85b5932f4aeef51045542c207cf4635c`.
- Merged at: `2026-07-27T04:21:16Z`.
- No production code changed in `R2`; the slice was test-only.

Accepted backend result after `R2` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — **not** re-executed for this section):

```text
496 collected
494 passed
2 failed
0 skipped
```

The two remaining failing nodes are exactly:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

Node 3 and node 4 are closed. Nodes 1 and 2 are the only open gate nodes.

### 14.2 The decided contract

`CR-005` is **accepted**. The full contract is durable in `docs/backup-and-restore.md` and `docs/export.md`, with the API-field semantics in `docs/api.md`. In summary, for **newly generated** backup and export artifacts:

- runs of non-alphanumeric separators collapse to **one** underscore;
- literal hyphens normalize to underscores inside the filename reason segment;
- leading and trailing underscores are removed;
- an empty result becomes `manual`;
- a numeric-only result is prefixed with `reason_`;
- letter case and Unicode alphanumerics are preserved; no lowercasing, transliteration, or new truncation;
- the create, list, and status `reason` values are the canonical **filename-derived** segment, and the visible UI reason resolves from that same segment — the frontend consumes the canonical slug without reconstructing, sanitizing, or normalizing it, mapping **known system slugs** to the **existing localized Russian display labels** and rendering **custom or unmapped slugs verbatim**, so the visible label is not always literally the slug;
- the uniqueness suffix is never part of the reported reason;
- the export JSON manifest keeps the **normalized human reason**;
- existing artifacts are never renamed, rewritten, or migrated, and legacy listing stays best-effort.

This settles the exact question that made nodes 1 and 2 inconclusive. The two independently written tests that assert the collapsed form are now confirmed to encode the intended contract.

### 14.3 Node 1 — Backups filename reason — post-decision classification

- **Post-decision classification** — **PRODUCT DEFECT — CONTRACT MISMATCH**
- **Severity** — **MEDIUM**
- **Impact**
  - user-visible mismatch between the filename and the reason label;
  - ambiguous round-trip for hyphenated reasons — a reason of `before-import` is recovered by the metadata parser as `import`;
  - backend baseline failure;
  - **no proven data loss**;
  - no source database mutation;
  - no overwrite regression — `_unique_backup_path` still avoids overwriting an existing backup.

### 14.4 Node 2 — Exports filename reason — post-decision classification

- **Post-decision classification** — **PRODUCT DEFECT — CONTRACT MISMATCH**
- **Severity** — **MEDIUM**
- **Impact**
  - user-visible mismatch between the filename and the reason label;
  - filename slug inconsistent with the newly decided contract;
  - backend baseline failure;
  - export manifest data remains readable;
  - **no proven data loss**;
  - no overwrite regression — `_unique_export_path` still avoids overwriting an existing export.

### 14.5 Shared root cause and grouping

The shared root cause is now decided rather than merely structural:

- two duplicated one-character-at-a-time sanitizers — `backend/app/services/backup.py:47` and `backend/app/services/export.py:84` — differing only in their empty-result fallback;
- both currently preserve a literal hyphen inside the reason segment;
- both lack the decided run-collapse and numeric-disambiguation rules.

§9 deferred grouping explicitly until a product decision existed, and stated that the duplicated-implementation evidence would then support a single bounded slice. That condition is now met. Nodes 1 and 2 share **one decided product contract** and are corrected in **one** bounded implementation slice, `R4`.

`backend/app/services/report_documents.py:174 sanitize_reason` remains a deliberately **different** contract and stays out of scope. It must not be unified into the shared helper.

### 14.6 `R4` contract

`R4 — Canonical backup/export filename reason normalization` is authorized and is **NOT IMPLEMENTED**. It may begin only after the `CR-005` decision pull request is merged, and only from `origin/main`. The full `R4` Scope, Non-goals, Architecture constraints, Backend requirements, Frontend requirements, Tests, Smoke, and Acceptance criteria are recorded in `docs/implementation-plan.md`.

Key boundaries:

- one narrowly scoped shared backend helper — recommended `normalize_artifact_reason_segment(value: str | None) -> str` in `backend/app/services/local_artifact_filenames.py`;
- the helper applies **only** to backup and export filename reason segments — never to backup source database stems, report-document reasons or filenames, uploaded filenames, recipe names, client names, or any other domain value;
- expected production surface is bounded to `backend/app/services/local_artifact_filenames.py`, `backend/app/services/backup.py`, and `backend/app/services/export.py`; a parser change inside those same service modules is allowed **only** where required by the new-file round-trip contract, and a filename-format migration must not be authorized merely to simplify parsing;
- the two existing failing tests must be preserved and made to pass **without being weakened**; no existing test may be deleted, renamed, skipped, or `xfail`-ed;
- acceptance requires every collected backend test to pass with `0 failed` and `0 skipped`. Because `R4` adds tests, the collection count is **not** required to stay at `496`;
- **no frontend production change is expected**, but focused **frontend test-only** changes are allowed so that the canonical-reason display contract is actually proven — either by adding reason-presentation assertions to the runnable `frontend/test/local-artifacts-reports-feedback.test.mjs` suite (preferred), or by making the standalone local-artifact-presentation suite runnable through an exact tsconfig and npm script without adding dependencies. The frontend production build and the final published-head browser smoke both remain required.

### 14.7 What this section does not claim

This subsection records the state **at decision time** and is preserved unedited. For the later `R4` branch implementation result see §15.

- **No implementation result.** `R4` is not implemented.
- **The two failures are not fixed.** Both nodes still fail on `origin/main` at `8efbdc5c85b5932f4aeef51045542c207cf4635c`.
- No backend `0-failure` state is claimed.
- No backend suite, frontend suite, frontend build, or browser smoke was executed for the decision that produced this section.
- `CR-004` — the potential SQLite backup transaction-consistency candidate in §12 — remains a separate `needs evidence` row and is **not** resolved, activated, or affected by this decision.

---

## 15. R4 branch implementation result (2026-07-27)

This section is a **branch** result. It supersedes nothing in §2–§9, §11, or §14; all earlier diagnostic evidence and its classification at diagnosis time stand unchanged.

Branch: `claude/r4-canonical-artifact-reason-normalization`, created directly from `origin/main` at `bef36822e50c245b72f813dad0afbffc7f772588`, which is the merge commit of the `CR-005` decision PR #145.

### 15.1 Pre-change baseline, re-executed on the branch

Executed from `backend/` with Python `3.12.13` and pytest `8.4.2` (rootdir `backend/`, configfile `pyproject.toml`), in a temporary virtual environment created outside the repository:

```text
496 collected
494 passed
2 failed
0 skipped
```

The two failures were exactly nodes 1 and 2. Each node was re-run twice in isolation and reproduced identically: the API call is reached, the artifact is created, unsafe characters are neutralized, the implementation emits one underscore per replaced character where the accepted contract requires one collapsed underscore run, and no overwrite or data-loss defect was observed. No baseline drift.

### 15.2 Post-change result on the branch

```text
562 collected
562 passed
0 failed
0 skipped
```

- Both former baseline nodes now pass; each was re-run twice in isolation after the change.
- All 496 previously collected node IDs are still collected; the collection difference is 66 added tests.
- No existing test was deleted, renamed, skipped, `xfail`-ed, or weakened.
- Production change is confined to `backend/app/services/local_artifact_filenames.py` (new shared helper), `backend/app/services/backup.py`, and `backend/app/services/export.py`. No API, schema, model, repository, or migration file changed. No frontend production file changed.
- Frontend: `npm run test:local-artifacts-reports-feedback` gives `40 pass, 0 fail, 0 skipped`; `npm run build` succeeds.

### 15.3 What §15 does not claim

- **`R4` is not DONE.** It is not reviewed and not merged.
- **No claim that the merged `main` baseline is already green.** On `origin/main` at `bef36822e50c245b72f813dad0afbffc7f772588` both nodes still fail; `562 / 562 / 0 / 0` is a branch result only.
- The focused exact-published-head `/backups` and `/exports` browser smoke is the remaining pre-merge gate and was **not** executed at the time this section was committed. A passing smoke is invalidated by any later commit.
- `CR-004` remains a separate, unresolved `needs evidence` row. Restore remains unimplemented. Product release readiness is not claimed.

---

## 16. Gate closure — R4 merged; both filename nodes closed (2026-07-27)

This section closes the gate. It **supersedes nothing**: §2–§9, §11, §14, and §15 are preserved unchanged, including the pre-merge `R4` branch record in §15 and its explicit statement that the merged baseline was not yet green at the time it was written.

Every result in this section is **VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE**. None of it was executed in the documentation task that added this section.

### 16.1 R4 merge closure

`R4` is **DONE**.

- PR #146 `R4 — Canonical backup/export filename reason normalization`, state `MERGED`.
- Final reviewed head: `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`.
- Merge commit: `127191feb182ccf68a4d7b9f2be28f6aa5b42453`.
- Merged at: `2026-07-27T08:51:06Z`.
- `origin/main` equals that merge commit; both the final head and the merge commit were verified as ancestors of `origin/main`.

**Both original filename nodes are closed on `main`:**

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

All four gate nodes are now closed: node 3 by `R2`, node 4 by `R3`, and nodes 1 and 2 by `R4`. **The backend baseline correction gate is DONE.**

### 16.2 Accepted merged result

Accepted merged backend result on `main`:

```text
562 collected
562 passed
0 failed
0 skipped
```

| Check | Accepted result |
|---|---|
| Backend complete suite | `562 / 562 / 0 / 0` |
| Frontend focused suite | `40 passed, 0 failed, 0 skipped` |
| Frontend production build | `PASS` |
| Focused exact-published-head `/backups` and `/exports` browser smoke | `PASS — FULL AUTOMATED SMOKE PASSED` |
| Exact smoke-tested head | `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb` |

The merged slice involved **no database migration**, **no filesystem migration**, **no existing artifact renamed, rewritten, or deleted**, and **no frontend production change**.

The `PRODUCT DEFECT — CONTRACT MISMATCH` (MEDIUM, no proven data loss) classification recorded for nodes 1 and 2 in §14.3 and §14.4 stands as the accepted post-decision classification and is now **resolved by the merged `R4`**. `CR-005` remains accepted and is now implemented. Neither `CR-005` nor `R4` is reopened.

### 16.3 Slice lifecycle — final

| Slice | Node | Status | Evidence |
|---|---|---|---|
| `R3` | Node 4 — purchase suggestions manual API smoke | **DONE** | PR #143 `MERGED`; head `c5fc27059a7aea0435c84535d2d15e6a0fc58428`; merge commit `f6468fae04f9dc7ae03a491560a32fac94f3a1ec`; accepted result `496 / 493 / 3 / 0` |
| `R2` | Node 3 — import draft issue count | **DONE** | PR #144 `MERGED`; head `52e2c64fc601b458cfd60e8b86a778efabd65671`; merge commit `8efbdc5c85b5932f4aeef51045542c207cf4635c`; accepted result `496 / 494 / 2 / 0` |
| `R4` | Nodes 1 and 2 — backups and exports filename reason | **DONE** | PR #146 `MERGED`; head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`; merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453`; accepted result `562 / 562 / 0 / 0`; exact-head smoke `PASS` |

The §13 lifecycle table records the state before the `R4` merge and is preserved unchanged; this table supersedes it.

**No successor runtime slice is selected by this closure.** The next gate must be separately selected and authorized.

---

## 17. Separate post-R4 observation — export create-response fallback

This is **not** a fifth backend baseline failure and it is **not** part of the four-node gate scoped in §1. It is a separate observation recorded after `R4` merged, tracked as `CR-006` in `state/change-requests.md`.

### 17.1 Exact current behavior

Read-only inspection of `backend/app/api/exports.py::create_export` on `origin/main` at `127191feb182ccf68a4d7b9f2be28f6aa5b42453` (VERIFIED FROM REPOSITORY):

- after `create_json_export` writes an export, the endpoint attempts to find the exact created file through `list_export_files`, matching on `export.path == result.export_path`;
- when the exact file is found, the API response is built from the parsed filename metadata and therefore returns the **canonical filename-derived reason**, per the `CR-005` contract;
- when the exact file is **not** found, the defensive fallback constructs an `ExportFile` using `ExportResult.reason`;
- `ExportResult.reason` is the normalized **human** reason — the same value preserved in the export JSON manifest, produced by `normalize_export_reason`, not by `normalize_artifact_reason_segment`;
- therefore the fallback **may** return a human reason where the API contract normally expects the canonical filename-derived slug.

### 17.2 Classification

**Classification — `NEEDS EVIDENCE`.**

- **This is not classified as a confirmed product defect.**
- **No user-visible failure has been reproduced.**
- **No data loss, overwrite, incorrect file content, or unsafe mutation is proven.**
- **No severity is assigned.**
- **No correction design is authorized.**

The normal path is green: the merged backend suite passes `562 / 562 / 0 / 0`, create/list/status integration coverage passes, and the focused exact-head browser smoke passed with the canonical slug reported on create, list, and status and rendered verbatim in the UI.

**Fallback reachability is not established.** No evidence in this repository shows that the exact-match lookup can fail in normal operation immediately after a successful write.

### 17.3 Required future diagnostic

A future, separately authorized diagnostic must answer two questions **in order**, and must not skip to an implementation.

First, whether the fallback can occur at all, under:

- artifact disappearance after write;
- a filesystem race;
- a permission or `stat` failure;
- a list/read failure;
- mocked or injected repository/service behavior.

Second, only once reachability is established, the desired contract:

- return a canonical reason;
- fail explicitly because the created artifact cannot be confirmed;
- or another documented outcome.

**No correction is authorized yet.** Do not change `backend/app/api/exports.py`, `ExportResult`, `list_export_files`, the API schemas, or the API error responses on the strength of this observation alone.

### 17.4 Boundaries

- **Non-blocking** for `R4` closure; `R4` remains **DONE**.
- **Not** an active implementation slice.
- **Not** part of `CR-004`.
- **Not** a reason to reopen `CR-005`.
- **Not** a reason to reopen `R4`.
- **Not** added as a fifth backend baseline failure; the gate scope in §1 is unchanged and closed.

Tracked as `CR-006 — Investigate export create-response fallback confirmation semantics`, status `needs evidence`, with no target PR assigned.

> **Superseded status line.** The `needs evidence` status above was correct when
> §17 was written and is preserved as that record. The diagnostic has since been
> executed; the completed evidence conclusion is §17.5, and `CR-006` is now
> `accepted`.

### 17.5 Completed evidence conclusion (2026-08-01)

`CR-006` is **resolved**. The evidence-only diagnostic required by §17.3 was
executed against `origin/main` = `1d4e90ccffb6f154882e685b09803f67f2f75ceb`,
Python `3.12.10`, FastAPI `0.115.12`, through the real FastAPI route, the real
`create_json_export`, an isolated migrated SQLite database and an isolated
export directory per scenario. Faults were injected only at named OS boundaries
(`pathlib.Path.stat`, `pathlib.Path.iterdir`) and named module seams
(`app.api.exports.list_export_files`, `app.api.exports.create_json_export`). **No
production file was modified**, and the temporary harness lived outside the
repository and was not committed. The reason under test was
`before-update ../unsafe`, whose canonical filename segment is
`before_update_unsafe`.

**Question 1 — can the fallback occur at all? Yes.** A synthetic empty-list
control reached it directly.

**Question 1b — is it reachable outside mocks? Yes.** A per-file `stat` failure
on the exact created file during the endpoint's secondary
`list_export_files(...)` reaches it while the export is present and correct on
disk, and so does a directory-entry race in which the file is gone from
`stat`'s point of view after `iterdir()` listed it. `list_export_files` catches
`OSError` from `_export_file_metadata` and silently skips the entry.

**Question 2 — the required contract.** Decided as **canonical reconstruction
from the authoritative create result**, recorded durably in
`docs/decisions/0014-json-export-create-confirmation-semantics.md`: a
successfully returned `ExportResult` is the authoritative result of the create
operation; the response is built only from it; the API `reason` is parsed from
the exact final filename through the same contract list and status use;
`ExportResult.reason` (the human manifest reason) is never the API reason; the
directory re-scan is removed from the create path but remains authoritative for
the independent `GET` reads; `201 Created` describes the operation boundary and
promises no permanent retention.

**Classification.**

```text
PRODUCT DEFECT — CREATE-RESPONSE CONTRACT MISMATCH
Severity: MEDIUM
```

Confirmed impact: inaccurate create-response metadata; human/canonical reason
mismatch that would be visible verbatim on `/exports`; false total failure —
HTTP `500` after a fully created export — when the same secondary scan raises a
non-ignorable `OSError`; and a duplicate-create risk that follows from that
false failure.

Explicitly **not** found: application-caused data loss, overwrite, incorrect
export bytes, source database mutation, or privacy exposure. A file removed by
an injected external actor after the creator returned is **not** treated as
application data loss.

**Adjacent findings, deliberately separated and not resolved by `CR-006`:**

1. The creator's own post-write `stat` at `backend/app/services/export.py:266`
   sits outside the `try` that maps `OSError` to `ExportError`, so a failure
   there escapes as a raw `OSError`, the endpoint returns a generic `500`, and a
   complete export remains on disk unreported. The fallback is unreachable on
   this path. `C3-II-B2` must carry a verification test for it; whether the
   endpoint's error mapping changes is not decided.
2. `GET /api/exports` and `GET /api/exports/status` inherit the same best-effort
   listing: a per-file `stat` failure silently omits a real export and reports
   `export_count: 0` / `latest_export: null`, and a directory `iterdir` failure
   makes both return `500`. Their contract is **unchanged** by this decision.

**Boundaries preserved.** `CR-005`, `R4`, `CR-009` and `C3-II-B1` are not
reopened; the export manifest reason and export schema version are unchanged; no
migration and no production change was made; `CR-004` is untouched and
`C3-II-B3` stays blocked. `C3-II-B2` is authorized only after the `CR-006`
decision pull request merges and is **not implemented**. The four-node gate
scope in §1 is unchanged and stays closed; this is still not a fifth backend
baseline failure. Full diagnostic matrix:
`docs/decisions/0014-json-export-create-confirmation-semantics.md`.
