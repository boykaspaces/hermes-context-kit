---
name: multi-repo-system-management
description: "Use when coordinating Tasks across repositories."
version: 0.1.1
author: Boyka Chen, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [multi-repo, tasks, integration, handoff, version-locking]
    related_skills: [project-context-management]
---

# Multi-Repository System Management

## Purpose

Coordinate one system whose implementation, integration state, and deployment
truth are owned by different repositories. This skill composes with
`project-context-management`; it does not replace that skill's Task statuses,
project-scope guards, Checkpoint rules, or index semantics.

## When to Load

Load this skill when:

- one work goal requires changes or evidence from two or more repositories;
- a component revision must be handed to an integration repository;
- a system Task advances an immutable component lock;
- integration, deployment, acceptance, or rollback spans repository boundaries;
- an agent must continue safely when one participating repository is inaccessible.

Load `project-context-management` first for every project-scoped Task, State,
Checkpoint, ADR, or index mutation.

## When NOT to Load

Do not load this skill for:

- a self-contained change in one repository with no system integration effect;
- ordinary source inspection or local validation;
- reusable Skill authoring itself — use `skill-authoring` after project-context
  classification;
- package dependency graphs that do not create cross-repository work state.

## Core Guards

**Explicit repository roles.** One integration repository owns each System
Task, its component graph, accepted revisions, integration evidence, and
deployment state. Component repositories own their source, tests, component
Tasks, and local documentation.

**No duplicated Task truth.** The System Task links Component Tasks and their
delivery records; it does not copy their progress. A component Task links its
parent System Task; it does not claim integration or deployment success.

**Immutable delivery identity.** A delivered component is identified by its
repository and full commit SHA. Branch names are review routes, not immutable
versions.

**No inaccessible-state claims.** If the integration repository cannot be
read or written, produce a validated Handoff and stop at the boundary. Never
infer that a private Task, lock, deployment, or acceptance result was updated.

**No secret transport.** Tasks, manifests, Handoffs, indexes, and Checkpoints
must not contain credential values or use model-visible files to transport
them.

**Integration is not deployment.** Component completion, merge, lock,
integration verification, and deployment are separate facts.

## Operation Router

| Operation | Load |
|---|---|
| Classify scope and assign repository roles | `references/scope-and-roles.md` |
| Create/update System and Component Tasks; advance delivery state | `references/tasks-and-delivery.md` |
| Transfer work when the integration repository is inaccessible | `references/handoffs.md` |
| Validate a repository, Handoff, System Task, or component lock | `references/validation.md` |

## Lifecycle Summary

1. Resolve every project being mutated and classify the work as Component or
   System scope.
2. Create one System Task in the integration repository only when two or more
   repositories or a deployment boundary are involved.
3. Create a Component Task in each repository that must change, with an
   explicit canonical parent such as `integration-repo:TASK-014`.
4. Complete and validate component work independently; generate a Handoff if
   the integration repository is unavailable.
5. Record reviewed full commit SHAs in the System Task manifest and advance
   the component lock only through the integration repository.
6. Run cross-component acceptance. Record deployment separately when it
   actually occurs.
7. Complete the System Task only when its stated goal and acceptance criteria
   are satisfied; then synchronize Task, State, Checkpoint, and indexes through
   `project-context-management`.

## Failure Handling

If a cross-repository reference is missing, a revision is mutable or malformed,
a lock disagrees with the System Task manifest, or a required repository is
inaccessible, leave the affected delivery state unchanged and report the
operation as Incomplete. Follow `references/validation.md` for the narrowest
repair and rerun the failed check.
