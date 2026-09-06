# TASK-003: Add Repository Validation CI

Status: In Progress
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

## Remaining

- Validate and publish the workflow.
- Confirm one successful GitHub-hosted run and record its check name.

## Blockers

None.

## Relevant Files

- `.github/workflows/validate.yml`
- `scripts/validate.sh`

## Next Step

Run local repository validation, commit the candidate, and publish it to
`main` so the first GitHub-hosted `repository-context` check runs.
