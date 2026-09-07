---
name: project-context-management
description: "Protocol for project state, tasks, ADRs and checkpoints."
license: MIT
metadata:
  context-kit:
    version: 2.0.0
    author: Boyka Chen
    platforms: [linux, macos, windows]
    tags: [project-management, context, persistent-state, routing, protocol]
    related_skills: []
---

# Project Context Management

## Purpose

This skill governs persistent project context operations. Its goal is to preserve the structured state and indexes required to reconstruct working context later — not to preserve the conversation or context window itself.

## When to Load

Load this skill before any of the following operations:

**Project lifecycle:** create · switch · resume · pause · archive · state mutation

**Tasks:** create · update · switch · complete · cancel · reopen

**Decisions:** ADR create · supersede · deprecate · reject

**Checkpoints:** create · resume · archive

**Persistence:** project memory write · index create/update/repair

**Consolidation / Recovery:** context consolidation · progressive context reconstruction · classification of project-derived procedures before global Skill handoff

> If uncertain whether an operation affects persistent project context — default to loading this skill.

## When Not to Load

Do not load this skill merely because work happens inside a project.

It is normally unnecessary for:
- Read-only source-code questions or single-file inspection
- Ordinary explanations or simple code edits
- Ephemeral debugging with no persistence or lifecycle operation
- Reusable Skill content, structure, destination, creation, or validation after project classification — use `skill-authoring`

**Exception:** if any of the above leads to a Task, ADR, Checkpoint, Memory, Project State, Index, Consolidation, or Recovery operation — this skill applies.

## Core Guards

**Explicit state only.** Never infer current project state from file timestamps, modification time, filename ordering, or conversational recency. Follow the global explicit-state rule.

**One primary source of truth per concept.** Do not duplicate stronger sources of truth into Memory or Checkpoints.

**Index consistency.** Any persistent navigation change must leave affected indexes consistent. An operation whose index update failed is Incomplete.

**Minimum sufficient context.** Load only the narrowest reference required. Session history is not project state.

**Unknown project scope write guard.** Never write project-scoped persistent context — Task, ADR, Checkpoint, Memory, Project State, or Index — when the target `project_id` is unresolved or ambiguous. Resolve project scope before any mutation. A read-only cross-project query does not require a project switch.

**Persistent workspace boundary.** Resolve the project root explicitly. When an operation crosses projects, resolve the canonical Workspace identity, Workspace Registry, and project path from the selected runtime adapter's operator-owned binding. Before a persistent read or mutation, verify that the target is accessible through the current file tools. Do not invent an identity marker, silently substitute a user-home or ephemeral path, or create a second registry. If a required binding is absent, ambiguous, or inaccessible, the operation is Incomplete.

**Adoption contract.** When `.context-kit/manifest.json` exists, it owns the
adopted specification version, immutable Kit version, profile, and enabled
features. Do not infer adoption from stray files or silently upgrade the
manifest during an ordinary context mutation.

**Global Skill handoff.** Follow the selected runtime adapter's canonical Skill scope and management mechanism. This skill may classify a project-derived procedure and verify cross-project applicability, but `skill-authoring` owns reusable Skill creation, destination, structure, and validation.

**Protocol Maintenance Candidate.** If execution reveals a suspected missing, ambiguous, conflicting, or unsafe project-context protocol rule that cannot be safely resolved by the current owning reference, treat it as a Protocol Maintenance Candidate. Do not modify the protocol; load `references/MAINTENANCE.md` only for read-only diagnosis and the user-approval maintenance workflow.

**Escalation boundary.** A project-state inconsistency that the current protocol can clearly resolve is not a Protocol Maintenance Candidate; handle it through the owning domain protocol.

## Operation Router

Identify the operation, then load only the matching reference.

| Operation | Load |
|---|---|
| Project create / switch / resume / pause / archive / reactivate / state mutation | `references/project-lifecycle.md` |
| Index create / update / navigation / repair | `references/indexing.md` |
| ADR / decision create / supersede / deprecate / reject | `references/decisions.md` |
| Task create / update / switch / complete / cancel / reopen | `references/tasks.md` |
| Checkpoint create / resume / archive | `references/checkpoints.md` |
| Project memory persistence | `references/memory.md` |
| Context consolidation | `references/consolidation.md` |
| Project-derived procedure classification / global Skill eligibility | `references/consolidation.md`, then hand off to `skill-authoring` |
| Project recovery / progressive loading | `references/recovery.md` |

## Reference Loading

1. Identify the operation type first.
2. Load only the narrowest reference required for that operation.
3. Load additional references only when the operation genuinely crosses multiple context-management domains.
4. A cross-reference such as "follow `references/indexing.md`" indicates protocol ownership — it does not mean that file must be loaded automatically. Load another reference only when the current operation actually requires that domain's detailed procedure.

**Mutation guard.** Before mutating persistent project context: resolve project scope; load the relevant domain reference in the current session; perform the mutation through that protocol; leave affected pointers and indexes consistent. Do not rely on remembered protocol details from previous sessions.
