# Project State

Project: hermes-context-kit
Status: Active
Active Task: TASK-003

## Current summary

The repository maintains three reusable Hermes Skills and neutral project
templates. `multi-repo-system-management` v0.1.0 adds cross-repository
System/Component Task coordination without changing the frozen
`project-context-management` protocol. TASK-003 is adding the first
GitHub-hosted validation check required by the controlled-coding Ruleset.

## Primary focus

Complete [`TASK-003`](../tasks/TASK-003.md) by publishing the read-only CI
workflow and verifying its first GitHub-hosted run.

## Active constraints

- Protocol rules have one canonical owning file.
- Public artifacts contain no consuming deployment state or credentials.
- `project-context-management` remains unchanged.
