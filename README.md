# Hermes Context Kit

Reusable, index-first context protocols for Hermes agents. This repository
contains the maintained Skill sources and neutral templates required to manage
project identity, state, Tasks, ADRs, Checkpoints, memory, indexes, recovery,
and reusable Skill authoring without relying on conversation history.

## Repository map

| Path | Status | Owns | Read when |
|---|---|---|---|
| [`skills/`](./skills/README.md) | Active index | Installable Hermes Skills and their routed references | Installing, reviewing, or changing protocol behavior |
| [`templates/`](./templates/README.md) | Current index | Neutral workspace and project-context starting structures | Bootstrapping a deployment or project |
| [`docs/`](./docs/README.md) | Current index | Architecture, adoption, security, and file ownership | Understanding or integrating the kit |
| [`.hermes/context-index.md`](./.hermes/context-index.md) | Current index | This repository's own public maintenance context | Resuming repository maintenance |
| [`tasks/`](./tasks/README.md) | Active index | This repository's development Tasks | Reviewing current or completed maintenance work |
| [`.github/workflows/validate.yml`](./.github/workflows/validate.yml) | Active automation | Read-only GitHub-hosted repository validation | Configuring or auditing required status checks |
| [`PROJECT.md`](./PROJECT.md) | Stable identity | This repository's purpose and source-of-truth boundaries | Starting repository maintenance |
| [`AGENTS.md`](./AGENTS.md) | Active instructions | Repository-wide AI editing and validation rules | Before changing this repository |
| [`LICENSE`](./LICENSE) | Active | MIT license | Reusing or redistributing the kit |

## Quick start

1. Read [`docs/ADOPTION.md`](./docs/ADOPTION.md).
2. Install only the required directories from `skills/` into the deployment's
   Hermes Skill root.
3. Define the deployment's canonical workspace identity and registry in its
   operator-owned `SOUL.md`; use
   [`templates/SOUL.project-context.example.md`](./templates/SOUL.project-context.example.md)
   as a placeholder-based example.
4. Bootstrap a project from [`templates/project-context/`](./templates/project-context/README.md).
5. Replace every `{{placeholder}}` before enabling persistent mutations.

The repository's own maintenance Tasks are public. It intentionally contains
no consuming deployment's live `SOUL.md`, project state, credentials,
deployment identifiers, or user-specific context.

## Compatibility

The Skills use Hermes Skill metadata and Markdown references. Deployment paths
and file-tool behavior are supplied by the consuming Hermes instance, not by
this repository.
