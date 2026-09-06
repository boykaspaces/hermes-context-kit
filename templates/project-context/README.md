# Project Context Template

This is a neutral skeleton for one project under the canonical workspace.

## Map

| Path | Purpose |
|---|---|
| `PROJECT.md` | Stable project identity and entry pointers |
| `AGENTS.md` | Repository-local instructions and source-of-truth boundaries |
| `.hermes/context-index.md` | Current-first context router |
| `.hermes/state.md` | Project-level current summary |
| `.hermes/checkpoints/README.md` | Explicit current checkpoint pointer |
| `tasks/README.md` | Task index |
| `tasks/current.md` | Primary active Task pointer |
| `docs/decisions/README.md` | ADR index |

Replace all `{{placeholder}}` values. Do not manufacture a Task, ADR, or
Checkpoint merely to fill an empty section.
