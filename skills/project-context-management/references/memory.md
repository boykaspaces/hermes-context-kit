# Project Memory Reference

Defines project-memory scope, eligibility, lifecycle, isolation, retrieval, promotion, supersession, and source-of-truth boundaries.

---

## Purpose and Scope

**Covered here:** what qualifies as Project Memory, global vs project scope, Facts/Lessons categories, eligibility, create/update/supersede/deprecate, retrieval, promotion boundaries, conflict handling, secret guard.

**Owned elsewhere:**
- Task lifecycle → `references/tasks.md`
- ADR lifecycle → `references/decisions.md`
- Checkpoint lifecycle → `references/checkpoints.md`
- Index mutation rules → `references/indexing.md`
- Context classification → `references/consolidation.md`
- Project lifecycle → `references/project-lifecycle.md`

---

## Memory Model

> Project Memory stores durable, verified, reusable project-specific knowledge that does not already belong to a stronger source of truth.

**Content Primary Home table:**

| Content | Primary Home |
|---|---|
| Implementation truth | Repository |
| Durable project choice | ADR |
| Current architecture | Docs / architecture |
| Current task state | Task file |
| Project-level current state | `state.md` |
| Resumable working snapshot | Checkpoint |
| Reusable project-specific knowledge | **Memory** |
| Repeatable procedure | Skill |
| Working / session history | Session |

Memory is supporting knowledge — it does not override any row above it in this table. Do not create a second source of truth by duplicating what already belongs to Task, ADR, architecture, or the repository.

**Example of what belongs in Memory:**
```
Vendor X's microtimestamp field is expressed in microseconds, not milliseconds.
Applies when normalizing Vendor X trade events.
Confirmed against API responses.
```

**Example of what does NOT belong in Memory:**
```
❌ Current task is implementing retry logic.     → Task
❌ Use DynamoDB as primary storage.              → ADR (if a formal decision)
❌ service.go currently has uncommitted changes. → Checkpoint
```

---

## Scope: Project vs Global

**Project Memory** — default for knowledge that is project-specific, durable, and reusable within one project:
- `stock-assistant` uses official disclosure feeds as the primary data source.
- Vendor X requires a custom retry workaround in this integration.

**Global Memory** — classification only in this protocol. When knowledge is demonstrably cross-project, stable, and not tied to project-specific assumptions, hand it to the built-in `memory` tool rather than storing it under the current project:
- User prefers Go for backend services.

Single-project recurrence does not equal cross-project applicability.

This reference owns Project Memory storage and lifecycle only. It does not define or write the global Memory store. Use `memory(action='add', target='user', content='<preference or user fact>')` for durable user information, or `memory(action='add', target='memory', content='<verified cross-project knowledge>')` for durable operating knowledge.

**Scope guard:** If `project_id` is unresolved or ambiguous, do not write Project Memory. Resolve project scope first. (Canonical rule: `SKILL.md` Scope Guard.)

---

## Categories

**Facts** — Confirmed, stable project-specific facts useful across future tasks.
> Vendor X timestamps are in microseconds.

**Lessons** — Reusable experience from implementation, failures, or repeated patterns.
> When a websocket reconnects after Cloudflare EOF, rebuild subscription state; do not rely on prior connection state.

If a Lesson forms a repeatable trigger + steps + clear outcome, keep it as project documentation or Project Memory until cross-project reuse is demonstrated. Then hand global Skill authoring to `skill-authoring`.

---

## Eligibility Test

Persist as Project Memory only if **all** are true:

1. **Project-specific?** Not a generic programming fact.
2. **Durable?** Likely to remain useful across future sessions and tasks.
3. **Verified?** Confirmed through implementation, testing, or official documentation.
4. **No stronger SOT?** Not already owned by code, ADR, architecture, or Task.
5. **Forgetting it causes repeated rediscovery or mistakes?**

If any answer is "no" — do not persist as Project Memory. Keep tentative hypotheses in Task or Checkpoint until confirmed.

---

## Memory Entry Model

**Status values:**

| Status | Meaning |
|---|---|
| **Active** | Currently valid; usable for present and future work |
| **Deprecated** | No longer recommended for new work; no complete replacement |
| **Superseded** | Explicitly replaced by a newer entry |
| **Historical** | Only relevant for understanding past behavior |

**Stable IDs** (`MEM-001`, `MEM-012`) — use when cross-referencing, superseding, or tracking. Small projects do not need IDs upfront.

**Recommended entry format:**
```markdown
## MEM-012 — Vendor timestamp unit

Status: Active

Verification: Confirmed
Verified-On: YYYY-MM-DD (when useful)

Fact:
Vendor X microtimestamp field is in microseconds.

Applies When:
Normalizing Vendor X events into millisecond timestamp model.

Evidence:
Confirmed against API responses and implementation.

See Also:
- TASK-021
```

Keep entries small: fact/lesson, scope, applicability, evidence if useful, related pointers. No conversation transcripts, logs, or large code blocks.

---

## Verification

- `Status` describes lifecycle (`Active`, `Deprecated`, `Superseded`, `Historical`). `Verification` is a separate field and must not be used as a lifecycle status.
- Long-term Memory must use `Verification: Confirmed`.
- Tentative hypotheses and suspected behaviors belong in Task or Checkpoint until confirmed.
- External facts (API limits, vendor behavior, service pricing, regulatory rules) may change. Re-verify rather than trusting Memory indefinitely.
- Verification date is audit metadata — it does not determine validity precedence.

---

## Storage and Index

Recommended structure (create only when retrieval value justifies it):

```
project/.context-kit/memory/
├── README.md       ← Memory Index
├── facts.md
└── lessons.md
```

Scale with need: `integrations.md`, `operations.md`, `domain.md` — but do not pre-create empty files.

**Memory Index** (`README.md`) — minimal:

| File | Status | Scope | Read When |
|---|---|---|---|
| `facts.md` | Active | Stable project facts | Project-specific fact needed |
| `lessons.md` | Active | Reusable lessons | Similar implementation issue |

Do not copy Memory content into the index.

When a mutation changes navigation (new category, index pointer, supersession affecting routing): leave affected Memory Index and context pointers consistent. Use `references/indexing.md` when detailed index mutation procedure is needed.

---

## Create or Update Memory

1. Resolve `project_id`. Do not write if scope is unresolved.
2. Run eligibility test. Stop if any criterion fails.
3. Verify no stronger source of truth already owns this.
4. Read Memory Index; find the narrowest relevant category.
5. Search for an existing canonical entry covering the same knowledge.
6. **Update existing entry** if it covers the same knowledge (clarification, better evidence, small correction).
7. **Create new entry** only if genuinely new knowledge.
8. Update Memory Index if navigation changed.

Do not load `references/indexing.md` automatically for every Memory write — only when index structure, repair, or complex navigation mutation is actually needed.

---

## Memory Lifecycle

**Update in place** — when the core fact has not changed and the update is a clarification, better evidence, or minor correction. No new entry needed.

**Supersede** — when a meaningful change replaces the old knowledge and historical record matters:
```
MEM-012: Status: Superseded → Superseded-By: MEM-031
MEM-031: Status: Active     → Supersedes: MEM-012
```
Do not create supersession chains for typo fixes.

**Deprecate** — when knowledge still explains legacy behavior but should not guide new work. Set `Status: Deprecated`. Does not enter current context by default.

**Historical** — load only when specifically investigating past behavior. Not part of normal bootstrap.

---

## Memory Retrieval

```
context-index
  ↓
memory/README.md
  ↓
relevant Active category
  ↓
specific entry
```

Load Memory only when the current task or question specifically requires it. Normal project resume does not dump all Memory.

Deprecated, Superseded, and Historical entries load only on demand — when the user asks, evolution is needed, or an active artifact explicitly references them.

Do not scan all memory files. Use the index to identify the narrowest relevant entry.

---

## Promotion

**Project Memory → Global Memory handoff** requires:
- Demonstrated cross-project applicability (not just multi-occurrence within one project)
- Stable meaning not tied to project-specific architecture or domain
- Unlikely to conflict with project-specific rules

The built-in `memory` tool owns the destination and write; do not write global Memory into the project store.

**Project-derived procedure → Global Skill** requires:
- Repeatable trigger condition
- Repeatable steps
- Clear expected result
- Demonstrated cross-project reuse value (not just a single fact or one-project recurrence)

After eligibility is proven, load `skill-authoring` and follow the canonical deployment scope. Do not package a single confirmed fact as a Skill. For detailed promotion classification, follow `references/consolidation.md`.

---

## Conflict and Staleness

If a Memory entry conflicts with the repository, an Active ADR, current docs, Task, or `state.md`:

```
verify the current/stronger source
  ↓
do not let stale Memory override it
  ↓
repair, update, deprecate, or supersede the Memory entry
```

**Memory is supporting knowledge, not an override layer.** A Memory entry recording PostgreSQL does not override an Active ADR that says DynamoDB.

---

## Secrets and Sensitive Data

**Never store in Memory:**
- Passwords, API secrets, private keys
- Access tokens, session tokens, credentials
- Any sensitive authentication material

**Allowed:**
- Credential location or mechanism: `Uses EC2 IAM Role`
- Secret identifier reference: `Key stored in AWS Secrets Manager under /prod/vendor-x`

Never the secret value itself.

---

## Size and Hygiene

Keep Memory entries focused. Avoid: conversation transcripts, large logs, full API responses, big code blocks, research dumps.

If an entry is growing to include background, examples, architecture, workflow, or API details — it may no longer belong in Memory. Migrate to `docs/`; Memory retains a pointer and a concise lesson.

Periodic hygiene: merge duplicates, deprecate/supersede stale facts, fix wrong scope, remove oversized or orphan entries. Do not use hygiene as a reason to broadly scan the project.

---

## Domain Invariants

- **Memory is curated durable knowledge, not compressed conversation.**
- **Do not duplicate stronger sources of truth into Memory.**
- **Project-specific knowledge stays project-scoped unless explicitly promoted.**
- **Memory stores knowledge; Skills store repeatable procedures.**
- **Lifecycle Status and Verification are separate; persistent Memory must be Confirmed.**
- **Stale Memory must not override current implementation, Active Decisions, or current project state.**
- **Never use Memory as a secret store.**
