# Tasks Reference

Defines task identity, lifecycle, active-task routing, status transitions, dependencies, completion, and task recovery.

---

## Purpose and Scope

**Covered here:** Task identity, statuses, file semantics, Task Index, `tasks/current.md`, creation, start/switch, block/unblock, progress update, complete, cancel, reopen, parent/subtask, conflict/consistency, retrieval.

**Owned elsewhere (ownership pointer — not automatic load):**
- Project switch / lifecycle → `references/project-lifecycle.md`
- Checkpoint schema → `references/checkpoints.md`
- ADR lifecycle → `references/decisions.md`
- Index mutation rules → `references/indexing.md`
- Recovery loading ladder → `references/recovery.md`
- Context classification → `references/consolidation.md`

---

## Task Model

> A Task is a persistent work unit with an explicit goal and current state.

Tasks are appropriate when work:
- Spans multiple sessions
- Has a clear completion criterion
- Needs to be resumed independently of session history

Tasks are **not** appropriate for: single commands, casual questions, trivial one-line edits, or temporary investigations with no durable output.

**Stable IDs** — `TASK-001`, `TASK-014`. IDs do not change due to rename, status change, file move, or completion.

**Task files are current-oriented state** — not append-only work logs. Update Completed / Remaining / Blockers / Next Step in place. Historical working snapshots belong in Checkpoint, Git, or session history.

---

## Status

Five valid statuses:

| Status | Meaning |
|---|---|
| **Planned** | Defined but not yet started |
| **In Progress** | Currently being executed |
| **Blocked** | Valid work; cannot progress due to a specific blocker |
| **Completed** | Goal achieved |
| **Cancelled** | Intentionally abandoned; not because it was completed |

No other statuses. If work is paused awaiting an external condition and still relevant — use **Blocked**.

Task status and user attention are separate. When user action is required but
independent work remains, keep `Status: In Progress` and record:

```text
Attention: User Action Required
Waiting On: User
Required Action: <specific action>
Resume Evidence: <fact or pointer that confirms completion>
```

Use `Blocked` only when the Task itself cannot progress. On recovery or a
status request, surface unresolved `User Action Required` before unrelated
next steps. Clear it only after the required evidence is confirmed; a generic
"continue" does not prove the action happened.

---

## Storage and Routing

```
tasks/
├── README.md       ← Task Index (Active / Planned / Completed sections)
├── current.md      ← Primary active task pointer only
├── TASK-014.md
└── completed/      ← Optional historical organization
```

`README.md` is the Task Index. `current.md` is a pointer — it contains the active task reference, not task content. `completed/` is optional; moving a file does not change its TASK ID.

---

## Active Task

`tasks/current.md` holds the single **primary active task pointer**:

```
Active Task: TASK-014
File: tasks/TASK-014.md
```

Rules:
- `current.md` may point to an **In Progress** or **Blocked** task.
- `current.md` **must not** point to a Completed or Cancelled task.
- A project may be Active with `Active Task: None` — this is valid.
- The Task Index may simultaneously show multiple In Progress / Blocked workstreams (parallel work), but `current.md` names one primary focus.

**Active Task Consistency Guard:** If `current.md` points to a Completed or Cancelled task, this is an inconsistency. Verify the intended active focus, repair `current.md` or the task status, update the Task Index, and continue. Do not resolve by mtime, highest TASK ID, last conversation, or filename ordering.

---

## Task Entry Model

Minimum required:

```
ID, Title, Status, Goal
```

Recommended for ongoing tasks:

```markdown
# TASK-014: Rule Engine

Status: In Progress
Priority: High

## Goal
Implement the rule execution engine.

## Completed
- Rule schema defined.

## Remaining
- Persistence layer.
- Retry behavior.

## Blockers
None.

## Relevant Files
- internal/rule/service.go

## Related Decisions
- ADR-007

## Next Step
Implement persistence write path and rerun unit tests.
```

**Next Step** must be specific and actionable.

| Bad | Good |
|---|---|
| Continue development. | Implement persistence write path and rerun unit tests. |

Optional fields: Priority, Dependencies, Parent Task, Result.

---

## Create Task

1. Resolve `project_id`. Do not create if scope is unresolved.
2. Read Task Index to check for duplicate goal or scope.
3. Assign the next stable TASK ID.
4. Create concise task file with Goal and Status.
5. Add entry to Task Index.
6. Update `current.md` only if this Task becomes the primary focus.

Do not create a Task for every user request — only for persistent meaningful work units.

---

## Start and Switch

1. Resolve target Task (via `current.md` for current, Task Index for others).
2. Persist meaningful state of current Task if it changed.
3. Validate target status:
   - **Planned** → set `Status: In Progress` when explicitly started
   - **Blocked** → may become primary focus while remaining Blocked; do not auto-set In Progress
   - **Completed / Cancelled** → must not become active without explicit Reopen or new Task
4. Update `current.md`.
5. Leave Task Index and project state pointers consistent.

**Same-task switch:** if the target equals the current active task, confirm scope and continue — do not re-mutate unnecessarily.

**Planned → In Progress** transition happens only when work actually begins, not when the task is read or referenced.

---

## Block and Unblock

When a task cannot proceed, record explicitly:

```
Status: Blocked
Blockers:
  - Waiting for vendor API credentials.
Next Step:
  - Resume integration after access is granted.
```

A Blocked task may still be the primary active task (`current.md` may point to it).

**Unblock:** transition to In Progress only when the blocker is confirmed resolved. Do not auto-unblock because the user says "continue."

If the blocker is owned by the user, keep `Waiting On`, `Required Action`, and
`Resume Evidence` current so another session can issue the same concise
reminder without relying on conversation history.

---

## Dependencies

Use stable references:

```
Depends-On:
  - TASK-010
  - ADR-007
```

Do not use only natural language ("the previous task", "that decision"). If a dependency blocks progress, set `Status: Blocked` with the dependency listed as the blocker.

---

## Update Progress

Update task fields in place to reflect current reality:

- `Completed` — what is currently accepted as done
- `Remaining` — what is left now
- `Blockers` — current blockers (clear when resolved)
- `Relevant Files` — current small working set
- `Next Step` — single, current, specific next action

Do not append session transcripts, debugging logs, or long command histories. Historical process belongs in Checkpoint, Git, or session history.

`Relevant Files` is a small working set to enable fast re-entry on resume — not a repository catalog.

---

## Complete Task

Before marking Completed, verify:
- Goal is genuinely satisfied
- Remaining is empty or intentionally out-of-scope
- Blockers resolved or irrelevant
- Required validation performed (if part of the goal)

**Completion flow:**
1. Set `Status: Completed`.
2. Record concise Result.
3. Clear or mark Remaining / Next Step.
4. Update Task Index.
5. Clear `current.md` or explicitly point it to the next active task.
6. Update project-level state if affected.
7. Move to `completed/` only if the project uses that structure.

`current.md` must not continue pointing to the newly Completed task.

---

## Cancel Task

When work is intentionally abandoned:

```
Status: Cancelled
Reason: Feature removed from MVP scope.
```

If `current.md` points to this task, clear it or set a new active task. Cancelled tasks are historical — do not auto-restore.

---

## Reopen or Create New Task

**Reopen** — only when the original Goal was genuinely not completed, or the Completed judgment was wrong:
```
Completed → In Progress
Reason: Integration test failures discovered post-merge.
```

**Create new Task** — when the original Goal was legitimately completed and new work has emerged:
```
TASK-030: Fix retry edge case in Rule Engine
Related-To: TASK-014
```

Do not endlessly reopen completed work to avoid creating new TASK IDs. New scope gets a new Task.

---

## Parent and Subtasks

A parent Task may list child TASK IDs; each child declares `Parent: TASK-XXX`.

Child completion does not automatically complete the parent. Parent completes only when the Parent Goal is satisfied (some children may legitimately be Cancelled).

Do not infer parent-child relationships from directory structure or filename patterns. If a project is small, hierarchy is optional.

---

## Retrieval

**Normal resume:**
```
tasks/current.md → current TASK file
```

If `current.md` pointer is valid, the full Task Index is usually not needed.

**Task overview or switch:**
```
Task Index (tasks/README.md) → specific TASK
```

Completed and Cancelled tasks are historical and loaded only when:
- User asks about prior work
- Regression or debugging requires it
- A new task explicitly depends on prior implementation

For the full project recovery ladder, follow `references/recovery.md`.

---

## Consistency

**Detect:**
- `current.md` points to Completed or Cancelled task
- `state.md` and `current.md` point to different tasks
- Task Index status disagrees with task file
- Task file missing for a referenced ID
- Parent/child pointer broken

**Resolve:**
```
validate tasks/current.md (canonical active-task pointer)
  ↓
if valid, use it and repair stale mirrors
  ↓
if missing or invalid, use exactly one explicit candidate or ask the user
  ↓
continue
```

Task file is the source of truth for Task content. `current.md` is the canonical active-task pointer. Task Index, project state, and Workspace Registry are routing mirrors. If `current.md` is missing or invalid and exactly one explicit In Progress or Blocked candidate can be established from valid project artifacts, repair the pointer to that Task. If multiple plausible candidates remain, stop before Task mutation and ask the user to identify the current Task. Do not resolve conflicts by recency, mtime, conversational context, or TASK ID magnitude.

**Mutation consistency:** When completing, starting, or cancelling a Task, the operation affects: TASK file + Task Index + `current.md` + project state (if exposed). If a key update fails, the operation is **Incomplete**. General atomicity rules are owned by `references/indexing.md`.

---

## Domain Invariants

- **Task IDs are stable; they do not change with rename, status, or file move.**
- **Task files describe current work state, not conversation history.**
- **`current.md` is a single primary-focus pointer, not task state itself.**
- **`current.md` must not point to Completed or Cancelled work.**
- **Blocked work may remain the primary active Task.**
- **Completing or cancelling the current Task requires updating `current.md`.**
- **Reopen only when the original goal was not truly complete; new scope gets a new Task.**
