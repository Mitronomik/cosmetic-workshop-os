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

## Intended future roles

These roles describe planned future use only. Installation and vendoring are out of scope until a separate PR explicitly approves them.

### Impeccable

Intended role: audit, hierarchy, layout, typography, accessibility, responsive behavior, hardening, and final polish.

Use after the relevant route and product workflow already exist. Impeccable-style feedback must separate objective usability issues from taste-based preferences and must not broaden scope without approval.

### Taste Skill

Intended role: explicit-only critique or redesign exploration.

Use only when the task asks for taste critique or redesign exploration. Its output is not automatically approved for implementation and cannot replace the product identity or contract.

### Emil skills

Intended role: motion work only after layout and interaction states are approved.

Use only for a separate motion scope. Motion must remain limited, purposeful, and reduced-motion compatible.

## Installation and review policy

Third-party installation, version pinning, script review, hook review, license review, local modifications, and vendoring will happen in a separate PR. Until then:

- do not install third-party skills;
- do not copy third-party skill content into this repository;
- do not add `.codex/hooks.json`;
- do not add skill scripts, hooks, npm packages, or lockfile changes;
- document planned skills only in `docs/third-party-skills.md`.
