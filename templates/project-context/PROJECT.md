# {{project_name}}

Project ID: {{project_id}}
Name: {{project_name}}
Status: Active

## Goal

{{project_goal}}

## Context entry points

| Artifact | Purpose | Read when |
|---|---|---|
| [`.hermes/context-kit.json`](./.hermes/context-kit.json) | Adopted protocol, release, profile, and features | Validating or upgrading project context |
| [`.hermes/context-index.md`](./.hermes/context-index.md) | Current-first context router | Starting or resuming project work |
| [`.hermes/state.md`](./.hermes/state.md) | Current project summary | Asking what is active now |
| [`tasks/current.md`](./tasks/current.md) | Primary active Task pointer | Continuing the current workstream |
| [`docs/decisions/README.md`](./docs/decisions/README.md) | Durable decision index | Work depends on a lasting decision |
