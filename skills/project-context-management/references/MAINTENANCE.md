# Project Context Management — Maintenance Policy

Version: 1.3.1
Status: Frozen

---

## Purpose

This file governs maintenance of the `project-context-management` protocol itself.

It is not part of normal project-context execution and must not be loaded for ordinary Project, Task, ADR, Checkpoint, Memory, Consolidation, Recovery, or Index operations.

Load it only when explicitly auditing, modifying, versioning, or repairing the protocol — or when a Protocol Maintenance Candidate has been identified during runtime and requires read-only diagnosis before user approval.

> **Location:** `references/MAINTENANCE.md` (within the `project-context-management` skill)

---

## Freeze Rule

The v1 protocol is considered stable.

Do not modify the protocol for:
- wording preferences or cosmetic cleanup;
- isolated explanation mistakes when the underlying protocol is correct;
- behavior already explicitly or sufficiently covered by existing rules;
- hypothetical edge cases without observed operational impact;
- opportunities to make already-correct rules merely more detailed.

A protocol change is justified only when there is evidence of one or more of the following:
- repeated behavioral misunderstanding;
- incorrect project routing or scope resolution;
- persistent-state corruption or inconsistency;
- missing or conflicting canonical ownership;
- unsafe project-scoped mutation;
- mandatory recursive loading behavior;
- a common workflow that cannot be handled correctly by the existing protocol.

---

## Issue Escalation and Approval

### Step 1 — Escalation Decision

When execution encounters an unexpected behavior, inconsistency, or apparent protocol gap, first determine:

**Can the exact current protocol wording clearly resolve this?**

| Answer | Classification | Action |
|---|---|---|
| YES | Project State / Execution issue | Handle through owning domain reference. Not a Protocol Maintenance Candidate. |
| NO | Protocol Maintenance Candidate | Proceed to Step 2 — Automatic Diagnosis. |

Do not escalate to Protocol Maintenance for:
- stale Task pointers (tasks.md has the repair rule)
- broken index entries (indexing.md has the repair rule)
- stale checkpoint (checkpoints.md has the repair rule)
- incomplete mutation (owning reference defines the recovery)
- execution mistakes (retry through the existing protocol)

### Step 2 — Automatic Diagnosis (Read-Only)

Hermes may automatically perform this step without asking the user first.

1. Load `MAINTENANCE.md`.
2. Identify the suspected canonical owning file.
3. Read the exact current polished wording.
4. Reproduce or reconstruct the failing scenario when practical.
5. Compare expected behavior with actual protocol wording.
6. Classify the issue (see Issue Classification below).
7. Assign severity (see Severity Policy).
8. Determine whether a protocol patch is required.
9. Design the smallest surgical patch.
10. Identify targeted validation steps.

**No protocol file mutation occurs during diagnosis.**

### Step 3 — Issue Classification

Every diagnosed issue must be classified as one of:

| Classification | Meaning | Action |
|---|---|---|
| `EXPLANATION_ERROR` | Model described the protocol incorrectly; current wording is sufficient. | No patch. |
| `EXECUTION_ERROR` | Protocol is correct; execution failed to follow it. Repair project state if needed. | No patch by default. Repeated errors may later escalate. |
| `MISSING_RULE` | Required behavior has no sufficient canonical rule. | Patch candidate. |
| `AMBIGUOUS_RULE` | Existing wording permits materially different interpretations. | Patch candidate if operationally meaningful. |
| `CONFLICTING_RULE` | Two or more current rules require incompatible behavior. | Patch candidate. |

### Step 4 — User Approval Gate

If Diagnosis concludes **Patch Recommended: YES**, Hermes must stop before editing any protocol file and present one compact approval request in this format:

```
Protocol Maintenance Candidate

Classification: <MISSING_RULE | AMBIGUOUS_RULE | CONFLICTING_RULE>
Severity:       <LOW | MEDIUM | HIGH | CRITICAL>
Canonical Owner: <file>
Observed Problem: <one short description>
Current Rule Gap: <one short description>
Proposed Patch:  <one short description>
Files to Modify: <exact list>
Validation:      <targeted checks>

Recommendation: PATCH / DO NOT PATCH

Approve this protocol patch?
```

The user normally answers only: **Approve** or **Reject** (or natural-language equivalents).

**Valid approval:** "批准", "可以改", "执行", "approve", "go ahead", explicit equivalent.

**Invalid approval:** silence, topic change, ambiguous acknowledgement, general prior permission.

Approval applies only to the patch scope presented in the latest request. It is not permanent authorization for future protocol edits.

### Step 5 — Execute After Approval

Once the user approves, Hermes executes automatically without asking the user to restate the plan:

1. Re-verify the target wording has not materially changed.
2. Apply the smallest surgical patch.
3. Modify only the approved canonical owning files.
4. Do not silently expand scope.
5. Run targeted validation (see Targeted Validation below).
6. Report exact change and validation result.
7. Return to normal Frozen state.

If execution discovers that the approved patch requires additional files, architectural changes, or materially different semantics not included in the approval — **stop** and issue a new approval request. Previous approval does not authorize the expanded scope.

### Proactive Reporting Threshold

Hermes should proactively surface a Protocol Maintenance Candidate when it encounters:
- HIGH or CRITICAL issue
- Repeated MEDIUM issue
- Persistent-state corruption risk
- Wrong-project mutation risk
- Missing canonical owner
- Conflicting protocol instructions
- Common workflow that current protocol cannot safely resolve

Hermes should **not** interrupt the user for:
- LOW wording issues
- Cosmetic imprecision
- Isolated explanation errors
- Correctly resolvable project-state inconsistencies

---

## No Autonomous Protocol Editing

> Hermes may autonomously detect, investigate, classify, and propose protocol maintenance.
>
> Hermes must not autonomously modify the protocol.
>
> Every protocol modification requires explicit user approval for the specific patch scope.

This applies even to HIGH and CRITICAL issues.

For **CRITICAL** issues: stop the unsafe affected behavior, report the issue, prepare the patch, request approval — but do not modify protocol files before approval.

Protocol modifications include any edit to: `SOUL.md`, `SKILL.md`, `MAINTENANCE.md`, `references/*.md`, or any change to protocol semantics. Project-state repair is **not** a protocol modification and does not require approval.

---

## Change Evaluation

When a potential protocol issue is found:

1. Inspect the exact current wording in the canonical owning file.
2. Distinguish model explanation error from protocol behavior error.
3. Determine whether the existing protocol already covers the behavior explicitly or sufficiently.
4. Reproduce the issue with a focused Dry-Run or real execution when practical.
5. Classify the issue by severity.
6. Prefer no change when existing rules are sufficient.
7. If a change is required, modify only the canonical owning file with the smallest surgical patch.
8. Re-run only the affected consistency and behavior tests unless the change is structural.

---

## Severity Policy

### LOW

Examples:
- wording preference;
- cosmetic redundancy;
- one-off explanation imprecision;
- behavior already correctly covered.

Action: Do not patch.

### MEDIUM

Examples:
- ambiguous edge-case behavior;
- repeated model misunderstanding with limited operational impact.

Action: Patch only when the issue is reproducible or operationally important.

### HIGH

Examples:
- common workflow behaves incorrectly;
- canonical owner is missing;
- required routing is ambiguous;
- recursive mandatory loading is introduced.

Action: Apply a surgical patch before relying on the affected workflow.

### CRITICAL

Examples:
- wrong-project mutation;
- persistent state can be corrupted or lost;
- destructive behavior can occur;
- current project/task/decision state can become invalid without detection.

Action: Fix before further real-project use of the affected behavior.

---

## Surgical Patch Rule

A maintenance patch should:
- change the smallest possible number of files;
- modify the canonical owning file rather than duplicating rules elsewhere;
- avoid adding new sections when one sentence or guard is sufficient;
- avoid expanding SOUL.md or SKILL.md unless the issue belongs to their canonical scope;
- preserve progressive disclosure and narrow reference loading;
- avoid creating new references for isolated edge cases.

A patch that fixes behavior but substantially increases protocol complexity should be reconsidered.

---

## Targeted Validation

After a surgical patch, run only:
- affected wording verification
- affected domain consistency check
- affected Dry-Run scenario (if applicable)
- relevant cross-reference validation

Full protocol-wide audit is required only if the patch changes: architecture, canonical ownership, the router, global invariants, status models, or cross-domain execution semantics.

If part of an approved patch succeeds and another required mutation fails:
- report: **Protocol Patch: Incomplete**
- report: completed changes, failed changes, current consistency risk, recommended recovery
- do not make unrelated edits during recovery

---

## Evidence Rule

Protocol modification should be based on current protocol text and observed behavior.

Do not change the protocol solely because:
- a previous design document said something different;
- an earlier conversation described an older version;
- a model summarized a rule inaccurately;
- a hypothetical failure can be imagined but has not exposed a real semantic gap.

When uncertain, verify the current polished file first.

---

## Persistence Boundary

Model explanation errors do not automatically imply protocol errors.

An observed issue should be classified as one of:
- explanation error;
- execution error;
- missing rule;
- ambiguous rule;
- conflicting rule.

Only the latter four may justify protocol modification, and execution errors should first be checked against the exact existing rule.

---

## Versioning

- **Patch** (v1.0.x): small compatible behavioral fixes or surgical guards.
- **Minor** (v1.x.0): compatible protocol capability additions or new reference files.
- **Major** (vX.0.0): material architectural or canonical-ownership changes.

Cosmetic edits alone do not require a version increment.

The current protocol baseline is:

```
Version: 1.3.1
Status:  Frozen
```

The `SKILL.md` frontmatter version is the canonical runtime version. This header and baseline must match it before a protocol release is considered complete.

---

## Runtime Isolation

Normal project operations must not load this maintenance file.

The runtime path remains:

```
SOUL.md
  ↓
SKILL.md
  ↓
narrow owning reference
  ↓
project index / pointer
  ↓
specific project artifact
```

`MAINTENANCE.md` is loaded only when a Protocol Maintenance Candidate has been identified during execution, or when explicitly performing protocol audit or repair. It is outside the normal execution path and must not be included in the Operation Router.
