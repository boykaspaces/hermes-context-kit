# Context Kit

A versioned, profile-based public protocol and reference implementation for
agent-managed projects. It provides maintained Skills, machine-readable
schemas, neutral templates, deterministic lifecycle tooling, and conformance
fixtures for project identity, state, Tasks, ADRs, recovery, multi-repository
coordination, and reusable Skill authoring.

## Repository map

| Path | Status | Owns | Read when |
|---|---|---|---|
| [`skills/`](./skills/README.md) | Active index | Installable runtime-neutral Skills and routed references | Installing, reviewing, or changing protocol behavior |
| [`adapters/`](./adapters/README.md) | Active index | Runtime and workflow bindings | Integrating a specific agent or delivery system |
| [`templates/`](./templates/README.md) | Current index | Neutral workspace and project-context starting structures | Bootstrapping a deployment or project |
| [`spec/`](./spec/README.md) | Normative index | Versioned portable project and multi-repository contracts | Implementing or reviewing protocol behavior |
| [`profiles/`](./profiles/README.md) | Active definitions | Minimal, repository, and multi-repository adoption requirements | Selecting project complexity |
| [`schemas/`](./schemas/) | Machine-readable contract | Adoption, component-lock, and System Task structures | Building validators or integrations |
| [`docs/`](./docs/README.md) | Current index | Architecture, adoption, security, and file ownership | Understanding or integrating the kit |
| [`.context-kit/index.md`](./.context-kit/index.md) | Current index | This repository's own public maintenance context | Resuming repository maintenance |
| [`tasks/`](./tasks/README.md) | Active index | This repository's development Tasks | Reviewing current or completed maintenance work |
| [`.github/workflows/validate.yml`](./.github/workflows/validate.yml) | Active automation | Read-only GitHub-hosted repository validation | Configuring or auditing required status checks |
| [`PROJECT.md`](./PROJECT.md) | Stable identity | This repository's purpose and source-of-truth boundaries | Starting repository maintenance |
| [`AGENTS.md`](./AGENTS.md) | Active instructions | Repository-wide AI editing and validation rules | Before changing this repository |
| [`LICENSE`](./LICENSE) | Active | MIT license | Reusing or redistributing the kit |

## Quick start

1. Check out an immutable release or reviewed commit.
2. Read [`docs/ADOPTION.md`](./docs/ADOPTION.md) and choose a profile.
3. Preview initialization with `python3 scripts/context_kit.py init ... --dry-run`.
4. Initialize, then run `python3 scripts/context_kit.py validate --root <project>`.
5. Select only the runtime adapters and Skills needed by the consumer.

The repository's own maintenance Tasks are public. It intentionally contains
no consuming deployment's live runtime instructions, project state, credentials,
deployment identifiers, or user-specific context.

## Compatibility

The protocol and CLI require Python 3 and repository-local files only. Common
Skills use portable frontmatter and Markdown references. Runtime instruction
files, Skill paths, global workspaces, and file-tool behavior are supplied by
explicit adapters or the consuming deployment.
