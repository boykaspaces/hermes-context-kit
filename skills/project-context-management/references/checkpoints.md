# Checkpoints Reference

Defines checkpoint triggers, resumable working snapshots, latest/archive lifecycle, resume hints, Git/validation state, and checkpoint recovery.

---

## Purpose and Scope

A checkpoint is a resumable working snapshot at a point in time. Its goal is to allow another session, model, or agent to resume work without replaying the full conversation.

**Covered here:** when to checkpoint, checkpoint schema, latest/archive lifecycle, Resume Hint, Git/validation state, create/update/archive procedures, retrieval, stale/conflict handling.

**Owned elsewhere:**
- Task lifecycle → `references/tasks.md`
- Project switch / resume → `references/project-lifecycle.md`
- Index mutation rules → `references/indexing.md`
- ADR lifecycle → `references/decisions.md`
- Memory persistence → `references/memory.md`
- Recovery loading ladder → `references/recovery.md`

---

## Checkpoint Model

**A checkpoint is a resumable working snapshot — not conversation history.**

| Content | Primary Home |
|---|---|
| Current task state (Completed / Remaining / Blockers / Next Step) | Task file |
| Durable architectural decision | ADR |
| Project-level current summary | `state.md` |
| Reusable project knowledge | Memory |
| Implementation truth | Repository |
| Working / session history | Session |
| Resumable working snapshot | **Checkpoint** |

A checkpoint records current valid state only. Conversations contain rejected ideas, dead ends, and superseded decisions — do not compress them wholesale into a checkpoint.

---

## When to Checkpoint

Create a checkpoint only when meaningful resumable state exists that Task and Project State alone cannot efficiently reconstruct.

**Create when:**
- Switching project or major task with meaningful unfinished work
- Pausing long-running work
- Handoff to a new session, model, or agent is expected
- Context is at risk of being lost
- User explicitly requests a save/resume point
- Complex dirty or debugging state needs to be captured

**Skip when:**
- No meaningful state changed
- The current Task file already captures everything needed to resume
- A simple question was answered or a trivial edit was made
- A temporary investigation produced no durable result

> Checkpoint meaningful resumable state, not every transition.

---

## Storage and Lifecycle

```
project/.context-kit/checkpoints/
├── README.md       ← Checkpoint Index
├── latest.md       ← Current resumable snapshot (Status: Current)
└── archive/        ← Historical snapshots (Status: Archived)
```

**`latest.md`** is the current resume pointer. Currency is determined by explicit `Status: Current` — never by mtime or filename order. When no current checkpoint exists, the index must state `Current: None` explicitly.

**Archive:** When creating a new `latest.md`, archive the previous one if it represents a meaningful historical milestone. Skip archiving if it was duplicative, empty, or never valid. The goal is useful historical snapshots, not a mechanical record of every mutation.

**After task completion:** Archive or replace `latest.md` if it still describes completed work as in-progress. Do not leave a stale snapshot that implies an old task is still active.

**Checkpoint Index** (`.context-kit/checkpoints/README.md`) — keep minimal:

```markdown
# Checkpoint Index
Current: latest.md
Current Task: TASK-014
Status: Current
Archive: archive/
```

---

## Checkpoint Schema

Minimum required fields:

```
Project
Task
Status
Objective
Completed / In Progress / Remaining
Blockers
Relevant Files
Resume Hint
```

For code projects, also record:

```
Relevant Decisions   ← ADR IDs only, no full rationale
Git State            ← Branch, Commit, Dirty Files
Validation State     ← test/build summary only, not full CI log
Known Attempts       ← only if ongoing resume value exists
```

**Full example:**

```markdown
# Checkpoint

Project: stock-assistant
Task: TASK-014
Status: Current
Created: 2026-08-28

## Objective
Implement the rule execution engine.

## Completed
- Rule schema completed.
- Scheduler design completed.

## In Progress
- RuleExecution persistence.

## Remaining
- Retry behavior.
- Execution history.

## Blockers
None.

## Relevant Decisions
- ADR-007, ADR-012

## Relevant Files
- internal/rule/model.go
- internal/rule/service.go

## Git State
Branch: feature/rule-engine
Commit: a83fc82
Dirty Files:
  - internal/rule/service.go

## Validation State
- go test ./... not yet rerun after latest edit.

## Resume Hint
Rule schema and EventBridge scheduling are complete.
Resume from RuleExecution persistence in internal/rule/service.go,
then rerun go test ./... before continuing to retry handling.
```

**Field semantics:** `Completed` = currently accepted as done. Do not mark items Completed because they were discussed or attempted. `Created` is audit metadata — it does not determine which checkpoint is current.

---

## Resume Hint

Every Current checkpoint must include a `Resume Hint`. It must answer:
- Where did we stop?
- What is already settled?
- What is the next concrete action?

**Requirements:** 1–4 sentences, current and specific, actionable, model-agnostic (use stable references: Task IDs, ADR IDs, file paths).

| Quality | Example |
|---|---|
| ❌ Vague | "Continue where we left off." |
| ❌ Historical | "We discussed many things about the rule engine." |
| ✅ Actionable | "Persistence changes are partially done in service.go. Finish `persistRetry()`, then rerun tests before moving to retry behavior." |

A Resume Hint must reduce the next session's search cost — not narrate the past.

---

## Working-State Metadata

For code projects, record the Git and validation snapshot relevant to resume.

**Git State:** Branch, Commit, Dirty Files. Optionally: untracked or staged files.

**Validation State:** A brief summary — `go test ./... failing in package rule` — not a full CI log.

**Dirty/broken state must be recorded honestly.** Do not write `Clean` or `Ready` if tests are failing or changes are uncommitted. A false clean baseline causes errors in the next session.

**A checkpoint records Git state; it does not trigger Git operations.** Do not auto-run `git commit`, `git reset`, `git clean`, `git checkout`, or `git push` on checkpoint creation.

---

## Create / Update Procedure

1. Confirm meaningful resumable state exists that Task/State alone cannot cover. If not — skip.
2. Resolve current project and active task.
3. Extract current valid working state (not conversation history).
4. Capture Git/validation state if relevant.
5. Archive previous `latest.md` if it has historical value.
6. Write new `latest.md` with `Status: Current`.
7. Update `.context-kit/checkpoints/README.md`.
8. Update `context-index` pointer if it references the checkpoint.

Leave affected checkpoint pointers and indexes consistent. If an index update fails, the operation is Incomplete. Use `references/indexing.md` when detailed index mutation rules are needed.

---

## Retrieval and Resume

Checkpoints are not the first layer on project resume — Task and Project State come first. Load `latest.md` only when:

- Task and State files alone are insufficient to reconstruct working context
- User explicitly requests resuming from the last save point
- A handoff snapshot is relevant

**Default retrieval path:** Checkpoint Index → `latest.md`

Do not scan `archive/`, sort by timestamps, or load all checkpoints.

**Archive retrieval:** Only when the user asks about past state, a regression requires it, restoring a specific prior snapshot is needed, or `latest.md` is confirmed stale. For the full project recovery ladder, follow `references/recovery.md`.

---

## Stale and Conflicting Checkpoints

A checkpoint may be stale if it:
- References a Completed or Cancelled task as still active
- References a Superseded ADR as current
- Points to files that no longer exist
- Contradicts current Task or State files

**When stale:** verify against current domain sources, do not restore the stale snapshot as current, archive or replace `latest.md`, repair the Checkpoint Index.

**When `latest.md` and `tasks/current.md` disagree:** do not guess from mtime. Determine which pointer represents current project intent, repair the stale reference.

**Current domain sources override historical checkpoint content.** A checkpoint snapshot that records PostgreSQL does not override an Active ADR that says DynamoDB.

---

## Historical Checkpoints

Archive is on-demand only. Do not scan archive during normal project resume.

Load a specific historical checkpoint only when:
- User asks about a prior working state
- Regression investigation requires it
- `latest.md` is confirmed inconsistent and an archive provides the correct baseline

---

## Size Guidance

Keep checkpoints concise — hundreds of words for a typical task, a few pages at most for complex work. If a checkpoint is growing long, migrate durable content to:

- Task file (Completed / Remaining / Blockers / Next Step)
- ADR (decisions)
- Memory (reusable project knowledge)
- Repository / docs

Keep in the checkpoint: current working state + file pointers + Git/validation context + Resume Hint.

---

## Domain Invariants

- **A checkpoint is a resumable working snapshot, not conversation history.**
- **Create checkpoints only when they add recovery value beyond current Task/State.**
- **`latest.md` is the current resume pointer; archive is historical and on-demand.**
- **Task and Project State are current domain sources; checkpoints are snapshots.**
- **Durable decisions belong in ADRs — not only in checkpoints.**
- **Resume Hint must be short, actionable, and use stable references.**
