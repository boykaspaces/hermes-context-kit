# Optional Context Kit Reinforcement for Hermes

This optional fragment reinforces Skill selection; it does not define Context
Kit behavior and is not required for runtime readiness. The installed Skills
remain the complete source of operating rules.

Persistent Context Kit projects use `/workspace`. Before a cross-project
operation, verify `/workspace/.hermes/WORKSPACE_ID` contains
`{{workspace_id}}`, then resolve projects through
`/workspace/.hermes/WORKSPACES.md`.

Load `project-context-management` before creating, switching, resuming, or
mutating persistent project context. Also load
`multi-repo-system-management` when coordinating System Tasks, component
locks, Handoffs, or acceptance across repositories. Load `skill-authoring`
only when creating or materially changing a reusable Skill.
