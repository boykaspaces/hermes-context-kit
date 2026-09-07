# GitHub Workflow Adapter

This adapter maps a GitHub pull request to the core proposal/acceptance model.

- The repository's configured integration branch is the accepted ref.
- A pull-request head is a candidate next state, not current canonical state.
- Merging the pull request activates the Task, State, index, lock, and evidence
  changes contained in its accepted commit graph.
- A read-only post-merge check may verify reachability and the resulting head;
  it does not require another pull request when the candidate facts survived.

For multi-repository work, merge Component pull requests first. Then update the
existing System pull request with the exact accepted component revisions, lock,
verification evidence, and `Completed` System Task state. Merge that System
pull request last. Do not merge an intermediate System proposal and open a
second proposal merely to record the first one's merge.

If squash or rebase changes a component revision, refresh the still-open System
proposal before it is merged. If the final accepted outcome unexpectedly
differs from its candidate state, open a repair proposal for the factual
difference; this is exception recovery, not the normal completion flow.
