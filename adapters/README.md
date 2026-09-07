# Adapter Index

Adapters bind the runtime-neutral Context Kit core to an execution runtime or
delivery workflow. They may add templates and validation but must not redefine
Task, State, evidence, profile, or component-lock semantics.

Runtime `adapter.json` files distinguish `project_templates`, which the CLI may
create inside a consumer project, from `operator_templates`, which require
deployment-owner integration and are never written by project initialization.

| Adapter | Kind | Purpose |
|---|---|---|
| [`runtime/hermes`](./runtime/hermes/README.md) | Runtime | Hermes workspace and Skill integration |
| [`runtime/codex`](./runtime/codex/README.md) | Runtime | Codex repository instructions and Skill integration |
| [`workflow/github`](./workflow/github/README.md) | Workflow | GitHub pull requests as candidate-state proposals |
