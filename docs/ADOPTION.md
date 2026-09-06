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

## Install Skills

Copy the required Skill directory without flattening it:

```text
skills/project-context-management/ -> {{hermes_skill_root}}/project-context-management/
skills/multi-repo-system-management/ -> {{hermes_skill_root}}/multi-repo-system-management/
skills/skill-authoring/             -> {{hermes_skill_root}}/skill-authoring/
```

Install `multi-repo-system-management` only for workspaces that coordinate
more than one repository. It composes with, and does not replace,
`project-context-management`.

Use the Hermes-supported Skill installation or management operation for the
target deployment. Do not assume that a repository checkout is itself the
runtime Skill directory.

## Configure the deployment contract

Adapt [`../templates/SOUL.project-context.example.md`](../templates/SOUL.project-context.example.md)
inside the deployment's operator-owned `SOUL.md`. Replace all placeholders,
then verify that the runtime cannot silently fall back to a container-local or
ephemeral path.

## Bootstrap a project

Copy [`../templates/project-context/`](../templates/project-context/README.md)
into the canonical project root. Replace placeholders and create only the
indexes that provide current navigation value. The template intentionally has
no fabricated active Task, ADR, Checkpoint, or memory entry.

## Validate

Run:

```sh
./scripts/validate.sh
```

Then exercise one happy path and one failure path in the real Hermes runtime:

- happy path: create a Task and confirm its index/current pointer are updated;
- failure path: remove or mismatch the workspace identity and confirm mutation
  is refused without creating a replacement registry.

For multi-repository adoption, also validate one System Task manifest and one
inaccessible-integration-repository Handoff before enabling automated lock or
deployment changes.
