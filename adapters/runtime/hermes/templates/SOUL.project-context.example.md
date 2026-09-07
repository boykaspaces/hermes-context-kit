# Context Kit Deployment Contract Example for Hermes

This fragment is intended for adaptation inside an operator-owned Hermes
`SOUL.md`. It is not a complete `SOUL.md` and is not part of the portable
Context Kit core.

## Persistent workspace boundary

Persistent project-context files are managed through
`{{canonical_workspace_root}}`.

- Workspace identity file: `{{canonical_workspace_root}}/{{identity_file}}`
- Required identity value: `{{workspace_id}}`
- Workspace registry: `{{canonical_workspace_root}}/{{workspace_registry}}`
- Default project root: `{{canonical_workspace_root}}/projects/{{project_id}}/`

Before a persistent cross-project read or mutation, verify that the identity
file exists, contains the configured identity, and is accessible through the
approved file tools. The identity marker is provisioned only by the host or an
authorized operator. Do not create it, silently substitute a home directory or
ephemeral path, or create a second registry.

Global Skill operations use `{{approved_skill_management_mechanism}}` and the
runtime Skill root `{{runtime_skill_root}}`. Repository-local project-context
operations remain inside the explicitly resolved project root.

Load `project-context-management` before creating, switching, resuming, or
mutating project state, Tasks, ADRs, Checkpoints, project memory, or indexes.
Use index-first progressive retrieval and update every affected pointer when a
navigation relationship changes.
