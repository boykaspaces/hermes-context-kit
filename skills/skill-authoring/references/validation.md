# Skill Validation Reference

Defines portable frontmatter, trigger precision, and behavioral validation for
agent Skills. Runtime adapters may add compatible platform-specific fields.

---

## Purpose and Scope

**Covered here:** frontmatter field rules, description constraints, trigger precision, happy path, failure path, verification checklist.

**Owned elsewhere:**
- Structural design decisions → `references/architecture.md`
- Versioning and patch approval → `references/maintenance.md`

---

## Frontmatter Rules

SKILL.md must begin with `---` at byte 0 (no leading blank line, no BOM).

Required fields:

```yaml
---
name: skill-name              # lowercase, hyphens only, ≤ 64 chars
description: "One concise trigger sentence."
---
```

Version, author, platforms, UI metadata, related-Skill metadata, and other
frontmatter are distribution- or runtime-owned fields. Include only keys that
the selected adapter or publication policy supports. Context Kit keeps
`license` in the portable top level and its other release metadata under
`metadata.context-kit`; these are repository conventions, not universal
requirements.

---

## Description Rules

- One concise sentence that fits the selected runtime adapter's discovery UI.
- Ends with a period when the target format permits prose descriptions.
- Starts with the trigger signal: "Use when...", or capability-first phrasing.
- No marketing words: "powerful", "comprehensive", "seamless", "advanced".
- Does not repeat the skill name.
- If the description contains `:`, quote it when the target format uses YAML.

**Good:** `Use when creating, refactoring, or auditing agent Skills.`
**Bad:** `A comprehensive skill for all aspects of skill management and authoring workflows.` (too long, marketing)

---

## Trigger Precision

`## When to Load` must be precise enough that an unrelated task would not accidentally trigger the skill.

**Good triggers:**
- Specific operation types (create, patch, validate, freeze)
- Specific artifact types (SKILL.md, reference files)
- Explicit scope boundary (personal skills only, not in-repo)

**Bad triggers:**
- "When working with skills" — too broad
- "When the user mentions skills" — over-triggers on any skill usage

`## When NOT to Load` must list at least one meaningful counter-trigger — tasks that look adjacent but don't require this skill.

---

## Happy Path

The skill must define a clear, executable procedure for the primary use case:
- Numbered steps with checkable completion criteria
- Exact tool invocations (not vague instructions)
- Clear stop condition (when is the task done?)

For router skills, each operation must route to a reference that defines the procedure.

---

## Failure Path

The skill must address at least the most common failure mode:
- What breaks most often?
- How is it detected?
- What is the repair path?

Acceptable forms: `## Pitfalls` section, inline notes in procedure steps, or a dedicated `## Failure Handling` section.

---

## Verification Checklist

Before freezing a skill, confirm:

- [ ] SKILL.md starts with `---` at byte 0
- [ ] Core required fields and adapter-required fields are present and valid
- [ ] Description is concise, self-contained, and fits the adapter's limits
- [ ] `When to Load` is precise; `When NOT to Load` has at least one counter-trigger
- [ ] No normative rule duplicated across files (one canonical owner per rule)
- [ ] References created only where navigation value exists
- [ ] Each procedure step has a checkable completion criterion
- [ ] At least one failure mode addressed
- [ ] No unapproved machine-local paths or session-specific content in skill files. A user-required deployment canonical path is allowed only when marked deployment-specific and verified against the host-side canonical realpath
- [ ] Expected Skill root and supported creation mechanism were resolved from
      the selected runtime adapter; the actual runtime path matches
- [ ] `related_skills` entries all resolve to existing skills

---

## Domain Invariants

- **Description is the routing signal; adapter constraints determine its field limits.**
- **Trigger precision prevents over-loading and under-loading.**
- **One canonical owner per rule — validation rules live here, not duplicated in architecture.md.**
- **Verification checklist runs before freeze, not after.**
