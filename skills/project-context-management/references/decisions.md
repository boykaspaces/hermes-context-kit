# Decisions / ADRs Reference

Defines ADR lifecycle, explicit decision state, supersession, active-decision indexing, and conflict handling.

---

## Purpose and Scope

**Covered here:** what qualifies as an ADR, stable ADR identity, statuses, decision area, Decision Index, create, supersede, deprecate, reject, conflict, retrieval.

**Owned elsewhere (ownership pointer — not automatic load):**
- Task lifecycle → `references/tasks.md`
- Index mutation rules → `references/indexing.md`
- Recovery loading ladder → `references/recovery.md`
- Context classification → `references/consolidation.md`
- Project lifecycle → `references/project-lifecycle.md`

---

## Decision Model

> An ADR records a durable project choice, why it was made, and the constraints it creates for future work.

**Appropriate for ADRs:**
- Architecture choices (storage, runtime, framework)
- Integration contracts and API strategy
- Deployment and infrastructure model
- Security model and authentication approach
- Major technical tradeoffs with long-term consequence
- Durable project policy

**Not appropriate:**
- Current task progress or next steps
- Temporary hypotheses or debugging notes
- Working snapshots
- Generic project facts without decision authority

**Stable IDs** — `ADR-001`, `ADR-007`. IDs do not change due to title change, status change, file move, or supersession.

---

## Status

Five valid statuses:

| Status | Meaning |
|---|---|
| **Proposed** | Candidate decision; not yet current truth |
| **Active** | Current valid decision; applies by default |
| **Superseded** | Explicitly replaced by a newer ADR |
| **Deprecated** | Should not guide new work; no complete replacement exists |
| **Rejected** | Considered and explicitly not adopted |

**Only Active ADRs are current decision truth by default.** Historical statuses load only on demand.

Proposed does not automatically become Active. Adoption must be explicit.

---

## Decision Area

A Decision Area names which durable choice an ADR governs (e.g., `Primary Database`, `Scheduler Mechanism`, `Auth Model`).

For exclusive Decision Areas — where only one choice applies at a time — **only one Active ADR should exist**. Two Active ADRs in the same exclusive area is an inconsistency that must be resolved before continuing (see Conflict and Consistency).

Do not resolve exclusive-area conflicts using mtime, ADR number magnitude, file order, or conversation recency.

---

## Storage and Routing

```
docs/decisions/
├── README.md        ← Decision Index
├── ADR-001-*.md
└── ADR-007-*.md
```

**Decision Index** (`README.md`) — Active and Proposed entries first, historical entries after:

```markdown
# Decision Index

## Active
| Area | ADR | Decision |
|---|---|---|
| Database | ADR-007 | Use DynamoDB |

## Proposed
| Area | ADR | Decision |
|---|---|---|
| Search | ADR-012 | Evaluate OpenSearch |

## Superseded / Deprecated / Rejected
| ADR | Status | Superseded-By |
|---|---|---|
| ADR-001 | Superseded | ADR-007 |
```

Index stores routing metadata — not full ADR rationale. Decision Index is the first entry point; read it before opening individual ADR files. Details of index mechanics are owned by `references/indexing.md`.

---

## ADR Entry Model

Minimum required fields:

```
ID, Title, Status, Decision, Rationale
```

Full recommended format:

```markdown
# ADR-007: Use DynamoDB for Primary Storage

Status: Active
Decision Area: Primary Database
Supersedes: ADR-001
Superseded-By: —

## Context
Event-oriented workload; operational simplicity preferred.

## Decision
Use DynamoDB as the primary persistence layer.

## Rationale
Lower operational overhead for the target workload pattern.

## Alternatives Considered
- PostgreSQL: higher operational overhead, richer queries
- Aurora Serverless: higher cost, less predictable latency

## Consequences
Lower operational overhead. Limited relational querying capability.
```

`Status` and `Decision Area` are required for routing. Dates (`Decided:`) are audit metadata — not precedence indicators.

---

## Create ADR

1. Resolve `project_id`. Do not create if scope is unresolved.
2. Read Decision Index; identify the Decision Area.
3. Check for existing Active or Proposed ADRs in the same area.
4. Determine whether this is a new decision, amendment, supersession, or duplicate.
5. Assign stable ADR ID.
6. Create ADR with explicit Status and Decision Area.
7. Update Decision Index.
8. Update affected architecture, state, or context pointers when the decision changes the current truth.

Do not create an ADR for every implementation detail, temporary preference, or passing observation — only for durable choices.

---

## Supersede ADR

When a decision replaces an existing Active ADR in the same area:

1. Identify current Active ADR for the Decision Area.
2. Create replacement ADR.
3. Set replacement: `Status: Active`, `Supersedes: ADR-old`.
4. Set old ADR: `Status: Superseded`, `Superseded-By: ADR-new`.
5. Update Decision Index.
6. Update affected architecture, state, and context pointers if the decision truth changed.
7. Validate that no contradictory Active decision remains in the area.

Supersession is **explicit** and **bidirectional** — both ADRs must carry the link. Reference stable IDs, not just titles.

**Multiple supersession:** A single new ADR may supersede multiple older ADRs. Each old ADR must record `Superseded-By: ADR-new`.

---

## Supersession Consistency

**A supersession must not leave both the old and replacement ADRs as Active for the same exclusive Decision Area.**

If supersession is interrupted mid-operation (new ADR written, old still Active, Decision Index partially updated) — the operation is **Incomplete**:

```
inspect both ADRs
  ↓
resolve intended current decision from ADR semantics
  ↓
repair statuses and bidirectional links
  ↓
repair Decision Index
  ↓
continue
```

Do not use timestamps or ADR number to determine which is the intended replacement.

**Partial supersession:** When a new ADR replaces only part of an existing one, the old ADR should not be marked fully Superseded unless its entire scope is replaced. Prefer: split the Decision Area, explicitly scope the replacement, or create a follow-up ADR clarifying the remaining active portion. Supersession scope must match the scope actually replaced.

---

## Deprecated, Rejected, and Reconsideration

| Status | Meaning |
|---|---|
| Superseded | Explicit replacement ADR exists |
| Deprecated | Should not guide new work; no complete replacement |

**Rejected ADRs** are preserved to answer "Did we consider X? Why not?" They do not enter current context by default and must not influence current implementation without explicit reconsideration.

**Reconsideration:** If a Rejected or Deprecated idea is revisited, create a new Proposed ADR or perform a controlled reactivation. Do not silently change `Rejected → Active` without recording the reasoning — that discards the historical rejection record.

---

## Decision Boundaries

| Content | Primary Home |
|---|---|
| Durable project choice and rationale | ADR |
| Current implemented behavior | Repository |
| Current architecture description | Architecture docs |
| Current work state (goal/remaining/next) | Task |
| Project-level current summary | `state.md` |
| Working / session history | Session |

**ADR expresses intended/decided truth. Repository expresses implemented truth.** When they conflict, surface the inconsistency — do not silently pick one over the other.

Tasks may reference ADR IDs for context. Tasks must not redefine or override durable decisions. If a task's implementation conflicts with an Active ADR, resolve which is authoritative before proceeding.

---

## Conflict and Consistency

**Detect:**
- Multiple Active ADRs in the same exclusive Decision Area
- Broken or one-directional supersession link
- Decision Index status disagrees with ADR file
- ADR file missing for a referenced ID
- Active ADR contradicts current architecture docs or repository

**Resolve:**
```
identify decision intent from ADR semantics
  +
identify implementation truth from repository
  ↓
repair narrow inconsistent decision metadata / index pointers
  ↓
surface intent-vs-implementation mismatch if still present
```

**Do not rewrite history.** If a durable choice genuinely changed — supersede or deprecate the old ADR, create a new one. Typo fixes, clarifications that do not change decision meaning, and metadata corrections may be applied in place.

Mutation consistency: supersession affects new ADR + old ADR + Decision Index + affected current pointers. If a key step fails, the decision mutation is **Incomplete**. General atomicity rules are owned by `references/indexing.md`.

---

## Retrieval

Normal path — to find the current decision for an area:

```
Decision Index → Active ADR for the area
```

To understand why a decision was made:

```
Decision Index → Active ADR → Rationale section
```

Load Superseded / Rejected / Deprecated ADRs only when:
- Historical rationale or evolution is explicitly needed
- Migration or regression analysis requires it
- A conflict investigation references historical decisions

For the full project recovery ladder, follow `references/recovery.md`.

---

## Domain Invariants

- **ADR IDs are stable; they do not change with title, status, or file move.**
- **Only Active ADRs are current decision truth by default.**
- **Exclusive Decision Areas must not have contradictory Active ADRs.**
- **Supersession is explicit and bidirectional; partial supersession must match its actual scope.**
- **An interrupted supersession leaving both ADRs Active is Incomplete and must be resolved.**
- **Durable decision changes preserve history — supersede rather than rewrite.**
- **ADR intent and repository implementation may differ; conflicts must be surfaced, not silently resolved.**
