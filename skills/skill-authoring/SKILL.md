---
name: skill-authoring
description: "Use when creating, refactoring, or auditing Hermes Skills."
version: 1.1.0
author: Boyka Chen, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, meta, methodology, architecture]
    related_skills: [hermes-agent-skill-authoring]
---

# Skill Authoring

Meta-skill for designing, creating, refactoring, and auditing personal Hermes Skills under `~/.hermes/skills/`.
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
- In-repo hermes-agent skill contributions — use `hermes-agent-skill-authoring`
- General Hermes configuration — use `hermes-agent`

> This skill exits after the target skill is created or validated.

## Project Context Handoff

`project-context-management` owns project scope, project artifacts, and the classification of project-derived procedures. This skill owns reusable Skill content, structure, destination, creation, and validation.

Follow the canonical deployment scope in `SOUL.md`. When project work produces a proven cross-project reusable procedure, finish classification through `project-context-management`, then load this skill and create a global personal Skill under the canonical user-local Skill root.

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

**Description limit.** ≤ 60 characters. System prompt truncates at 57 + `...` — trigger must be self-contained in that window.

**Frontmatter first.** SKILL.md must start with `---` at byte 0. No leading blank lines.

**Minimal structure.** Do not create references, indexes, or sections before they have navigation value.

**Approval gate.** Patching a frozen skill requires explicit user approval. See `references/maintenance.md`.

## Creation Lifecycle (summary)

1. Qualify → 2. Trigger → 3. Non-trigger → 4. Domains → 5. Ownership →
6. Complexity → 7. File structure → 8. SKILL.md as router →
9. Add references only when useful → 10. Validate → 11. Slim/dedup →
12. Consistency check → 13. Freeze → 14. Exit authoring.

Full lifecycle: `references/architecture.md § Lifecycle`.
