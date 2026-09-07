# Recovery Reference

Defines session-independent project recovery, progressive context reconstruction, loading order, stop conditions, validation, and historical fallback.

---

## Purpose and Scope

**Covered here:** recovery entry, progressive loading ladder, query-specific depth, current-state reconstruction, working-set reconstruction, stop condition, validation, broken/stale/conflicting state handling, historical fallback, session-independent resume, cross-project read semantics.

**Owned elsewhere (ownership pointer — not automatic load):**
- Project selection / activation → `references/project-lifecycle.md`
- Task mutation → `references/tasks.md`
- ADR mutation → `references/decisions.md`
- Checkpoint creation → `references/checkpoints.md`
- Memory write → `references/memory.md`
- Index repair details → `references/indexing.md`
- Persistent write-back / classification → `references/consolidation.md`

---

## Recovery Model

> Reconstruct the minimum sufficient current working context required to safely continue work.

```
Persistent Project State
  + Active Task
  + Relevant Decisions
  + Relevant Working Files
  + optional Checkpoint
  + on-demand Memory / Docs
= Working Context
```

**Recovery must be session-independent.** The project must be recoverable after a new session, different model, agent restart, or long interruption. Old sessions are fallback evidence — not the primary source.

If recovering a project requires "I remember from yesterday's conversation..." — persistent context is incomplete.

---

## Resolve and Enter Project

Project scope is resolved by `references/project-lifecycle.md`. Recovery begins once scope is known.

If a Workspace Registry is needed:
- For cross-project recovery, resolve and read the canonical Workspace Registry
  supplied by the selected runtime adapter's operator-owned binding.
- Resolve the target by exact `project_id` or an unambiguous registered name.
- Validate that the registered path is accessible through the current file tools.
- Validate the project is Active or Paused (Archived must not silently become Active).
- Do not guess another path or consult a second registry when resolution fails.

Then load: `PROJECT.md` + active runtime-adapter instructions +
`.context-kit/index.md` if present.

**PROJECT.md missing guard:** If `PROJECT.md` is absent, do not reconstruct project truth from old sessions. Use existing managed index/state evidence to determine whether this is an established persistent project. Create or repair `PROJECT.md` only when necessary through the appropriate lifecycle/index protocol.

---

## Progressive Loading Ladder

Not every recovery traverses every level. **Stop as soon as sufficient context exists.**

```
Level 0  Workspace routing (if project_id / path not already known)
Level 1  PROJECT.md + project instructions + context-index
Level 2  Current project state (state.md)
Level 3  Active task (tasks/current.md → task file)
Level 4  Directly relevant Active decisions
Level 5  Relevant working files
Level 6  Latest checkpoint (only if needed)
Level 7  Project memory (on demand)
Level 8  Project documentation / supporting knowledge
Level 9  Historical artifacts / old sessions (last resort)
```

Do not preload unrelated ADRs, memories, archives, history, or repository-wide content.

---

## Bootstrap Current State

Minimum bootstrap (Level 1–3) should answer:

- What project is this?
- What is its goal?
- What is currently active?
- What task is active?
- Where should I look next?
- What project-specific rules apply?

Target size: ~1K–3K tokens where practical.

---

## Active Task

```
tasks/current.md → active TASK file
```

If `current.md` pointer is valid, the full Task Index is usually not needed.

**Guards:**
- No Active Task is a valid recovered state. Do not auto-select a Completed or Cancelled task.
- A Blocked task remains Blocked unless the blocker is confirmed resolved.
- `tasks/current.md` is the canonical active-task pointer. If it names an existing In Progress or Blocked Task, use it and repair stale mirrors such as `state.md`.
- If `tasks/current.md` is missing or invalid and exactly one explicit current-task candidate can be established from valid project artifacts, repair the pointer to that Task.
- If `tasks/current.md` is missing or invalid and multiple plausible candidates remain, stop before Task mutation and ask the user to identify the current Task. Never resolve the conflict by mtime, Task ID magnitude, or conversational recency.

Task mutation and lifecycle details are owned by `references/tasks.md`.

---

## Relevant Decisions

Load decision content only when the current task, state, or working files actually require it.

```
Task: Related Decisions list → Decision Index → specific Active ADR
```

Superseded, Rejected, and Deprecated ADRs load only when:
- Rationale requires historical context
- Migration or conflict investigation is needed
- Regression analysis requires it

For ADR mutation and status rules, follow `references/decisions.md`.

---

## Working Set

Start from Relevant Files listed in the current Task or latest checkpoint. Do not scan the entire repository to rediscover the working set.

The repository is implementation truth. If persistent state and implementation obviously conflict — surface the inconsistency; verify; repair through the owning protocol. Do not silently trust the stale source.

### Git Ref Currency Guard

Project context read from a Git repository describes only the ref and worktree
from which it was read. Before reporting whole-project current status, identify
the checked-out branch, HEAD, and dirty state. Inspect other local worktrees or
refs only when a currency signal exists: the user reports a later or different
state, the checkout is dirty, a recorded branch/SHA disagrees with the checkout,
or the active work uses a review branch or immutable candidate.

Use branch and worktree metadata only to locate plausible refs, then read their
explicit Task, State, checkpoint, or System Task artifacts from those refs
through a non-mutating mechanism such as `git show`. Never infer currency or
completion from a branch name, commit date, ref ordering, or Git log alone; do
not checkout, reset, or clean merely to answer a status question. Report
branch-scoped facts separately when they differ, such as checked-out state,
candidate state, and merged or locked state.

---

## Optional Checkpoint

Load `latest.md` only when:
- Task and State files alone are insufficient for exact resume
- Dirty, unvalidated, or broken working state matters
- User explicitly requests resuming from the last save point

```
Checkpoint Index → latest.md
```

Do not load `archive/`.

**Checkpoint is an optional accelerator, not mandatory recovery storage.** If Task + State + Relevant Files are sufficient — skip checkpoint.

For checkpoint creation and format, follow `references/checkpoints.md`.

---

## Supporting Knowledge

**Memory** — load only when current task/question specifically requires a project-specific fact or lesson:
```
Memory Index → relevant Active entry
```

**Documentation** — navigate through index:
```
docs/README.md → relevant document
```

Do not load all Memory or all docs. Memory must not override current Task, ADR, or State — it is supporting knowledge, not an override layer.

---

## Stop Condition

**When the model knows:**
- Project scope and goal
- Current task / status
- Relevant constraints (active ADRs, project rules)
- Next action
- Relevant working files

**→ STOP LOADING. Start working.**

Do not continue loading because more files exist. Sufficient context is the stopping criterion.

---

## Query-Specific Recovery

Recovery depth is determined by the request — not by the full ladder.

**Current status question:**
```
PROJECT.md → state.md → current task
→ Git ref currency guard (when Git-backed) → STOP
```

**Continue implementation:**
```
state.md → current task → relevant files
→ relevant ADR/checkpoint only if needed → STOP
```

**Historical or decision question:**
```
relevant index → specific historical pointer → specific artifact → STOP
```

For simple requests, stop earlier. Do not mechanically run the full ladder.

---

## Validation and Repair

Validate only the current recovery path — not the entire project.

Check:
- Project identity and status are valid
- Active task pointer is valid and task status is compatible with the request
- Referenced files exist
- Required Active ADRs are not Superseded
- Checkpoint is not stale (if loaded)
- Indexes are not obviously contradictory

**Broken pointer:** follow the nearest valid layer index. Do not guess by filename or mtime.

**Stale index:** verify the current owner artifact, repair the minimal pointer/index, then continue.

**State/current-task conflict:** treat a valid `tasks/current.md` as authoritative and repair stale mirrors. If that pointer is missing or invalid and multiple plausible candidates remain, stop before mutation and ask the user. Do not resolve by mtime, Task ID magnitude, or conversational recency.

Index repair details are owned by `references/indexing.md`.

---

## Recovery Failures

| Category | Meaning |
|---|---|
| **Missing** | Required artifact does not exist |
| **Stale** | Artifact exists but no longer represents current state |
| **Conflicting** | Multiple current sources contradict each other |
| **Corrupt** | Format or references cannot be reliably parsed |
| **Insufficient** | Persistent state exists but is not enough to safely resume |

**Standard repair flow:**
```
detect broken layer
  ↓
limit to smallest affected scope
  ↓
verify authoritative / current source
  ↓
minimal repair if appropriate
  ↓
resume indexed recovery
```

Only when persistent state is genuinely **Insufficient** — proceed to Historical Fallback.

Do not treat all failures as "search old sessions."

**Missing index** is not automatically an error. A small project with only `PROJECT.md` + `state.md` is valid. Create an index only when multiple candidate artifacts produce a navigation need.

---

## Historical Fallback

Historical layer (Level 9) includes: completed tasks, superseded ADRs, checkpoint archive, deprecated memory, history docs, Git history, old sessions.

Load only when current layers (Level 0–8) cannot resolve what is needed.

```
identify the specific missing information
  ↓
choose the narrowest relevant historical source
  ↓
read specific artifact
  ↓
stop when resolved
```

Old sessions are the last resort — not bootstrap. For time-sensitive external facts (API behavior, vendor limits, pricing): re-verify from the current external source rather than trusting old Memory or sessions.

---

## Cross-Project Read

When recovery requires reading another project:

```
current project remains active
  ↓
resolve other project via WORKSPACES.md
  ↓
follow its index to the narrow relevant artifact
  ↓
read only what is needed
```

Cross-project read does not imply a project switch, adoption of other-project facts, or writing to other-project context. Project scope management is owned by `references/project-lifecycle.md`.

---

## Standard Recovery Algorithm

```
resolve / validate project scope (project-lifecycle.md)
  ↓
PROJECT.md + instructions + context-index  [Level 1]
  ↓
current state  [Level 2]
  ↓
active task  [Level 3]
  ↓
relevant Active decisions / decision index  [Level 4]
  ↓
relevant working files  [Level 5]
  ↓
latest checkpoint if needed  [Level 6]
  ↓
memory / docs if needed  [Level 7–8]
  ↓
validate coherent context
  ↓
STOP when sufficient
  ↓
historical fallback only if unresolved  [Level 9]
```

Recovery vs Consolidation:

| | Direction | Nature |
|---|---|---|
| **Recovery** | Persistent State → Working Context | Read / reconstruct |
| **Consolidation** | Working Context → Persistent State | Classify / write |

Recovery is read-first. Perform only minimal repair required to restore a coherent current path. Real write-back belongs to the owning protocol or `references/consolidation.md`.

---

## Domain Invariants

- **Recover state, not conversation.**
- **Recovery follows progressive current-state loading and stops when sufficient context exists.**
- **Historical artifacts and old sessions are last-resort fallback, not bootstrap.**
- **Checkpoint and Memory are optional supporting layers, not mandatory recovery content.**
- **No Active Task is a valid recovered state.**
- **Cross-project read does not switch the active project or adopt other-project facts.**
- **Recovery is read-first; perform only minimal repair when required.**
