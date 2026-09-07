# Adoption Guide

## Prerequisites

The consuming Hermes deployment must provide:

- a persistent workspace root visible to the agent's generic file tools;
- an operator-provisioned workspace identity marker;
- a canonical workspace registry with absolute project paths;
- a global `SOUL.md` that defines those paths and forbids the agent from
  creating substitute identities or registries;
- a global Skill directory managed through the deployment's approved Skill
  mechanism.

Do not enable project-context mutations until the identity marker, registry,
and file-tool visibility have been verified together.

## Install or update Skills

The repository checkout is the source; it is not the runtime Skill directory.
Preserve each Skill directory without flattening it:

```text
skills/project-context-management/     -> {{hermes_skill_root}}/project-context-management/
skills/multi-repo-system-management/   -> {{hermes_skill_root}}/multi-repo-system-management/
skills/skill-authoring/                 -> {{hermes_skill_root}}/skill-authoring/
```

Install `multi-repo-system-management` only for workspaces that coordinate
more than one repository. It composes with, and does not replace,
`project-context-management`.

Use this controlled workflow for both first installation and upgrades:

1. Check out an explicit repository commit and run `./scripts/validate.sh`.
2. Inspect the currently installed copy with `skill_view(name="<skill-name>")`.
3. Before replacing an existing Skill, make a timestamped backup outside the
   repository checkout and record the source commit and installed Skill version.
4. Compare the source and Runtime Skill inventories. Submit the complete Skill
   through one deployment-approved `skill_manage` batch: replace every current
   file and include an explicit `remove_file` operation for every obsolete
   Runtime `references/`, `templates/`, `scripts/`, or `assets/` file absent from
   the incoming source. An upgrade is Incomplete while stale Runtime files remain.
5. If Skill write approval is enabled, inspect the exact pending diff and approve
   that pending ID through the runtime `/skills` approval flow. A chat message
   saying "approve" does not apply a runtime pending write. Repeated submissions
   create independent pending entries; approve or reject each obsolete entry
   explicitly.
6. Re-read the installed Skill with `skill_view`, confirm its version and linked
   files, and exercise one happy path and one failure path.
7. Keep the backup until the updated Runtime Skill has operated successfully.
   Rollback through one approved batch that restores every backed-up file and
   removes every Runtime file absent from the backup; then verify the restored
   version and linked-file inventory with `skill_view`.

Do not copy Skills into a project root, infer a runtime destination from the
current container's home directory, or treat repository validation as proof
that the host-side Runtime Skill was updated.

## Configure the deployment contract

Adapt [`../templates/SOUL.project-context.example.md`](../templates/SOUL.project-context.example.md)
inside the deployment's operator-owned `SOUL.md`. Replace all placeholders,
then verify that the runtime cannot silently fall back to a container-local or
ephemeral path.

The multi-repository routing sentence in the template is intentionally brief.
Do not copy the complete multi-repository protocol into `SOUL.md`; the Skill
remains the canonical owner of those procedures.

## Bootstrap a project

Choose one of two bootstrap modes:

- **Minimum:** create `PROJECT.md`, `.hermes/state.md`, and `AGENTS.md` only when
  repository-local instructions are needed. Add Task, ADR, Checkpoint, memory,
  and context indexes only when they provide current navigation value.
- **Full skeleton:** copy
  [`../templates/project-context/`](../templates/project-context/README.md),
  replace every placeholder, and remove any unused empty navigation layer before
  enabling mutations.

The full skeleton is a convenience layout, not a requirement to pre-create
every index. Never manufacture an active Task, ADR, Checkpoint, or memory entry
merely to populate the template.

## Validate

Run:

```sh
./scripts/validate.sh
```

Then exercise one happy path and one failure path in the real Hermes runtime:

- happy path: create a Task and confirm its index/current pointer are updated;
- failure path: remove or mismatch the workspace identity and confirm mutation
  is refused without creating a replacement registry.

For multi-repository adoption, also validate one System Task manifest, its
component lock, and one inaccessible-integration-repository Handoff before
enabling automated lock or deployment changes. Confirm that verified/deployed
integration is rejected while any included component remains below the required
delivery state.
