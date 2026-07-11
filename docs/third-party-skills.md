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

## Registry entries

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

- Status: reviewed; not approved for installation, vendoring, or copying.
- Skill name: Taste Skill.
- Purpose: reverse-engineer the visual design system and design trade-offs of external websites.
- Source repository: `senlindesign/taste-skill`.
- Reviewed upstream commit: `6dce223f2f5665d3636ca9a44ec3a7aa1322a9b8`.
- Declared skill version: `1.1.0`.
- Review date: 2026-07-11.
- License status: the README claims MIT, but the repository contains no license text or legal file, GitHub does not detect a license, and no legal file exists anywhere in the reviewed Git history.
- Imported files: none.
- Included scripts: none imported.
- Included hooks: none imported.
- Included dependencies or MCP servers: none installed.
- Review record: [`docs/taste-skill-review.md`](taste-skill-review.md).
- Reviewed material: `SKILL.md`, `README.md`, `evals/evals.json`, `references/extract.js`, all Markdown references, repository metadata, and complete Git history for legal-file presence.
- Decision: do not install the upstream skill, do not place it under `.agents/skills`, and do not copy its source or reference text into the project.
- Primary blockers: incomplete licensing evidence; unpinned `@latest` Playwright MCP dependency; external browser automation; broad implicit activation; current-directory output writes; optional mutation or overwrite of AI instruction and tool configuration files.
- Product constraint: external design analysis must not replace the approved identity and human-readable workflow of «Мастерская косметолога».
- Implicit invocation policy: prohibited.
- Approved use cases for the upstream skill: none.
- Project-owned alternative: evidence-based UI audits may be designed independently under the canonical UI/UX contract without copying upstream text or code.
- Revisit conditions: complete license text, pinned dependencies, explicit-only invocation, sandboxed outputs, no mutation of canonical instruction files, and a new security and architecture review.
- Update policy: any reconsideration requires a new pinned-commit review in a separate PR.

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
