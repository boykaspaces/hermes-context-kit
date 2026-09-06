# References Index

This directory contains the detailed protocol references for each project context operation domain.
Load only the reference matching your current operation — do not load all references.

| File | Domain | Status | Description |
|---|---|---|---|
| `indexing.md` | Index create / update / navigation | **Active** | Defines hierarchical index-first retrieval, active-first navigation, index consistency, and context-budget rules. |
| `project-lifecycle.md` | Project create / switch / resume / pause / archive | **Active** | Defines project identity, create/switch/resume/pause/archive lifecycle and progressive project recovery. |
| `decisions.md` | ADR / decision create / supersede / deprecate | **Active** | Defines ADR lifecycle, explicit decision state, supersession, active-decision indexing, and conflict handling. |
| `tasks.md` | Task create / update / switch / complete | **Active** | Defines task identity, lifecycle, active-task routing, status transitions, dependencies, completion, and task recovery. |
| `checkpoints.md` | Checkpoint create / resume | **Active** | Defines checkpoint triggers, resumable working snapshots, latest/archive lifecycle, resume hints, Git/validation state, and checkpoint recovery. |
| `memory.md` | Project memory persistence | **Active** | Defines project-memory scope, eligibility, lifecycle, isolation, retrieval, promotion, supersession, and source-of-truth boundaries. |
| `consolidation.md` | Context consolidation | **Active** | Defines semantic context classification, persistence routing, promotion, deduplication, discard rules, and consolidation consistency. |
| `recovery.md` | Project recovery / progressive loading | **Active** | Defines session-independent project recovery, progressive context reconstruction, loading order, stop conditions, validation, and historical fallback. |
