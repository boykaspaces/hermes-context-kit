# Skill Maintenance Reference

Defines runtime-neutral versioning, freeze semantics, patch approval, and
deprecation rules for agent Skills.

---

## Purpose and Scope

**Covered here:** versioning, freeze rule, change evaluation, patch approval gate, scope expansion guard, deprecation, skill deletion.

**Owned elsewhere:**
- Structural design → `references/architecture.md`
- Frontmatter and trigger validation → `references/validation.md`

---

## Versioning

```
Patch  (v0.x.y → v0.x.y+1): small behavioral fixes, guard additions, pitfall notes
Minor  (v0.x.0 → v0.x+1.0): new reference files, new operation domains, compatible additions
Major  (v0.x.0 → v1.0.0):   initial stable release, or breaking changes to canonical ownership
```

- New skills start at `v0.1.0`.
- Cosmetic wording edits alone do not require a version increment.
- Increment `metadata.context-kit.version` in this repository's SKILL.md when
  the change affects behavior. Other distributions follow their adapter's
  version field.

---

## Freeze Rule

A frozen Context Kit skill (`metadata.context-kit.version: ≥ 1.0.0`) is
considered stable. Other distributions follow their adapter's stability rule.

Do **not** modify a frozen skill for:
- Wording preferences or cosmetic cleanup
- Behavior already correctly covered by existing rules
- Hypothetical edge cases without observed operational impact

A frozen skill change is justified only when there is evidence of:
- Repeated behavioral misunderstanding by the model
- Missing rule for a common operation
- Conflicting rules producing ambiguous behavior
- Incorrect procedure causing execution failures

---

## Change Evaluation

When a potential issue is found in a frozen skill:

1. Read the exact current wording in the canonical owning file.
2. Determine whether the issue is an explanation error or a genuine rule gap.
3. Reproduce the issue with a concrete scenario when practical.
4. Classify: `EXPLANATION_ERROR` / `EXECUTION_ERROR` / `MISSING_RULE` / `AMBIGUOUS_RULE` / `CONFLICTING_RULE`.
5. Assign severity: LOW / MEDIUM / HIGH / CRITICAL.
6. Prefer no change when existing rules are sufficient.
7. If a change is required: smallest surgical patch to the canonical owning file.

---

## Approval Gate

Patching a frozen skill (`version ≥ 1.0.0`) requires explicit user approval.

Present one compact approval request:

```
Skill Maintenance Candidate

Skill:            <name>
Classification:   <MISSING_RULE | AMBIGUOUS_RULE | CONFLICTING_RULE>
Severity:         <LOW | MEDIUM | HIGH | CRITICAL>
Canonical Owner:  <file>
Observed Problem: <one short description>
Proposed Patch:   <one short description>
Files to Modify:  <exact list>

Recommendation: PATCH / DO NOT PATCH

Approve this patch?
```

Valid approval: "批准", "approve", "go ahead", explicit equivalent.

Approval applies only to the specific patch scope presented. It is not permanent authorization.

---

## Scope Expansion Guard

If during execution the approved patch requires additional files not listed in the approval:
- **Stop.**
- Issue a new approval request with the expanded scope.
- Previous approval does not authorize the expanded scope.

---

## Severity Policy

| Severity | Action |
|---|---|
| LOW | Do not patch. |
| MEDIUM | Patch only when reproducible and operationally important. |
| HIGH | Patch before relying on the affected operation. |
| CRITICAL | Fix before further use of the affected behavior. |

---

## Deprecation and Deletion

**Deprecate** when a skill is superseded but may still be referenced:
- Add `metadata.context-kit.status: Deprecated` for Context Kit publication,
  or the selected adapter's equivalent metadata.
- Add a note in SKILL.md pointing to the replacement.
- Do not delete until no active references remain.

**Delete** (`skill_manage action='delete'`) when:
- The skill is fully superseded and no longer needed.
- Pass `absorbed_into=<replacement-name>` when merging into another skill.
- Pass `absorbed_into=""` when pruning with no forwarding target.

---

## Domain Invariants

- **Frozen skills require explicit approval for any behavioral change.**
- **Approval is patch-specific — not a blanket authorization.**
- **Scope expansion always requires a new approval request.**
- **Explanation errors do not justify protocol modification.**
- **Version increments reflect behavioral changes, not cosmetic edits.**
