# TASK-003: Add Repository Validation CI

Status: Completed
Type: Component
Priority: High
Parent System Task: personal-hermes-agent:TASK-008

## Goal

Run the repository's canonical validation on pull requests to `main` and on
accepted branch pushes so GitHub Rulesets can require an immutable,
least-privilege status check.

## Completed

- Defined a read-only GitHub Actions workflow around `scripts/validate.sh`.
- Pinned the checkout action to an immutable upstream commit.
- Published the workflow to `main` and confirmed GitHub-hosted run
  `34034945784` completed successfully.
- Established `repository-context` as the check name for the `main` Ruleset.

## Remaining

None.

## Blockers

None.

## Relevant Files

- `.github/workflows/validate.yml`
- `scripts/validate.sh`

## Next Step

None. The parent System Task can configure `repository-context` as a required
status check when creating the `main` Ruleset.

## Result

Pull requests to `main` and pushes to `main` or `hermes/**` now run the
canonical repository validator with read-only token permissions and an
immutable checkout dependency.
