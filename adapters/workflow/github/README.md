# GitHub Workflow Adapter

This adapter maps a GitHub pull request to the core proposal/acceptance model.

- The repository's configured integration branch is the accepted ref.
- A pull-request head is a candidate next state, not current canonical state.
- Merging the pull request activates the Task, State, index, lock, and evidence
  changes contained in its accepted commit graph.
- A read-only post-merge check may verify reachability and the resulting head;
  it does not require another pull request when the candidate facts survived.

## Delivery-governance evidence

For the advisory delivery-governance experiment, resolve evidence strength as
separate facts:

- The pull request API's `head.sha` identifies the exact candidate commit at
  the time it is read. A branch name alone is not an immutable candidate.
- A check run's `head_sha` identifies the exact commit validated by that run.
  Matching only the check name or the latest branch run is insufficient.
- A pull-request comment may record an audit and name an exact SHA, but
  authorized users can edit, hide, or delete comments. Treat a comment as a
  mutable advisory record, not an immutable attestation or approval review.
- A submitted GitHub review records `COMMENTED`, `APPROVED`, or
  `CHANGES_REQUESTED`; repository Rulesets or branch protection determine
  whether approval is required and whether a new push dismisses it.
- Bypass actors remain part of the enforcement boundary. A configured approval
  rule does not prove that every accepted change passed that rule when an actor
  may bypass it.

A governance record therefore states the exact target SHA, evidence kind,
mutability, reviewer identity or independence claim, applicable enforcement
policy, and whether bypass was used or cannot be ruled out. Do not collapse
those facts into a generic claim that review evidence is `trusted`, `durable`,
or `immutable`.

For an exact-head Final Audit, create the final candidate first, let required
checks run against that head, then record or submit the audit without pushing
another commit. Any later push changes the candidate and invalidates the audit
for readiness. A workflow that cannot expose the candidate SHA or applicable
review enforcement leaves that part of readiness `Incomplete`.

For multi-repository work, merge Component pull requests first. Then update the
existing System pull request with the exact accepted component revisions, lock,
verification evidence, and `Completed` System Task state. Merge that System
pull request last. Do not merge an intermediate System proposal and open a
second proposal merely to record the first one's merge.

If squash or rebase changes a component revision, refresh the still-open System
proposal before it is merged. If the final accepted outcome unexpectedly
differs from its candidate state, open a repair proposal for the factual
difference; this is exception recovery, not the normal completion flow.
