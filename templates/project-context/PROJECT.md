# {{project_name}}

Project ID: {{project_id}}
Name: {{project_name}}
Status: Active

## Goal

{{project_goal}}

## Context entry points

| Artifact | Purpose | Read when |
|---|---|---|
| [`.context-kit/manifest.json`](./.context-kit/manifest.json) | Adopted protocol, release, profile, features, and adapters | Validating or upgrading project context |
| [`.context-kit/index.md`](./.context-kit/index.md) | Current-first context router | Starting or resuming project work |
| [`.context-kit/state.md`](./.context-kit/state.md) | Current project summary | Asking what is active now |
| [`tasks/current.md`](./tasks/current.md) | Primary active Task pointer | Continuing the current workstream |
| [`docs/decisions/README.md`](./docs/decisions/README.md) | Durable decision index | Work depends on a lasting decision |
