# Third-Party Codex Skills Registry

This registry tracks third-party Codex skills and reviewed reference material considered for **cosmetic-workshop-os**.

Project-adapted guidance stored outside `.agents/skills/` is not an installed or independently discoverable Codex skill. Before any third-party content is installed, activated, or vendored, a separate PR must review source, license, scripts, hooks, invocation behavior, and compatibility with `docs/ui-skill-policy.md` and `docs/ui-ux-contract.md`.

## Required registry fields for every future skill

- Skill name
- Purpose
- Source repository
- Imported version or commit SHA
- Import date
- License
- Included scripts
- Included hooks
- Reviewed files
- Local modifications
- Implicit invocation policy
- Approved use cases
- Forbidden use cases
- Update policy

## Planned entries

### Impeccable

- Status: approved project-adapted guidance and provenance record; not installed as an active Codex skill
- Skill name: Impeccable
- Purpose: advisory material for UI audit, hierarchy, layout, typography, accessibility, responsive behavior, hardening, onboarding, and final polish.
- Source repository: `https://github.com/pbakaus/impeccable`
- npm CLI version reviewed: `3.2.1`
- Embedded upstream skill version: `3.9.1`
- Imported commit SHA: `0d1c34e9d0fcfff1070c7210cd808eda504105d7`
- Import date: `2026-07-11`
- Vendored location: `.agents/vendor/impeccable/3.9.1/`
- License: Apache-2.0
- Upstream notice: `NOTICE.md` reviewed and not vendored because it applies only to excluded `ios.md` and `android.md` platform reference files.
- Included upstream reference files: none
- Included scripts: none
- Included hooks: none
- Included provider agents: none
- Reviewed files: npm metadata; CLI download, target, copy, update, and hook logic; upstream `SKILL.md`; selected upstream reference files; executable and file-mutation risk markers.
- Local modifications: raw upstream instructions were excluded after review. `GUIDANCE.md` is a project-authored safe adaptation; `UPSTREAM.md` and `SHA256SUMS` record provenance and integrity.
- Implicit invocation policy: none. Only project-authored `GUIDANCE.md` may be consulted through the project-owned `cosmetic-workshop-ui` skill for an applicable, explicitly scoped UI task.
- Approved use cases: evidence-based audits, accessibility and responsive review, interaction review, hierarchy and typography guidance, onboarding review, hardening, and polish of approved routes.
- Forbidden use cases: activating the upstream skill; running upstream scripts; enabling hooks, live mode, update checks, `impeccable init`, or `impeccable document`; generating competing `PRODUCT.md` or `DESIGN.md`; changing architecture, domain logic, APIs, schemas, migrations, dependencies, unrelated routes, historical or operational data, or the approved product identity.
- Update policy: update only in a separate PR pinned to an exact upstream commit, with renewed source, license, script, hook, behavior, file-list, and checksum review.

### Taste Skill

- Status: not installed
- Skill name: Taste Skill
- Purpose: explicit-only critique or redesign exploration.
- Source repository: TBD
- Imported version or commit SHA: not imported
- Import date: not imported
- License: TBD before installation
- Included scripts: none installed
- Included hooks: none installed
- Reviewed files: none yet
- Local modifications: none
- Implicit invocation policy: none unless explicitly requested by a task.
- Approved use cases: future design critique or exploratory redesign reports when explicitly scoped.
- Forbidden use cases: automatic redesign, replacing the approved product identity, changing unrelated routes, adding dependencies, or altering product/domain/architecture contracts.
- Update policy: install/update only in explicit separate PR with review.

### Emil design skills

- Status: not installed
- Skill name: Emil design skills
- Purpose: motion design support after layout and interaction states are approved.
- Source repository: TBD
- Imported version or commit SHA: not imported
- Import date: not imported
- License: TBD before installation
- Included scripts: none installed
- Included hooks: none installed
- Reviewed files: none yet
- Local modifications: none
- Implicit invocation policy: none unless explicitly requested by a motion task.
- Approved use cases: future limited, purposeful motion work with reduced-motion support after UI states are approved.
- Forbidden use cases: layout redesign before approval, decorative animation on operational screens, ignoring reduced motion, dependency additions without approval, or changes to domain/API/schema behavior.
- Update policy: install/update only in explicit separate PR with review.
