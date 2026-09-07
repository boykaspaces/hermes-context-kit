# Hermes Context Kit

Project ID: hermes-context-kit
Name: Hermes Context Kit
Status: Active

## Goal

Provide reusable, auditable protocols and neutral templates for durable,
index-first Hermes project context and Skill authoring.

## Sources of truth

- `spec/` owns versioned public artifact and state contracts.
- `profiles/` owns coherent adoption requirements.
- `.hermes/context-kit.json` owns this repository's accepted Kit version,
  profile, and enabled features.
- `skills/<name>/SKILL.md` owns each Skill's trigger, guards, and operation
  routing.
- The matching `skills/<name>/references/` file owns detailed protocol rules.
- `templates/` owns neutral bootstrap examples, not runtime state.
- `docs/FILE_MAP.md` routes maintainers to the owning artifact.
- `tasks/` and `.hermes/` own only this public repository's maintenance state.

## Context entry points

| Artifact | Purpose | Read when |
|---|---|---|
| [`.hermes/context-index.md`](./.hermes/context-index.md) | Current-first repository context | Starting or resuming maintenance |
| [`.hermes/state.md`](./.hermes/state.md) | Current repository summary | Asking what work is active |
| [`tasks/current.md`](./tasks/current.md) | Primary active Task pointer | Continuing current repository work |
| [`docs/decisions/README.md`](./docs/decisions/README.md) | Repository decision index | Work depends on a durable local decision |
| [`spec/README.md`](./spec/README.md) | Public specification index | Work changes portable contract semantics |
| [`profiles/README.md`](./profiles/README.md) | Adoption profile index | Bootstrapping or migrating a project |

## Boundaries

- Do not store a consuming user's live `SOUL.md`, state, memory, Tasks,
  Checkpoints, or workspace registry here. Repository-maintenance context must
  remain public and free of deployment-specific data.
- Do not specialize reusable protocols with one deployment's paths or policy
  unless the path is explicitly a placeholder or example.
- Preserve stable Skill names and reference routing when making compatible
  changes.
