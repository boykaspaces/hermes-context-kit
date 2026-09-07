---
name: skill-authoring
description: "Use when creating, refactoring, or auditing agent Skills."
license: MIT
metadata:
  context-kit:
    version: 2.0.0
    author: Boyka Chen
    platforms: [linux, macos, windows]
    tags: [skills, authoring, meta, methodology, architecture]
    related_skills: []
---

# Skill Authoring

Meta-skill for designing, creating, refactoring, and auditing reusable agent
Skills. Runtime adapters own platform-specific packaging, destination, and
installation behavior.
This skill is **authoring-time only** — it is not a dependency of any target skill at runtime.

## When to Load

Load this skill when:
- Creating a new personal skill (`skill_manage create`)
- Adding or updating reference files within an existing skill
- Refactoring or splitting an existing skill
- Validating skill structure, frontmatter, or description
- Freezing, versioning, or patching a skill
- Authoring a global personal Skill from a project-derived procedure after project-context classification

## When NOT to Load

Do **not** load for:
- Ordinary use of any existing skill — use that skill directly
- Project context operations that do not create or modify a reusable Skill — use `project-context-management`
- Runtime configuration that does not create or modify a reusable Skill

> This skill exits after the target skill is created or validated.

## Project Context Handoff

`project-context-management` owns project scope, project artifacts, and the classification of project-derived procedures. This skill owns reusable Skill content, structure, destination, creation, and validation.

When project work produces a proven cross-project reusable procedure, finish
classification through `project-context-management`, then select the target
runtime adapter. The adapter owns the approved management mechanism, canonical
destination, and platform-specific metadata; this Skill owns the portable
content and validation criteria.

## Operation Router

| Operation | Load |
|---|---|
| Qualify + design a new skill; complexity, ownership, file structure | `references/architecture.md` |
| Validate frontmatter, description, trigger precision, happy/failure path | `references/validation.md` |
| Freeze, audit, patch, version an existing skill | `references/maintenance.md` |
| Navigate available references | `references/README.md` |

Load **only the reference required for the current operation**.

## Core Guards

**One canonical owner per rule.** Do not duplicate normative rules across reference files.

**Discoverable description.** Keep the trigger concise and self-contained.
Follow the selected runtime adapter's field and display limits.

**Frontmatter first.** SKILL.md must start with `---` at byte 0. No leading blank lines.

**Minimal structure.** Do not create references, indexes, or sections before they have navigation value.

**Approval gate.** Patching a frozen skill requires explicit user approval. See `references/maintenance.md`.

## Creation Lifecycle (summary)

1. Qualify → 2. Trigger → 3. Non-trigger → 4. Domains → 5. Ownership →
6. Complexity → 7. File structure → 8. SKILL.md as router →
9. Add references only when useful → 10. Validate → 11. Slim/dedup →
12. Consistency check → 13. Freeze → 14. Exit authoring.

Full lifecycle: `references/architecture.md § Lifecycle`.
