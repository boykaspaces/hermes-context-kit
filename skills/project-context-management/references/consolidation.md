# Context Consolidation Reference

Defines semantic context classification, persistence routing, promotion, deduplication, discard rules, and consolidation consistency.

---

## Purpose and Scope

**Covered here:** when consolidation is useful, candidate extraction, semantic classification, destination routing, strongest-source-first ordering, deduplication, promotion routing, discard, cross-project write scope, mutation ordering, consistency validation.

**Owned elsewhere (ownership pointer — not automatic load):**
- Task lifecycle → `references/tasks.md`
- ADR lifecycle → `references/decisions.md`
- Checkpoint schema → `references/checkpoints.md`
- Memory lifecycle → `references/memory.md`
- Index mutation rules → `references/indexing.md`
- Project lifecycle → `references/project-lifecycle.md`

---

## Consolidation Model

> Consolidation is semantic classification, not conversation summarization.

```
Working Context
  ↓ extract meaningful candidates
classify by semantics
  ↓ check canonical owner / existing SOT
update only necessary artifacts
  ↓
discard the rest
```

**Persistence is opt-in.** The vast majority of a session — temporary reasoning, raw tool output, failed hypotheses, repeated explanations, conversation wording — should not be persisted.

If consolidation finds no durable new information, no state change, and no resume-critical context: **No persistent changes required** is a valid and correct result.

---

## When to Consolidate

Consolidation is useful when:
- User explicitly requests it
- A major task milestone was reached
- Project or task switch with meaningful changed state
- Session/model handoff is expected
- Important context may be lost
- A durable decision emerged
- A reusable lesson or procedure emerged

Do not run a full consolidation automatically on every turn.

---

## Candidate Extraction

Do not process the conversation message-by-message. Extract candidates first:

- New durable decisions
- Task progress changes (completed / remaining / blockers / next step)
- Project-state changes
- Resume-critical working state
- New verified reusable facts
- New reusable lessons or procedures
- Documentation-worthy knowledge

Then classify the extracted candidates — not the raw conversation.

---

## Destination Router

Evaluate candidates in this order. Stop at the first match. Stronger sources of truth must be evaluated before Memory.

| Order | Candidate Meaning | Primary Destination |
|---|---|---|
| 1 | Implementation / config / schema / current technical truth | Repository / current docs |
| 2 | Durable project choice | ADR |
| 3 | Current work goal / progress / blocker / next step | Task |
| 4 | Project-level current summary | `state.md` |
| 5 | Resume-critical working snapshot Task/State cannot capture | Checkpoint |
| 6 | Durable reusable project-specific knowledge | Project Memory |
| 7 | Repeatable project-specific procedure | Project documentation or Project Memory; Skill creation is outside this protocol |
| 8 | Stable cross-project knowledge | Global Memory |
| 9 | Proven generic repeatable procedure | Global Skill |
| 10 | Long-form guide / runbook / domain architecture | Documentation |
| 11 | Temporary / non-durable / transient | **Discard** |

**One concept has one primary persistent home.** Other artifacts may hold pointers or concise summaries — not full content.

This is not a mandatory pipeline. A candidate may route directly: Conversation → ADR, Conversation → Docs, Conversation → Discard — based on semantics.

---

## Source-of-Truth Guard

Before writing to Memory, Checkpoint, or any supporting layer, check:

> Does a stronger canonical artifact already own this information?

Formal project choices belong in ADRs. Implementation truth belongs in the repository. Current work belongs in Tasks. Do not create a second source of truth for facts that are already owned.

Permitted duplication: pointer-only routing metadata (e.g., `state.md: Active Task: TASK-014`, `.context-kit/index.md → TASK-014`, `tasks/current.md → TASK-014`). Full Task content must not be copied into state, checkpoint, or memory.

---

## Candidate Validation

For each candidate:

1. Is it still current? (not superseded mid-session)
2. Is it verified enough to persist?
3. Is it durable? (not a one-off)
4. Is it already stored in an existing artifact?
5. Does another artifact own it (stronger SOT)?
6. Is it project-specific or global?
7. Will persisting it reduce future rediscovery or repeated mistakes?

If any critical answer is "no" — discard or keep only in the working session.

---

## Deduplication Before Write

```
read relevant index
  ↓
find existing canonical entry
  ↓
update existing if same concept
  ↓
create new only if genuinely new
```

Never blindly create a new ADR, Task, or Memory entry because the session contained something useful. Find the canonical entry first.

---

## Project Scope Guard

Never write project-scoped persistent context — Task, ADR, Checkpoint, Memory, Project State, or Index — while `project_id` is unresolved or ambiguous.

```
resolve project scope first → then classify and write
```

A session mentioning multiple projects does not authorize writing to all of them. Cross-project mutation must be an explicit, intentional operation. (Canonical rule: `SKILL.md` Scope Guard.)

---

## Domain Write Rules

When a candidate's destination is identified:

| Destination | Write rule |
|---|---|
| Task | Update current-oriented Task fields in place. Follow `references/tasks.md`. |
| ADR | Use ADR lifecycle; create/supersede through Decision Index. Follow `references/decisions.md`. |
| Checkpoint | Only if Task/State is insufficient for resume. Follow `references/checkpoints.md`. |
| Project Memory | Only if eligibility test passes. Follow `references/memory.md`. |
| Project-specific procedure | Keep as project documentation or Project Memory; reusable Skill destination follows the selected runtime adapter and `skill-authoring`. |
| Global Memory | Only when cross-project applicability is demonstrated; hand off to the built-in `memory` tool with the semantic target (`user` or `memory`). |
| Global Skill | Only when cross-project applicability and a repeatable trigger + steps + result are demonstrated; then load `skill-authoring`. |

Load the owning reference only when that domain's detailed procedure is actually needed.

---

## Promotion

**Project Memory → Global Memory** requires:
- Demonstrated cross-project applicability
- Stable meaning not tied to project-specific assumptions
- Single-project recurrence ≠ cross-project

**Project-derived procedure → Global Skill** requires:
- Repeatable trigger condition
- Repeatable steps with clear expected result
- Repeat use across multiple projects
- Generic procedure; no project-specific paths/names
- Stable inputs, outputs, and clear trigger

Until these conditions are met, retain the procedure as project documentation or an eligible Project Memory lesson; do not hand it off for Skill creation.

**Oversized Memory → Documentation** when the entry grows to include guides, runbooks, architecture explanations, or API documentation: migrate to `docs/`; Memory retains a pointer + concise lesson.

> Promotion follows demonstrated reuse, not optimism.

---

## User Intent

When the user says "remember this", "save this", "this is our decision", "save progress" — treat it as a strong persistence signal.

Route to the **semantically correct destination**, not mechanically to Memory:

- "We formally decided to use DynamoDB" → ADR (not Memory)
- "Remember this vendor quirk" → Project Memory (if eligible)
- "Save where we are" → Checkpoint or Task update

If the user explicitly specifies a destination (e.g., "put this in memory", "save as ADR"), follow it — unless it violates scope, source-of-truth design, or safety rules (e.g., "save this API key to memory" → refuse).

---

## Discard

The following are discarded by default:

- Temporary hypotheses that led nowhere
- Failed approaches with no lasting lesson
- Raw logs and tool outputs
- One-time calculations
- Repeated explanations and conversation filler
- Brainstorming not adopted
- Superseded working assumptions
- Resolved questions

Agent-generated suggestions, possible next steps, and architectural ideas that have not been adopted or become actual verified project state must not be persisted as project truth in `state.md`, Tasks, ADRs, or Memory.

Discarded content requires no action.

---

## Switch and Handoff

Before a project/task switch or session handoff:

1. Extract candidates for changed state.
2. Persist durable decisions (ADR if formal).
3. Update task progress in Task file.
4. Create checkpoint only if it adds resume value beyond Task/State.
5. Leave affected pointers and indexes consistent.

Then lifecycle/recovery handles the transition. Do not reproduce the Project Switch algorithm here.

---

## Mutation Procedure

1. Resolve `project_id`. Do not write if scope is unresolved.
2. Extract candidates from working context.
3. Classify each candidate against the Destination Router.
4. Load only the required owning domain reference for each write.
5. Update strongest sources of truth first (repository, ADR).
6. Update Task and Project State.
7. Update Project Memory only if eligibility criteria pass; hand eligible Global Memory or Global Skill candidates to their owning protocols.
8. Create Checkpoint only if needed.
9. Leave affected indexes and pointers consistent.
10. Validate: if a key write or pointer update failed — report **Incomplete**, not done.

Index mutation atomicity is owned by `references/indexing.md`.

---

## Correction and Incomplete State

Consolidation may repair directly-exposed issues:
- Stale memory entry discovered during the process
- Duplicate candidate found while deduplicating
- Outdated current pointer revealed during Task update

**Do not** use consolidation to perform full project cleanup, rewrite historical artifacts, scan all memories, or reformat everything. Scope remains narrow.

If a key mutation or index update fails: the consolidation is **Partial / Incomplete**. Repair the affected consistency before reporting success or continuing.

---

## Example: Mixed Session

| Candidate | Destination |
|---|---|
| Rule schema completed | Task: update Completed |
| "We'll use EventBridge" | ADR: create/supersede |
| Vendor retry IDs are idempotent for 24h | Project Memory (if verified) |
| Tried Redis, abandoned it | Discard |
| `service.go` has unfinished edits | Checkpoint — only if Task/State insufficient |

---

## Domain Invariants

- **Consolidation is semantic classification, not conversation summarization.**
- **Persistence is selective; no-change is a valid result.**
- **Stronger sources of truth are updated before supporting knowledge.**
- **One concept has one primary persistent home.**
- **Project-scoped writes require resolved `project_id`.**
- **Reusable Skill destination follows the canonical deployment scope; eligible global candidates are handed to `skill-authoring`.**
- **Promotion requires demonstrated reuse and correct scope.**
- **Consolidation is complete only when its directly affected artifacts and pointers are consistent.**
