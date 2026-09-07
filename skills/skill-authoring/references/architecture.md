# Skill Architecture Reference

Defines skill qualification, complexity levels, file structure, and canonical ownership rules for personal Hermes Skills under the deployment-defined user-local Skill root.

---

## Purpose and Scope

**Covered here:** skill qualification, complexity tiers, file structure, SKILL.md as router, canonical ownership, reference creation threshold, source-of-truth hierarchy.

**Owned elsewhere:**
- Frontmatter rules and trigger validation → `references/validation.md`
- Versioning, patching, freeze policy → `references/maintenance.md`

---

## Qualification

Create a personal skill only when the workflow:
- Recurs across multiple sessions
- Involves non-obvious steps, pitfalls, or tool combinations
- Has been successfully executed at least once (proven path)
- Would otherwise require re-explaining or re-discovering the approach

Do **not** skill-ize:
- One-off tasks with no reuse value
- Simple single-tool invocations
- Tasks that are trivially discoverable from docs

---

## Complexity Tiers

| Tier | Characteristics | Structure |
|---|---|---|
| **Small** | Single domain, ≤ 5 steps, no branching | SKILL.md only |
| **Medium** | Multiple domains or significant procedure | SKILL.md + 1–2 references |
| **Large** | Router skill with distinct operation domains | SKILL.md (router) + domain references |

Choose the smallest tier that fits. Do not pre-create references for future complexity.

---

## File Structure

```
<canonical-skill-root>/
└── <skill-name>/
    ├── SKILL.md              ← entry point; router or self-contained
    └── references/
        ├── README.md         ← index of references (when ≥ 2 exist)
        ├── <domain-a>.md
        └── <domain-b>.md
```

Optional supporting directories (create only when needed):
- `templates/` — reusable file templates
- `scripts/` — helper scripts invoked via `terminal`
- `assets/` — static reference data

---

## Skill Destination Resolution

Resolve the approved Skill management mechanism and canonical user-local Skill
root from the deployment contract in `SOUL.md` before any persistent creation.
Do not hardcode or infer the root from a username, home directory, sandbox, or
repository checkout. All newly created global personal Skills must be direct
children of that deployment-defined root:

```
<canonical-skill-root>/<skill-name>/
```

Do not create, infer, or pass a category subdirectory during Skill creation. Existing nested Skills may remain where they are; do not move them as a side effect of this rule.

Before creation:

1. Identify the Skill name.
2. Resolve and state the expected canonical Skill root from `SOUL.md`.
3. If the user specifies that exact root, honor it.
4. If the user specifies a different path or a category, do not create the Skill and do not silently rewrite the destination. Report the conflict and obtain explicit direction.
5. If the user specifies no path, use the deployment-defined canonical destination and make it explicit before writing.
6. If the deployment contract does not define an approved mechanism and canonical root, stop and report Skill creation as Incomplete.

Create the Skill with `skill_manage(action='create', name='<skill-name>', content='<full SKILL.md>')` and omit the `category` argument. Do not use the generic sandboxed `write_file` tool for initial Skill creation.

After creation, verify:

| Field | Value |
|---|---|
| Expected Skill root | `<canonical-skill-root>/<skill-name>/` |
| Actual Skill root | `<canonical realpath returned or resolved by the host-side Skill runtime>` |
| Match | YES / NO |

Verify the created `skill_md` path from the `skill_manage` result, resolve its canonical realpath through the host-side Skill runtime, and confirm `skill_view('<skill-name>')` succeeds. The generic Docker `terminal` or `write_file` workspace is not evidence of host persistence.

If the actual Skill root does not match the expected canonical destination, or the host-side runtime cannot read it, treat Skill creation as **Incomplete**. Skill Index discoverability alone does not prove destination correctness.

---

## SKILL.md as Router

For Medium and Large skills, SKILL.md is the entry point and router — not the full procedure.

SKILL.md should contain:
- When to Load / When NOT to Load
- Operation Router table (operation → reference file)
- Core Guards (always-active constraints)
- Brief creation lifecycle summary (if applicable)

SKILL.md should **not** contain:
- Full domain procedures (those belong in references)
- Content that duplicates a reference file
- Historical changelogs or design rationale

---

## Reference Creation Threshold

Create a reference file only when:
- The content is too large for SKILL.md without obscuring the router
- Multiple operations share a distinct domain that benefits from isolation
- The content will be loaded selectively (not always needed)

Do **not** create references:
- Before the content exists
- To satisfy a template or assumed structure
- When SKILL.md would remain clear without them

> Do not create structure before it has navigation value.

---

## Canonical Ownership

Every normative rule belongs to exactly one file.

- Define the rule in the canonical owner.
- Cross-reference by pointer (`see references/validation.md § Trigger`), not by copying.
- When two files appear to define the same rule, the owning file wins; the other file must defer.

Ownership follows domain:
- Frontmatter and trigger rules → `validation.md` owns
- Structural and design decisions → `architecture.md` owns
- Versioning and patch semantics → `maintenance.md` owns

---

## Source-of-Truth Hierarchy

When skill files conflict:
1. `SKILL.md` frontmatter — authoritative for metadata
2. Canonical reference file — authoritative for domain rules
3. Session history — fallback only; not project state

---

## Lifecycle

1. **Qualify** — does this workflow merit a skill?
2. **Define triggers** — When to Load / When NOT to Load
3. **Identify domains** — what distinct operation types exist?
4. **Assign ownership** — one canonical file per domain
5. **Choose complexity** — Small / Medium / Large
6. **Design file structure** — only what is needed now
7. **Author SKILL.md** — router + guards + lifecycle summary
8. **Add references** — only when navigation value exists
9. **Validate** — see `references/validation.md`
10. **Slim and dedup** — remove anything that doesn't change behavior
11. **Consistency check** — no duplicate rules, no broken pointers
12. **Freeze** — see `references/maintenance.md`
13. **Exit authoring** — skill is live; do not keep authoring context active

---

## Domain Invariants

- **Skill qualification is required before design.**
- **SKILL.md is the router; references are the procedures.**
- **One canonical owner per rule — never duplicate normative content.**
- **Create references only when they provide navigation value.**
- **Complexity grows incrementally; do not pre-build structure.**
