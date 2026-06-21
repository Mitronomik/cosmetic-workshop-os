# scripts/AGENTS.md

Scope: scripts under `scripts/`.

Script rules:

- Scripts must be safe, explicit and reviewable.
- Do not run destructive commands without clear confirmation or an explicit developer-only contract.
- Do not assume real user data paths; use temporary or configured test paths for checks.
- Scripts must not require user-mode users to use terminal.
- Scripts are for developer, build, packaging, backup/restore or release support unless explicitly scoped otherwise.
- Prefer clear output and actionable failure messages.
- Do not embed secrets, credentials or machine-specific private paths.
