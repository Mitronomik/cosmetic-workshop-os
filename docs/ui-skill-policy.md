# UI Skill Policy

This policy defines how project-owned and third-party Codex UI/design skills may be used in **cosmetic-workshop-os**.

## Instruction priority

For frontend, visual, accessibility, responsive, or motion tasks, apply instructions in this order:

1. Project architecture and product documentation, including `AGENTS.md`, `docs/product-spec.md`, `docs/architecture.md`, `docs/domain-model.md`, `docs/frontend-concept.md`, roadmap/state files, and any scoped `AGENTS.md` files.
2. `docs/ui-ux-contract.md`.
3. The project-owned `.agents/skills/cosmetic-workshop-ui/SKILL.md` skill.
4. The explicit Codex task for the current PR.
5. Third-party design skills.

If instructions conflict, the higher-priority source wins. Canonical project documentation always overrides third-party skills.

## Third-party skill boundaries

Third-party skills are advisory and implementation aids only. They cannot:

- override project architecture or product documentation;
- change domain logic;
- change API contracts;
- change database schemas or migrations;
- introduce dependencies without explicit approval;
- add scripts, hooks, or executable automation without explicit approval;
- redesign unrelated routes;
- mutate historical or operational data;
- bypass local-first constraints;
- replace backend ownership of critical calculations;
- remove confirmations, auditability, import preview, production confirmation, or stock-movement safety;
- replace the approved product identity: warm cream/off-white surfaces, deep brown navigation/typography, restrained rose-gold or soft copper accents, calm operational density, high text contrast, and purposeful motion.

Third-party output must be reviewed against `docs/ui-ux-contract.md` before implementation.

## Approved and planned roles

Only the reviewed Impeccable provenance record and project-adapted guidance described below are currently approved. Taste Skill and Emil skills remain planned only and are not installed or vendored.

### Impeccable

Approved role: project-adapted advisory guidance for audit, hierarchy, layout, typography, accessibility, responsive behavior, interaction design, onboarding, hardening, and final polish.

The reviewed source record and project-authored guidance live at `.agents/vendor/impeccable/3.9.1/` and are intentionally outside `.agents/skills/`. Raw upstream command references are not included. The directory is not an independently discoverable skill and has no vendored scripts, hooks, live mode, provider agents, or automatic update behavior.

Use it only after the relevant route and product workflow already exist and only through the project-owned `cosmetic-workshop-ui` skill. Impeccable-derived feedback must separate objective usability issues from taste-based preferences and must not broaden scope without approval.

Generic upstream taste rules do not override the existing project identity. In particular, the approved warm cream/off-white surfaces, deep brown typography and navigation, restrained rose-gold or soft copper accents, rounded operational surfaces, and calm visual density remain valid when used according to `docs/ui-ux-contract.md`.

### Taste Skill

Intended role: explicit-only critique or redesign exploration.

Use only when the task asks for taste critique or redesign exploration. Its output is not automatically approved for implementation and cannot replace the product identity or contract.

### Emil skills

Intended role: motion work only after layout and interaction states are approved.

Use only for a separate motion scope. Motion must remain limited, purposeful, and reduced-motion compatible.

## Installation, vendoring, and review policy

A third-party skill must not be installed into `.agents/skills/`, activated, or updated unless a separate PR explicitly approves that exact mode.

The currently approved Impeccable integration is limited to project-authored adapted guidance and a pinned provenance record under `.agents/vendor/`. It must remain:

- outside `.agents/skills/`;
- free of raw upstream command references;
- non-executable;
- free of hooks and `.codex/hooks.json`;
- free of live-mode files and provider agents;
- free of npm packages and lockfile changes;
- tied to an exact reviewed upstream commit;
- documented with source, license, reviewed scope, restrictions, and checksums.

The project-owned `cosmetic-workshop-ui` skill is the only instruction layer allowed to consult `GUIDANCE.md`.

Taste Skill and Emil skills remain uninstalled and unvendored. Any future third-party addition or Impeccable update requires a separate review PR.
