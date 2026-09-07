# Project Context Template

This is an optional full skeleton for one project under the canonical
workspace. A minimum bootstrap may start with only `PROJECT.md`,
`.hermes/state.md`, and `AGENTS.md` when repository-local instructions are
needed. Add the remaining navigation layers only when they have current value.

## Map

| Path | Purpose |
|---|---|
| `PROJECT.md` | Stable project identity and entry pointers |
| `AGENTS.md` | Repository-local instructions and source-of-truth boundaries |
| `.hermes/context-kit.json` | Adopted specification, Kit release, profile, and features |
| `.hermes/context-index.md` | Current-first context router |
| `.hermes/state.md` | Project-level current summary |
| `.hermes/checkpoints/README.md` | Explicit current checkpoint pointer |
| `tasks/README.md` | Task index |
| `tasks/current.md` | Primary active Task pointer |
| `docs/decisions/README.md` | ADR index |

Prefer `python3 scripts/context_kit.py init` over copying this directory by
hand. If adapting the example manually, replace all `{{placeholder}}` values
and ensure the profile's feature list is correct. Remove any unused empty
navigation layer before enabling mutations. Do not manufacture a Task, ADR,
Checkpoint, or memory entry merely to fill an empty section.
