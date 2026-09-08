# Project State

Project: hermes-context-kit
Status: Active
Active Task: TASK-011

## Current summary

Context Kit 0.5.0 keeps project specification v2 and defines Hermes adapter v3
as a transactional runtime-package contract. Runtime and source-validation
inventories are separate, current complete installation is operator-only, and
SOUL remains optional and user-controlled. AI delivery governance has passed a
minimum documentation-only feasibility check and now has a sequential,
merge-gated experimental rollout covering source design, toolset installation,
existing-project adoption, multi-repository acceptance, and live runtime
verification. This repository now enables the advisory manual contract as an
experimental extension. TASK-011 is dogfooding its evidence and exact-candidate
review semantics; no core protocol or automation is enabled.

## Primary focus

Complete the bounded TASK-011 manual dogfood cycle, then stop at its pull
request for user review and acceptance.

## Active constraints

- Protocol rules have one canonical owning file.
- Public artifacts contain no consuming deployment state or credentials.
- Breaking protocol changes require an explicit specification version and
  migration path.
- Existing consumer assumptions are evidence for fixtures, not universal
  public requirements.
