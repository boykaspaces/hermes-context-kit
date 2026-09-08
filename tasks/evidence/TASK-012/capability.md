# Capability Audit — TASK-012

Status: Passed
Applicability: Required
Gate Result: Pass

## Environment

- Repository: `boykaspaces/hermes-context-kit`
- Workflow adapter: GitHub v1
- Evidence date: 2026-09-09
- Observed pull request: PR #10
- Observed candidate: `cd09d4f59d1d2fc1d56f137043430f80d8ce6dae`
- Observed accepted merge: `4270b5b4a1d37c85a9f906fe1ae4ae2ab4e108a3`
- Observed Ruleset: `protect-main` (`22387255`)

## Required Guarantees

| ID | Guarantee | Required Primitive | Evidence | Failure Boundary | Result | Disposition |
|---|---|---|---|---|---|---|
| CAP-1 | A GitHub pull request exposes its exact candidate commit | Pull request `head.sha` | PR #10 API returned `cd09d4f59d1d2fc1d56f137043430f80d8ce6dae` | Mutable branch name without resolving head | Supported | Keep |
| CAP-2 | Check runs identify the exact commit they validated | Check Run `head_sha` | All three PR #10 check runs returned the same full candidate SHA | Reading only a check name or latest branch run | Supported | Keep |
| CAP-3 | A pull-request comment is immutable trusted Final Audit evidence | Immutable append-only review record | GitHub permits authorized users to edit, hide, or delete comments | Post-audit comment mutation or deletion | Unsupported | Reduce Contract |
| CAP-4 | For actors subject to `protect-main`, a new push dismisses stale approval before merge | Stale-review policy enforced without bypass | `protect-main` enables `dismiss_stale_reviews_on_push` and one required approval | Administrative bypass actor or different repository policy | Supported | Reduce Contract |
| CAP-5 | The observed Final Audit was independently approved through GitHub review | A distinct authorized reviewer and submitted approval review | PR #10 had no submitted reviews; its audit comment used the contributor identity | Same identity and administrator bypass | Unsupported | Reduce Contract |

## Evidence

- GitHub protected-branch behavior:
  `https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`
- GitHub check-run behavior:
  `https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-checks`
- GitHub comment mutation behavior:
  `https://docs.github.com/en/communities/moderating-comments-and-conversations/managing-disruptive-comments`
- PR #10:
  `https://github.com/boykaspaces/hermes-context-kit/pull/10`
- Final Audit comment from TASK-011:
  `https://github.com/boykaspaces/hermes-context-kit/pull/10#issuecomment-5588427739`

## Capability Miss

ID: CM-1
Origin: Late Discovery after TASK-011 Gate 0

TASK-011 treated a pull-request comment as sufficient durable external Final
Audit evidence without separately stating that the comment is mutable, no
formal GitHub review approval existed, and an administrator bypass could merge
without the configured approval gate. Exact-head binding was valid; evidence
immutability, reviewer independence, and enforcement were overstated.

Disposition: Correct the current experimental contract and GitHub adapter.
Do not rewrite TASK-011's accepted historical record.

## Contract Reduction

- A GitHub PR and check runs may prove which exact SHA was proposed and tested.
- A comment may record advisory audit content, but it is mutable and is not a
  tamper-proof attestation or independent approval.
- Review approval and stale-review enforcement are claimed only when the
  repository policy requires them and no authorized bypass is used.
- The experiment reports target identity, evidence kind, mutability,
  independence, and enforcement separately.

## Gate Result

PASS — exact-head identity and check binding are supported. Unsupported
immutability, independence, and universal enforcement claims were removed from
the Task contract before implementation. No retained required guarantee is
Unknown.
