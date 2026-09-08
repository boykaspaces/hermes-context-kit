# AI Delivery Governance Rollout

Status: Experimental planning record

## Purpose

Define the smallest safe path for evaluating AI delivery governance without
changing the stable Task lifecycle, project specification, reusable Skills,
schemas, CLI, runtime adapters, or workflow adapters in one large change.

The source design is an input to this plan, not a normative Context Kit
artifact. Each increment must be accepted independently before the next Task
starts.

## Existing Ownership Boundaries

- `project-context-management` continues to own Task identity, the five Task
  statuses, current pointers, progress, and completion.
- A workflow adapter continues to own proposal acceptance and the transition
  from candidate state to canonical state.
- `multi-repo-system-management` continues to own component source,
  integration acceptance, and deployment state across repositories.
- Runtime adapters and authoritative platform evidence own claims about
  available primitives. Governance metadata cannot manufacture authority,
  atomicity, identity, or observability.

No experimental delivery field may advance a Task, component, integration, or
deployment state owned by one of those contracts.

## Minimum Feasibility Gate

The feasibility check used a temporary project initialized from Context Kit
0.5.0 with the repository profile, Codex runtime adapter, and GitHub workflow
adapter. The temporary project added:

- `extensions.delivery-governance` in `.context-kit/manifest.json`;
- an active Task with `Delivery Stage`;
- `Acceptance Criteria`, `Out of Scope`, and `Required Validation` sections.

The unmodified `context_kit.py validate` command accepted that project.

| Required guarantee | Primitive or boundary | Evidence | Result |
|---|---|---|---|
| Advisory adoption metadata can be recorded without a specification change | Manifest `extensions` object | Clean temporary initialization and validation | Supported |
| Optional Task fields can coexist with the five-status Task model | Current Task parser validates the canonical `Status` field and tolerates additional Markdown fields | Temporary active-Task validation | Supported |
| Candidate completion can remain separate from acceptance | Project specification v2 and GitHub workflow adapter | Existing normative text and merged PR workflow | Supported |
| Cross-repository delivery truth remains separate | Multi-repository specification v2 | Existing source, acceptance, and deployment fields | Supported |

Gate result: **PASS for a documentation-only advisory experiment.**

This result does not authorize a core protocol, Skill, schema, CLI, runtime, or
CI change. Those changes require later Task evidence and their normal review
and maintenance boundaries.

## Corrected Experimental Semantics

The experiment must use these constraints from the start:

1. Capability Gate 0 has four outcomes: `Not Required`, `Pass`, `Blocked`, and
   `Incomplete`. An unresolved dependency or unknown required primitive cannot
   produce `Pass`.
2. `Ready for Acceptance` is a derived workflow condition, not a persisted
   Task delivery stage. A completed candidate becomes canonical through its
   configured workflow adapter without leaving a stale pre-acceptance stage in
   the accepted Task.
3. Validation and review evidence must identify the exact candidate revision.
   A later candidate change invalidates affected validation and final-audit
   evidence.
4. Risk acceptance requires an identified authority and evidence. A capability
   matrix cannot authorize its own risk exception.
5. Deferred findings remain review records. They do not automatically create
   Planned Tasks or expand current scope.
6. Required validation is descriptive during the manual experiment. Any later
   autonomous execution must use repository-controlled gate identifiers rather
   than treating arbitrary Task text as executable authority.

## Sequential Increments

Only one increment is active at a time. Every increment receives its own Task,
branch, validation, and pull request. The next Task starts only after the user
reviews and merges the preceding pull request.

### Increment 1 — Feasibility and rollout boundary

Owned by `TASK-008`.

- Record the minimum feasibility result.
- Freeze ownership and safety boundaries.
- Define the sequential rollout.
- Make no core protocol or automation change.

### Increment 2 — Advisory manual contract

Create the next Task only after Increment 1 is accepted.

- Add one concise, explicitly experimental delivery-governance reference.
- Enable advisory adoption for this repository through manifest extension
  metadata.
- Define Task contract, capability matrix, and review ledger conventions.
- Keep evidence linked from the Task rather than creating new global indexes.
- Do not modify reusable Skill semantics, JSON schemas, CLI behavior, runtime
  adapters, or CI.

### Increment 3 — First manual dogfood cycle

Create this Task only after Increment 2 is accepted.

- Apply the advisory contract to one bounded repository change.
- Exercise Initial Audit, finding disposition, focused fixes, Delta Review,
  deterministic validation, and Final Audit.
- Bind review and validation evidence to an exact candidate revision.
- Record ambiguity, review rounds, late discoveries, regressions, and deferred
  findings without automating policy.

### Increment 4 — Platform-dependent dogfood cycle

Create this Task only after Increment 3 is accepted.

- Use a change whose correctness depends on a real platform or workflow
  primitive.
- Exercise Capability Gate 0 with positive and negative evidence.
- Confirm that unsupported or unknown primitives lead to contract reduction,
  explicit risk acceptance, or a blocked Task rather than assumed support.
- Exercise Stabilization only if its trigger occurs naturally; do not invent a
  false successful stabilization record.

### Increment 5 — Phase 1 evidence decision

Create this Task only after Increment 4 is accepted.

- Compare the manual cycles against the stated Phase 1 readiness criteria.
- Decide whether more dogfood is needed.
- If the workflow is stable, propose the canonical owner and exact protocol
  patch through the applicable maintenance process.
- Do not assume the result must be a new Skill or a change to
  `project-context-management`.

### Conditional Phase 2 increments

Do not create these Tasks until Increment 5 concludes that Phase 1 evidence is
sufficient:

1. Freeze a machine-readable ledger schema.
2. Add one read-only governance check.
3. Add CI enforcement in a separate pull request.

Continuous autonomous execution remains later work and requires its own
capability, safety, and workflow-acceptance audit.

## Pull Request Gate

For every increment:

1. Start from the accepted integration branch.
2. Keep one Task and one bounded change package in the pull request.
3. Run the validation required by that Task.
4. Prepare the complete candidate Task and project-state transition in the
   same pull request.
5. Notify the user that review is ready.
6. Stop. Do not begin the next Task until the user merges the pull request.

