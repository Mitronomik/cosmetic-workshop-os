# UI/UX Contract

This contract defines the product-owned interface rules for **cosmetic-workshop-os** / **Мастерская косметолога**. It applies to frontend, visual, accessibility, responsive, copy, and motion work. It does not replace the product specification, architecture contract, or domain model; it translates them into practical UI decisions.

The product is a local-first working system for a small cosmetic workshop. It must feel calm, understandable, and operational — not like a technical administration panel, generic SaaS dashboard, enterprise ERP, design showcase, online shop, or unrelated card collection.

## Primary user and daily jobs

The primary user is a non-technical cosmetic maker who uses the app to answer daily operational questions:

- What needs attention today?
- Which orders are waiting, ready, in progress, produced, or delivered?
- Which formula and exact version should be used?
- Do I have enough ingredients, lots, and packaging?
- What expires soon?
- What should I buy?
- What will this cost, which tax applies, and what will I earn?
- What exactly happened in the system?

UI decisions must optimize for confident daily work, traceability, and clear next actions. The interface should reduce cognitive load without hiding warnings, confirmations, or historical meaning.

## Product experience principles

1. **Calm working system.** Use warm cream/off-white surfaces, deep brown navigation and typography, restrained rose-gold or soft copper accents, clear hierarchy, and high contrast.
2. **Human first.** Labels, statuses, errors, and empty states are Russian and understandable to a non-technical user.
3. **Operational truth over decoration.** The page must make stock, recipe, order, production, cost, and warning state easier to understand.
4. **Backend-owned facts.** Critical calculations and operational decisions come from backend APIs/domain services. Frontend may format and explain them, but must not become the source of truth.
5. **No hidden destructive behavior.** Dangerous actions require explicit confirmation and must align with archive, cancel, reverse, or version-based domain behavior.
6. **Traceability.** Historical recipe versions, production facts, stock movements, imports, exports, and audit events must remain understandable and not be visually flattened into generic activity.
7. **Consistency before novelty.** Existing typography, gradients, cards, and rounded elements are not defects by default. Evaluate them by usability, consistency, hierarchy, accessibility, and this contract.

## Information hierarchy

Each screen should present information in this order:

1. **Where am I?** Clear page title and section context.
2. **What is the current state?** Key status, counts, warnings, or readiness summary.
3. **What should I do next?** Primary action and safe secondary actions.
4. **What details support this?** Tables, lists, cards, history, and explanations.
5. **What are the risks?** Expiration, low stock, missing density, recipe total, insufficient materials, import validation, or destructive-action warnings.

Avoid equal-weight blocks competing for attention. Do not hide critical warnings below decorative content.

## Application shell and navigation

The shell must preserve the product as an operational tool:

- Main navigation labels should be Russian and stable: `Главная`, `Рецепты`, `Клиенты`, `Заказы`, `Склад`, `Тара`, `Закупки`, `Производство`, `Отчеты`, `Импорт`, `Настройки`, plus approved supporting sections such as help, demo data, or report documents.
- Navigation should make current location obvious.
- Group related data/settings routes instead of scattering them as unrelated cards.
- Do not expose API route names, table names, internal identifiers, or implementation statuses as primary navigation copy.
- Dashboard must answer daily questions rather than act as a generic KPI showcase.

## Screen composition

A screen should normally include:

- page title and short plain-language description;
- one clear primary action when the route supports mutation;
- critical warnings/status panels near the top;
- main content area using tables, lists, forms, or grouped cards appropriate to the task;
- secondary navigation to related workflows when useful;
- empty/error/loading states in the same visual area where content will appear.

Do not create broad redesigns or unrelated layout changes in a narrow task. Prefer incremental improvements that preserve recognizable routes.

## Forms

Forms are working tools, not technical payload editors.

- Field labels and helper text must be Russian and domain-specific.
- Required fields must be obvious before submission.
- Validation messages must identify the field, the problematic value when safe, the expected format, and the next action.
- Keep sensitive client notes out of debug-like summaries and logs.
- Use appropriate controls for dates, numeric values, statuses, and choices where existing patterns allow.
- Do not ask the user to enter internal IDs. Use names, selectors, statuses, and human-readable references.
- Save/cancel behavior must be explicit. Unsaved destructive or irreversible operations require confirmation.

## Tables and lists

Tables and lists are preferred for operational data that must be compared, sorted, scanned, or audited.

- Use clear column headings and domain units.
- Show status and warning information in words, not only color or icons.
- Keep primary row actions predictable and near the row they affect.
- Avoid exposing database IDs unless they are intentionally user-facing document/order numbers.
- For empty lists, explain why the list is empty and how to create or import data.
- For long or dense lists, preserve readability and keyboard access before adding visual decoration.

## Cards and grouped content

Cards are useful for summaries, grouped actions, warnings, or related workflows. They must not become an unrelated card wall.

- Use cards when they improve scanning or group a complete concept.
- Keep card headings action-oriented and user-readable.
- Avoid multiple equally prominent cards when one workflow is clearly primary.
- Existing rounded cards, gradients, and soft surfaces are acceptable when they support hierarchy and remain consistent.

## Actions

### Primary actions

Primary actions advance the main user goal on the page, such as saving a record, creating a draft, confirming a safe preview, or opening the main workflow. Use only one dominant primary action per area when possible.

### Secondary actions

Secondary actions support navigation, refresh, cancel, preview, or related workflows. They must not compete visually with the primary action.

### Dangerous actions

Dangerous actions include canceling orders, clearing demo data, reversing movements, applying imports, deleting generated files if ever supported, or any action with operational consequences.

- They require explicit Russian confirmation.
- The confirmation must explain what will and will not happen.
- Prefer archive/cancel/reverse/version instead of silent deletion or mutation.
- Never make dangerous actions the default keyboard action without confirmation.

## Loading states

Every route or content region that waits for backend data needs a visible loading state:

- Use Russian copy such as `Загружаем данные…` with context where helpful.
- Preserve layout stability where practical.
- Disable duplicate-submit actions while a mutation is pending.
- Do not show stale success/error state as if it belongs to a new request.

## Empty states

Empty states must explain:

- what is missing;
- why it matters for the workshop;
- the next safe action.

Example direction: `Пока нет партий ингредиентов. Добавьте покупку или импортируйте остатки, чтобы система могла проверить производство и сроки годности.`

## Error states

Errors must be human-readable and actionable.

- Never expose raw stack traces, Python/JavaScript exception names, database errors, SQL, API handler names, or internal IDs.
- Preserve backend-provided structured user messages when available.
- For imports, identify row, column, problematic value, expected format, and suggested fix.
- If no safe recovery is possible in the UI, tell the user what did not happen and which workflow to try again.

## Success feedback

Success feedback should be brief, specific, and tied to the completed action:

- confirm what was saved/created/applied/generated;
- provide the next useful action when appropriate;
- avoid celebratory motion or excessive visual noise;
- do not imply business effects that did not happen.

## Disabled states

Disabled controls must not leave the user guessing.

- Explain why an action is unavailable when the reason is not obvious.
- Prefer inline helper text or a nearby warning panel over silent disabled buttons.
- Do not use disabled styling as the only validation feedback.

## Confirmations

Use confirmations for production, import apply, destructive cleanup, cancellation, reversal, or anything that changes operational history.

A confirmation should state:

- the action being confirmed;
- affected records or workflow in human-readable terms;
- irreversible or audited consequences;
- what will not be changed;
- the safest alternative when relevant.

## Desktop behavior

MVP is desktop-first for MacBook use.

- Prioritize comfortable scanning, keyboard interaction, and clear side-by-side context on desktop widths.
- Avoid cramped forms or hidden critical warnings.
- Dense operational pages may use tables, but must preserve readable labels and units.

## Narrow-screen and mobile-width behavior

The MVP is not a mobile app, but layouts must not block future phone viewing.

- Content must remain reachable without horizontal page scrolling, except intentionally scrollable data tables when unavoidable.
- Navigation and primary actions must remain discoverable.
- Tables may become stacked cards/lists if an existing pattern supports it.
- Confirmations, error messages, and warnings must remain readable at narrow widths.

## Keyboard navigation and visible focus

- Interactive elements must be reachable by keyboard in a logical order.
- Focus must be visible and high-contrast against warm surfaces.
- Dialogs and confirmations must not trap users incorrectly.
- Do not remove outlines unless replacing them with an equally visible focus style.
- Keyboard testing is required for frontend UI changes.

## Accessibility

- Maintain high text contrast, especially for brown text on cream surfaces and copper/rose-gold accents.
- Do not communicate status by color alone.
- Use semantic headings, buttons, links, form labels, and table structure where possible.
- Error and success messages should be associated with the relevant area or control when practical.
- Copy must remain understandable without design-specific knowledge.

## Russian user-facing copy

- User-facing copy should be Russian by default.
- Use domain language the maker understands: recipe, formula, client, order, lot, stock, production, purchase, backup, import, report.
- Avoid developer terms such as `payload`, `endpoint`, `DTO`, `migration`, `stack trace`, `foreign key`, `undefined`, or raw enum names.
- If an English technical term is unavoidable in developer-facing docs, keep it out of the product UI.

## Technical information never exposed to users

Never show the user:

- raw stack traces;
- SQL/database errors;
- API paths or handler names;
- internal database IDs as workflow labels;
- JSON payloads;
- Python/TypeScript exception names;
- environment paths;
- sensitive client notes in logs/debug panels;
- secrets, tokens, or local filesystem internals not needed for backup/export workflows.

## Motion and reduced motion

Motion must be limited and purposeful:

- Use motion only to clarify state changes, not to entertain.
- Avoid repeated attention-grabbing animation on operational screens.
- Respect reduced-motion preferences.
- Motion work should be a separate scope after layout, hierarchy, states, and copy are approved.

## Design-token direction

Do not introduce a new design framework in UI tasks unless explicitly approved.

Token direction should preserve:

- warm cream/off-white page and content surfaces;
- deep brown navigation and primary text;
- restrained rose-gold or soft copper accents;
- high-contrast warnings and errors;
- calm density suitable for desktop work;
- consistent spacing, radius, shadow, and typography based on existing frontend patterns.

Exact pixel values should not be invented in this contract. Use existing frontend tokens and patterns where available.

## Forbidden generic UI patterns

Avoid:

- generic admin panels with technical table dumps;
- SaaS-style vanity dashboards unrelated to daily work;
- e-commerce/product-card metaphors for operational records;
- decorative card grids that obscure workflow priority;
- hidden destructive actions;
- silent auto-normalization of formulas;
- frontend-only critical calculations;
- color-only statuses;
- broad route redesigns in narrow PRs;
- third-party visual identities replacing the approved product identity.

## UI Definition of Done

A UI change is done only when:

- it follows the product, architecture, domain, and UI contracts;
- critical calculations and operational state remain backend-owned;
- Russian user-facing copy is human-readable;
- loading, empty, error, success, and disabled states are handled for changed flows;
- dangerous actions have explicit confirmation;
- keyboard navigation and visible focus are preserved;
- narrow-screen behavior is checked;
- reduced-motion expectations are respected where motion exists;
- no raw technical details or sensitive notes are exposed;
- no unrelated routes are redesigned;
- no dependencies, scripts, hooks, APIs, schemas, migrations, or domain logic are changed unless explicitly in scope.

## Required smoke verification

For frontend, visual, accessibility, responsive, or motion changes, run or document the minimum relevant checks:

- project-required build/type/lint/test command for the touched area;
- desktop smoke of the affected route;
- narrow-screen smoke of the affected route;
- keyboard tab/focus check;
- loading, empty, error, success, and disabled state review for changed flows;
- reduced-motion check for motion changes;
- confirmation copy check for dangerous actions.

If a smoke check cannot be run in the environment, state the limitation clearly in the PR summary.
