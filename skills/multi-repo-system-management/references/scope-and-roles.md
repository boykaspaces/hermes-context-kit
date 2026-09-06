# Scope and Repository Roles

## Scope Classifier

Classify the work before creating or mutating a Task.

| Question | Result |
|---|---|
| Can the goal be completed and accepted entirely inside one repository? | Component scope |
| Must two or more repositories change or be versioned together? | System scope |
| Does the goal change an environment, component lock, rollout, or rollback? | System scope |
| Is another repository merely informational and unchanged? | Component scope unless system acceptance depends on it |

A local change does not become System scope merely because the repository is
part of a larger product. Conversely, a one-line lock or deployment change is
System scope because it changes the assembled system.

## Roles

### Integration repository

Exactly one repository owns a System Task. It owns:

- the System Task Markdown file and current status;
- the machine-readable System Task manifest;
- reviewed immutable component revisions;
- integration and deployment evidence;
- production/private bindings and rollback records when applicable.

The integration repository may be private. Public components must not depend
on reading it in order to build or validate themselves.

### Component repository

A component repository owns:

- reusable implementation and configuration;
- component-local tests and documentation;
- its Component Task and repository-maintenance context;
- a Handoff describing a completed review candidate when direct integration
  access is unavailable.

It does not own claims that the complete system was integrated or deployed.

### Context/protocol repository

A protocol repository is a Component repository when its Skill or template is
changed. Runtime copies and deployment-specific behavioral context remain
owned by the consuming deployment or integration repository.

## Dependency Direction

```text
component repositories
        |
        | immutable revisions + validated Handoffs
        v
integration repository
        |
        | lock + environment bindings + acceptance
        v
deployed system
```

The integration repository depends on components. Public components never
require a private integration repository to compile, test, or explain their
generic behavior.

## Canonical Identities

Use:

- project identity: the explicit `Project ID:` from `PROJECT.md`;
- Task identity: `<project-id>:TASK-NNN` across repositories;
- source identity: canonical repository URL plus a 40-character commit SHA;
- system identity: explicit stable `system_id` in the System Task manifest.

Do not infer identities from directory names, Git remotes, timestamps, or the
largest Task number.

## Repository Access Boundary

Before a cross-repository mutation:

1. Resolve the target project identity through its project context.
2. Confirm the repository is accessible through the approved file tools.
3. Read its current pointer and the exact Task being changed.
4. Mutate only repositories explicitly in scope for the work.

If step 1–3 cannot be completed, do not create substitute state in another
repository. Follow `handoffs.md` instead.
