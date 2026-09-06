# Project Lifecycle Reference

Defines project identity, create/switch/resume/pause/archive lifecycle, workspace registry, and cross-project scope semantics.

---

## Purpose and Scope

**Covered here:** project identity, current project resolution, workspace registry, project status, creation, switch, pause, archive/reactivate, cross-project scope isolation, rename/move, lifecycle consistency.

**Owned elsewhere (ownership pointer only — not automatic load):**
- Detailed context reconstruction → `references/recovery.md`
- Task lifecycle → `references/tasks.md`
- Checkpoint schema → `references/checkpoints.md`
- Index mutation rules → `references/indexing.md`
- Context classification → `references/consolidation.md`

---

## Project Identity

Every persistent project has a stable, unique `project_id`.

```
project_id: stock-assistant    ← stable; assigned once; never changes
Name:       Investment Assistant  ← may change freely
Path:       /workspace/projects/stock-assistant  ← may change; update registry
```

Rules:
- `project_id` is not derived from directory basename or timestamp.
- Display name and path changes do not alter `project_id`.
- Project identity is determined by `project_id`, not by mtime, last session, or recently edited repo.
- If `project_id` migration is required, treat it as a high-impact operation and update all stable references.

**Scope guard:** If `project_id` is unresolved or ambiguous, do not perform project-scoped mutations. Resolve scope first. (Canonical: `SKILL.md` Scope Guard.)

---

## Current Project Resolution

Resolve current project in this priority order. Use the highest-priority signal available; explicit scope overrides implicit evidence.

1. User's current message explicitly names a project
2. Currently activated project scope
3. Managed working directory / repository context
4. `PROJECT.md` declared `project_id`
5. Existing routing/state evidence
6. Conversation context only as last fallback

---

## Workspace Registry

The canonical project routing index for this deployment is `/workspace/.hermes/WORKSPACES.md`.

Registry paths must be absolute, canonical, and accessible through the current file tools. The default root for newly managed projects is `/workspace/projects/<project_id>/`.

The canonical workspace must first be authenticated by `/workspace/.hermes/WORKSPACE_ID` with exact content `hermes-default`. This marker is provisioned by the host deployment or an authorized operator. Sandbox file tools must never create or repair it.

Do not create or fall back to `~/.hermes/WORKSPACES.md`. If the workspace identity is absent or different, or the canonical registry is required but inaccessible, stop the lifecycle mutation and report it as Incomplete.

| Project ID | Name | Path | Status | Active Task |
|---|---|---|---|---|
| stock-assistant | Stock Assistant | /workspace/projects/stock-assistant | Active | TASK-014 |
| old-demo | Old Demo | /workspace/projects/old-demo | Archived | — |

Routing index only — do not copy architecture, decisions, task details, memory, or checkpoint content into it.

**Source-of-truth boundaries:**
- `PROJECT.md` owns `project_id`, name, goal, and project status.
- `/workspace/.hermes/WORKSPACES.md` owns the current routing path and mirrors name, status, and active task for navigation.
- `tasks/current.md` owns the current active task pointer; the registry only mirrors it.
- Avoid recording an absolute project path in `PROJECT.md`; if one exists for compatibility, keep it synchronized until it can be removed safely.

---

## Project Status

| Status | Meaning |
|---|---|
| **Active** | Currently maintained; can be resumed normally |
| **Paused** | Not actively worked on; full resume state preserved |
| **Archived** | Excluded from normal active routing; preserved but not active |

Status must be explicit. Do not infer from file timestamps, mtime, or last session.

---

## Creating a Project

Create a persistent project only when work will:
- Span multiple sessions
- Accumulate long-term state
- Involve a repository or workspace
- Produce multiple tasks or decisions
- Be explicitly identified as a project by the user

Do not auto-create for one-off tasks.

**Creation preflight:**
1. Verify `/workspace/.hermes/WORKSPACE_ID` exists and its exact content is `hermes-default`.
2. Verify `/workspace` is accessible through the current file tools.
3. Verify or create `/workspace/.hermes/WORKSPACES.md` only after the workspace identity matches.
4. Resolve the proposed project root explicitly.
5. Verify the resolved path is inside the authenticated, accessible persistent workspace.
6. If the user specified an exact path, do not silently rewrite it. If it is inaccessible, stop and request an accessible path or mount.

**Creation flow:**
1. Choose stable `project_id` and root path.
2. Check Workspace Registry for duplicate `project_id`, path, or equivalent purpose.
3. Create minimum project manifest: `PROJECT.md`, `.hermes/state.md`, `AGENTS.md` if needed.
4. Register in `WORKSPACES.md`.
5. Add further layers (`tasks/`, `decisions/`, `memory/`, `checkpoints/`) only when navigation value appears.

If a matching project already exists: resume it — do not create a second context set.

---

## PROJECT.md

Project manifest and primary context entry point.

```
Project ID:  <project_id>
Name:        <display name>
Goal:        <one paragraph>
```

Add as complexity grows: architecture pointer, decision index pointer, state pointer, active task pointer. `PROJECT.md` contains pointers — not full state, history, or decision content.

---

## Switching Projects

**Switching projects is a state transition, not a directory change.**

Conceptual model:
```
current scope
  ↓ persist meaningful state if needed
leave current scope
  ↓
resolve and validate target
  ↓
activate target scope
  ↓
invoke Recovery Protocol for context reconstruction
```

**Switch procedure:**
1. Resolve current and target project. If same, see Same-Project Switch.
2. Evaluate whether meaningful current state needs persisting.
3. Persist state / create checkpoint only if it adds resume value — not merely because a switch occurred.
4. Ensure affected current pointers and indexes are consistent.
5. Resolve target through Workspace Registry; validate status and path.
6. Activate target project scope.
7. Use `references/recovery.md` for detailed context reconstruction of the target.

For checkpoint creation decisions, use `references/checkpoints.md` when that domain's procedure is actually needed.

### Same-Project Switch

If the target `project_id` equals the current active project — confirm scope and continue. Do not re-checkpoint, re-reload, or rebuild context unless the user explicitly requests it.

---

## Leaving a Project

Before leaving, determine whether meaningful state exists to persist:

**Persist when:**
- Active task progress changed
- New blocker or next action identified
- Working files changed
- Durable decision was made
- Context contains resume-critical information

**Skip when:**
- No state changed since last save
- Purely exploratory with no durable output

> Do not checkpoint merely because a switch occurred.

**Never auto-commit, reset, discard, or clean dirty working state** as part of a project switch. If the project has uncommitted changes, failing tests, or known broken state — record it honestly in state or checkpoint before leaving.

---

## Activating and Resuming a Project

When the target scope becomes active, invoke the Recovery Protocol to reconstruct context:

```
activate target scope → use references/recovery.md
```

**Key guarantees this reference owns:**
- Resume must start from persistent Project Context, not old conversation.
- Old sessions are fallback evidence, not the primary resume source.
- An Active project with no active task is a valid state — do not auto-resume a Completed task.
- Project context must be recoverable after a new session, model change, context compression, or agent restart.
- If project context requires yesterday's conversation to reconstruct — persistence is incomplete.

For the detailed progressive loading ladder, follow `references/recovery.md`.

---

## Pausing a Project

1. Persist meaningful current state.
2. Create/update checkpoint only if it adds resume value.
3. Set `Status: Paused` in `PROJECT.md`.
4. Update `WORKSPACES.md`.
5. Preserve active task pointer unless intentionally cleared.

Paused ≠ Completed or Archived. The project remains valid and resumable.

---

## Archive and Reactivate

**Archiving:**
1. Save meaningful final state.
2. Set `Status: Archived` in `PROJECT.md` and `WORKSPACES.md`.
3. Exclude from normal active project routing.
4. Preserve all project files, tasks, decisions, and history — archive means exclude from active retrieval, not delete.

**Archived projects** must not be auto-selected during normal project routing or "continue project" requests. Load only when the user explicitly names the archived project, historical investigation requires it, or a cross-project reference explicitly needs it.

**Reactivation:** Set `Status: Active` and update `WORKSPACES.md` only when the user explicitly intends to resume development. Reading an archived project's history does not automatically reactivate it.

---

## Cross-Project Scope

The model must enforce project isolation explicitly.

When current project is `stock-assistant`:
- **Use:** global context + `stock-assistant` project context
- **Do not use by default:** other projects' task state, decisions, memory, or skills

Cross-project reference is permitted only when the user explicitly requests it or the current task explicitly requires it. Facts from another project must not automatically become facts of the current project.

**Cross-project read is not a project switch.** After a switch, treat prior project conversation as previous working context — not as current project truth. Target project files and state take priority.

---

## Rename and Move

**Display name change:** update `name` in `PROJECT.md` and `WORKSPACES.md`. `project_id` unchanged. No new project, no ADR/Task ID namespace change.

**Path change:** update `path` in `WORKSPACES.md` and `PROJECT.md` if it records an absolute path. Update relevant routing pointers. `project_id` unchanged — path change is not a new project.

---

## Lifecycle Consistency

Any lifecycle mutation that changes project status, path, active task pointer, or routing must leave affected indexes and registry entries consistent.

After a lifecycle mutation, re-read the affected manifest, registry entry, and current pointer through the same runtime file tools. If any required write is missing, inaccessible, or inconsistent, the mutation is Incomplete. Do not report success until the smallest affected state has been repaired and revalidated.

| Change | Update |
|---|---|
| Status change | `PROJECT.md`, `WORKSPACES.md` |
| Path moved | `WORKSPACES.md`, `PROJECT.md` |
| Active task changed | task index / `tasks/current.md`, `context-index` if it exposes active task |
| Project archived | `WORKSPACES.md` |

If a broken pointer, invalid path, status conflict, or ambiguous scope is discovered during a lifecycle operation:
- Identify the smallest affected scope.
- Verify the authoritative source of truth.
- Repair minimal routing/state.
- Do not reconstruct from old sessions as the primary source.

Detailed index mutation rules are owned by `references/indexing.md`.

---

## Domain Invariants

- **Project identity is the stable `project_id` — not its name or path.**
- **Switching projects is a scope/state transition, not a directory change.**
- **A project may be Active with no active task; this is a valid state.**
- **Archived projects are excluded from normal active routing but preserved in full.**
- **Cross-project read does not implicitly switch or adopt another project's state.**
- **Project context must be recoverable independently of old sessions.**
