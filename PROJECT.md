# Hermes Context Kit

Project ID: hermes-context-kit
Name: Hermes Context Kit
Status: Active

## Goal

Provide reusable, auditable protocols and neutral templates for durable,
index-first Hermes project context and Skill authoring.

## Sources of truth

- `skills/<name>/SKILL.md` owns each Skill's trigger, guards, and operation
  routing.
- The matching `skills/<name>/references/` file owns detailed protocol rules.
- `templates/` owns neutral bootstrap examples, not runtime state.
- `docs/FILE_MAP.md` routes maintainers to the owning artifact.

## Boundaries

- Do not store a user's live `SOUL.md`, state, memory, Tasks, Checkpoints, or
  workspace registry here.
- Do not specialize reusable protocols with one deployment's paths or policy
  unless the path is explicitly a placeholder or example.
- Preserve stable Skill names and reference routing when making compatible
  changes.
