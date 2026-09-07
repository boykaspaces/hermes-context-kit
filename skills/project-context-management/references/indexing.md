# Indexing and Navigation Reference

Defines hierarchical index-first retrieval, active-first navigation, index consistency, and controlled broad retrieval.

---

## Purpose and Scope

**Covered here:** index-first navigation, hierarchical index model, index entry semantics, active/current-first retrieval, stable pointers, direct-read exceptions, broad-scan policy, index consistency, broken/stale index handling, index creation threshold, retrieval budget.

**Owned elsewhere (ownership pointer — not automatic load):**
- Project lifecycle → `references/project-lifecycle.md`
- Recovery loading ladder → `references/recovery.md`
- Task lifecycle → `references/tasks.md`
- ADR lifecycle → `references/decisions.md`
- Checkpoint lifecycle → `references/checkpoints.md`
- Memory lifecycle → `references/memory.md`
- Context classification → `references/consolidation.md`

---

## Navigation Model

> Enter through the narrowest useful index before reading underlying artifacts.

```
index
  ↓ identify current / active entry
narrower index or direct pointer
  ↓
specific artifact
  ↓
historical artifact — only if needed
```

**Core principles:**
- **Index before content.** Read the routing layer first.
- **Current before history.** Active and In Progress state is the default.
- **Narrow before broad.** Follow the pointer; do not scan.
- **Stop when sufficient.** Load only what is needed to act correctly.

**Loading optimization:** A domain mutation does not require loading this reference merely because an index must be updated. Simple, well-defined index/pointer updates are performed directly by the owning domain protocol. Load `indexing.md` only when: new index structure is needed, index repair is required, routing is ambiguous, or a broken/stale pointer must be resolved.

---

## Hierarchical Index Model

Indexes form a navigation hierarchy. Descend one layer at a time.

```
<deployment-workspace-registry>                  ← global workspace registry
  ↓
<registered-project-path>/PROJECT.md             ← project manifest
  ↓
project/.hermes/context-index.md                 ← project navigation router
  ↓
domain index (tasks/README.md, docs/decisions/README.md, .hermes/memory/README.md)
  ↓
specific artifact (TASK-014, ADR-007)
  ↓
historical artifact — only when needed
```

Not every project requires all layers. Small projects may navigate directly from `PROJECT.md` without an intermediate `context-index.md`.

---

## When to Create an Index

Create an index only when it provides real navigation value.

**Create when:**
- Multiple artifacts of the same kind exist and routing matters
- Current / historical distinction is meaningful
- Stable IDs need a routing summary
- Repeated navigation would otherwise require scanning

**Skip when:**
- A single obvious artifact exists
- The project is tiny and navigation is unambiguous
- No ambiguity requires an index entry

> Do not create structure before it has navigation value. Do not create empty indexes to satisfy a template.

---

## Index Entry Model

A minimal entry needs only:

```
ID / File | Status | Title or one-line description | Read When
```

Optional: current pointer, supersession link, parent/child pointer.

**Index stores routing metadata — not artifact content.**

**Current state must be explicit.** Never derive it from file timestamps, filename ordering, creation time, or conversational recency. Status fields in the index and in the artifact must be the primary signal.

---

## Stable Pointers

Pointers should use stable references:

```
✅  TASK-014
✅  ADR-007
✅  project_id: stock-assistant
✅  explicit file path
```

Avoid:

```
❌  "the latest task"
❌  "that decision we made"
❌  "the previous file"
```

Stable pointers survive rename, file moves, and cross-session or cross-model handoffs.

---

## Current and Historical Retrieval

**Default — load Active/Current state:**

- Active, Current, In Progress, Blocked, Proposed (when proposal context matters)

**Historical — on demand only:**

- Completed, Cancelled, Superseded, Deprecated, Rejected, Archived, Historical

Load historical state only when:
- User explicitly asks for history
- Conflict or migration investigation requires it
- Regression or debugging needs it
- An active artifact explicitly references a historical one

Domain-specific status semantics are owned by the relevant reference.

---

## Narrowest Path and Direct Reads

**Narrowest path:** When a current pointer or index entry identifies the target, follow it directly — do not scan sibling files or the parent directory.

```
✅  tasks/current.md → TASK-014 → read TASK-014
❌  scan all tasks/ → open every file → find current task
```

**Direct read exceptions** — bypass index retrieval only when:
- User explicitly names the artifact
- Parent index already provided a direct pointer this session
- Active Task lists the file in its working set
- Current operation is modifying that exact artifact

Direct read does not justify scanning adjacent artifacts.

---

## Broad Scan Policy

Broad directory scanning is permitted only when:

- Index is missing and navigation is genuinely ambiguous
- Index is stale, broken, or unresolvable
- User explicitly requests exhaustive discovery
- Repository-wide verification is the actual task

**Standard fallback:**
```
attempt indexed path
  ↓
detect failure or genuine insufficiency
  ↓
broaden to smallest necessary scope
  ↓
repair or create index if appropriate
  ↓
return to indexed retrieval
```

Do not broaden because more information might be useful. Broaden only when the indexed path genuinely fails.

---

## Index Consistency

**Index is navigation; artifact is source of truth.**

When an artifact mutation changes status, path, active pointer, supersession, or routing, all affected index entries and pointers must be updated in the same logical operation.

Example — Task Completed:
```
TASK file (Completed)
  + Task Index updated
  + tasks/current.md cleared or updated
  + context-index updated if it exposes active task
```

If a key index or pointer update fails: **the mutation is Incomplete**. Do not report success. Repair the consistency gap before continuing.

If index and artifact conflict: verify the owning artifact's semantics. Repair the index. The artifact is the domain source of truth; the index is a navigation summary.

---

## Broken or Stale Index

**Detect:**
- Index points to a missing or renamed file
- Index status disagrees with the artifact
- Current pointer references a Completed, Superseded, or Archived artifact
- Supersession pointer is one-directional or broken
- Project path in registry is invalid

**Repair:**
```
identify canonical artifact or current intent
  ↓
repair the smallest affected index entry or pointer
  ↓
validate the corrected routing
  ↓
continue
```

Do not resolve ambiguity by choosing the newest file, highest ID, or most recent conversation turn. Domain semantics — Task status, ADR status, project_id — determine correctness.

---

## Retrieval Budget

Read routing metadata first. Load detailed artifact content only when the routing confirms it is needed. Load historical artifacts last.

Keep indexes short and current-oriented. If an index is growing to hold full artifact content, the content belongs back in the artifact; the index should retain only a pointer and a one-line summary.

Stop loading when sufficient context exists to act correctly on the current request.

---

## Domain Invariants

- **Indexes are routing structures, not sources of domain truth.**
- **Enter through the narrowest useful index or explicit pointer.**
- **Current and active routing is explicit — never derived from timestamps or file ordering.**
- **Broad scans are fallback or task-specific, not default retrieval.**
- **Navigation-changing mutations must leave all affected pointers and indexes consistent.**
- **A mutation whose index or pointer update failed is Incomplete.**
- **Create indexes only when they provide navigation value.**
