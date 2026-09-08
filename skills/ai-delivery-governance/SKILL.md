---
name: ai-delivery-governance
description: "Use for explicitly adopted advisory delivery governance."
license: MIT
metadata:
  context-kit:
    version: 0.1.0
    author: Boyka Chen
    platforms: [linux, macos, windows]
    tags: [delivery, governance, review, validation]
    related_skills: [project-context-management, multi-repo-system-management]
---

# AI Delivery Governance

Experimental, runtime-neutral Skill for planning, reviewing, validating, and
presenting one bounded change proposal without redefining project or delivery
state owned elsewhere.

## When to Load

Load this Skill when both conditions are true:

1. the selected project's explicit adoption manifest enables the
   `delivery-governance` extension; and
2. the current Task declares `Governance: Required`.

Load it when resuming such a Task even if the conversation does not mention
governance. Use the Task-linked ledger and capability audit to recover the
current review stage and exact candidate boundary.

## When NOT to Load

Do not load this Skill for:

- ordinary Task creation, status, pointers, or completion without explicit
  governance adoption; use `project-context-management`;
- one-off work that does not justify a persistent Task;
- automatic command execution, merge, installation, or deployment;
- component, integration, lock, or deployment transitions owned by
  `multi-repo-system-management`.

## Operation Router

| Operation | Load |
|---|---|
| Plan, capability audit, contract freeze, review, validation, Final Audit, or recovery | [`references/delivery-cycle.md`](./references/delivery-cycle.md) |
| Start a Task capability audit | [`templates/capability-audit.md`](./templates/capability-audit.md) |
| Start a Task review ledger | [`templates/review-ledger.md`](./templates/review-ledger.md) |

## Core Guards

- `project-context-management` remains the owner of Task identity, status,
  state, pointers, and indexes. Governance stages are secondary progress only.
- The configured workflow adapter owns proposal acceptance. Candidate
  completion is not canonical acceptance.
- Load `multi-repo-system-management` whenever work crosses repositories or a
  component, integration, lock, Handoff, or deployment boundary.
- Run Capability Gate 0 before contract freeze when correctness depends on an
  uncertain external primitive. Unknown required capability evidence cannot
  produce `Pass`.
- Bind validation and Final Audit to the exact candidate revision. A later
  candidate mutation invalidates affected evidence.
- Evidence records cannot grant authority, atomicity, identity, enforcement,
  rollback, or recovery that the underlying platform does not provide.
- Keep every rollout increment in one bounded Task and proposal. Stop for user
  acceptance before starting the next increment.

## Procedure

1. Resolve the selected project and read its explicit adoption manifest.
2. Confirm the current Task opts in and load the canonical delivery cycle.
3. Create Task-linked evidence from the packaged templates only when required.
4. Execute the bounded cycle and record supported evidence boundaries.
5. Stop when the exact candidate is ready for workflow acceptance.

## Failure Handling

If project identity, adoption, authority, exact candidate identity, or required
evidence is unavailable, do not infer it from conversation or nearby files.
Follow the owning protocol's blocked or incomplete path and record the missing
fact in the current Task.
