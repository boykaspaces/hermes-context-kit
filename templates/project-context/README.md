# Project Context Template

This is an optional runtime-neutral skeleton for one project. A minimum
bootstrap starts with `PROJECT.md`, `.context-kit/manifest.json`, and
`.context-kit/state.md`. Runtime instruction files are added only by an
explicitly selected adapter.

## Map

| Path | Purpose |
|---|---|
| `PROJECT.md` | Stable project identity and entry pointers |
| `.context-kit/manifest.json` | Adopted specification, Kit release, profile, features, and adapters |
| `.context-kit/index.md` | Current-first context router |
| `.context-kit/state.md` | Project-level current summary |
| `.context-kit/checkpoints/README.md` | Explicit current checkpoint pointer |
| `tasks/README.md` | Task index |
| `tasks/current.md` | Primary active Task pointer |
| `docs/decisions/README.md` | ADR index |

Prefer `python3 scripts/context_kit.py init` over copying this directory by
hand. If adapting the example manually, replace all `{{placeholder}}` values
and ensure the profile's feature list is correct. Remove any unused empty
navigation layer before enabling mutations. Do not manufacture a Task, ADR,
Checkpoint, or memory entry merely to fill an empty section. Select a runtime
adapter when an agent-specific instruction entry point is required.
